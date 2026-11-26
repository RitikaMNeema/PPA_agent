"""Closed-loop PPA agent:  observe -> diagnose -> propose -> verify -> evaluate -> accept/revert.

    python flow/agent.py --base iter000_baseline --steps 4 --parallel 4 --executor spark
    python flow/agent.py ... --proposer llm --max-usd 2.00      # Claude proposals (paid API)

Each step
  1. observe    bottleneck extraction on the current accepted run (power / timing / congestion)
  2. propose    ranked suggestions with patches, from the rule library or the LLM
  3. guard      exact-match patching, forbidden parameters, already-tried actions,
                lint of every candidate (rejections are logged with the reason)
  4. evaluate   surviving candidates run the full flow **in parallel** on the executor
                (local pool / Spark / Docker); the firmware regression must pass
  5. decide     greedy: accept the best candidate if it lowers the PPA cost by more
                than --min-gain, otherwise stop ("no improving action")

Stopping rules: step budget, no improving / no applicable action, LLM dollar budget.
Everything is written to runs/agent/<session>/trajectory.json (+ report.md) after
every step, so a long session can be monitored and audited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

from advisor import CATS, rule_based
from bottlenecks import RtlIndex, extract
from candidates import PatchError, make_candidate
from env import ROOT, RUNS
from executor import FlowJob, get_executor, host_info
from objective import DEFAULT_WEIGHTS, METRICS, cost, metrics_of

AGENT = RUNS / "agent"
# Claude Opus 5.5 list price (USD per million tokens) for the budget guard
PRICE_IN, PRICE_OUT, MAX_OUT = 4.0, 20.0, 32000
CONF = {"high": 0, "medium": 1, "low": 2}


def _rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def patch_key(s: dict) -> str:
    if s.get("patch_id"):
        return s["patch_id"]
    blob = json.dumps({"e": s.get("edits", []), "p": s.get("params", [])}, sort_keys=True)
    return "h" + hashlib.sha1(blob.encode()).hexdigest()[:10]


# ------------------------------------------------------------------ proposers
class RuleProposer:
    name = "rules"

    def propose(self, b: dict, run_dir: Path) -> list[dict]:
        adv = rule_based(b)
        return [dict(s, category=c) for c in CATS for s in adv[c]["suggestions"]]


class LLMProposer:
    """Claude proposals under a hard dollar budget; falls back to rules on any error."""
    name = "llm"

    def __init__(self, max_usd: float):
        self.max_usd, self.spent, self.calls, self.errors = max_usd, 0.0, 0, []

    def propose(self, b: dict, run_dir: Path) -> list[dict]:
        from advisor import _context, ask_claude
        core = run_dir / "inputs" / b["rtl_file"]
        rtl = RtlIndex(core)
        worst = (len(_context(b, rtl)) / 3.0 * PRICE_IN + MAX_OUT * PRICE_OUT) / 1e6
        if self.spent + worst > self.max_usd:
            self.errors.append(f"budget: spent ${self.spent:.2f}, next call up to ${worst:.2f} > ${self.max_usd}")
            return RuleProposer().propose(b, run_dir)
        try:
            adv = ask_claude(b, rtl)
            u = adv["_meta"]
            self.spent += (u["input_tokens"] * PRICE_IN + u["output_tokens"] * PRICE_OUT) / 1e6
            self.calls += 1
            return [dict(s, category=c, source="llm") for c in CATS for s in adv[c]["suggestions"]]
        except Exception as e:
            self.errors.append(f"{type(e).__name__}: {e}"[:300])
            return RuleProposer().propose(b, run_dir)


# ------------------------------------------------------------------ agent
class PPAAgent:
    def __init__(self, a):
        self.a = a
        self.sid = a.session or "agent_" + datetime.now().strftime("%m%d_%H%M%S")
        self.dir = AGENT / self.sid
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ex = get_executor(a.executor, a.parallel, master=a.master)
        self.prop = LLMProposer(a.max_usd) if a.proposer == "llm" else RuleProposer()
        self.w = DEFAULT_WEIGHTS
        self.tried: set[str] = set()
        self.T = {"session": self.sid, "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  "base_run": a.base, "proposer": self.prop.name, "executor": self.ex.name,
                  "parallel": a.parallel, "pwr_cycles": a.pwr_cycles, "weights": self.w,
                  "min_gain": a.min_gain, "host": host_info(), "steps": [], "status": "running"}

    def save(self):
        self.T["llm"] = ({"calls": self.prop.calls, "spent_usd": round(self.prop.spent, 4),
                          "budget_usd": self.prop.max_usd, "errors": self.prop.errors}
                         if isinstance(self.prop, LLMProposer) else None)
        (self.dir / "trajectory.json").write_text(json.dumps(self.T, indent=2))
        write_report(self.T, self.dir / "report.md")

    def _reference(self) -> dict:
        """Re-measure the base design with this session's power window (fair comparison)."""
        src = RUNS / self.a.base / "inputs"
        cfg = json.loads((src / "config.json").read_text())
        cfg["rtl"] = [_rel(src / Path(p).name) for p in cfg["rtl"]]
        cp = self.dir / "s0_config.json"
        cp.write_text(json.dumps(cfg, indent=2))
        tag = f"{self.sid}_s0"
        print(f"[agent] step 0: reference run of {self.a.base} ({self.a.pwr_cycles:,}-cycle window)", flush=True)
        r = self.ex.map([FlowJob(tag, _rel(cp), self.a.pwr_cycles)])[0]
        if r.get("status") != "ok":
            raise RuntimeError(f"reference run failed: {r.get('status')} (see runs/{tag}.out)")
        return r

    def run(self):
        t0 = time.time()
        ref = self._reference()
        self.ref = metrics_of(ref["ppa"])
        cur = {"tag": ref["tag"], "metrics": self.ref, "cost": 1.0, "ppa": ref["ppa"]}
        self.T["reference"] = {"tag": ref["tag"], **self.ref, "seconds": ref["seconds"]}
        self.T["accepted"] = [dict(cur, step=0, change="baseline")]
        self.save()

        for k in range(1, self.a.steps + 1):
            step = {"step": k, "from": cur["tag"], "from_cost": cur["cost"], "proposed": [],
                    "rejected": [], "evaluated": [], "decision": None}
            self.T["steps"].append(step)
            rd = RUNS / cur["tag"]
            b = extract(rd)                                              # 1. observe
            (rd / "bottlenecks.json").write_text(json.dumps(b, indent=2))
            step["top_bottlenecks"] = {c: (b[c]["items"][0]["id"] + " " + b[c]["items"][0].get("name", "")
                                           if b[c].get("items") else None) for c in CATS}
            sugs = self.prop.propose(b, rd)                              # 2. propose
            sugs.sort(key=lambda s: CONF.get(s.get("confidence"), 3))
            cands = []
            for i, s in enumerate(sugs):                                 # 3. guard
                key = patch_key(s)
                info = {"title": s["title"], "category": s["category"], "kind": s["kind"], "key": key,
                        "source": s.get("source", "rules")}
                step["proposed"].append(info)
                if not (s.get("edits") or s.get("params")):
                    step["rejected"].append(dict(info, reason="no machine-applicable patch")); continue
                if key in self.tried:
                    step["rejected"].append(dict(info, reason="already tried")); continue
                if len(cands) >= self.a.parallel:
                    step["rejected"].append(dict(info, reason="over parallel budget (deferred)")); continue
                try:
                    m = make_candidate(cur["tag"], [s], name=f"{self.sid}_s{k}_{len(cands)}")
                except PatchError as e:
                    self.tried.add(key)
                    step["rejected"].append(dict(info, reason=f"patch: {e}")); continue
                self.tried.add(key)
                if not m.get("lint", {}).get("ok"):
                    step["rejected"].append(dict(info, reason="lint failed")); continue
                cands.append((info, m))
            self.save()
            if not cands:
                step["decision"] = "stop: no applicable untried action"
                break

            print(f"[agent] step {k}: evaluating {len(cands)} candidates in parallel on {self.ex.name}", flush=True)
            res = self.ex.map([FlowJob(m["name"], m["config"], self.a.pwr_cycles,
                                       meta={"title": info["title"]}) for info, m in cands])   # 4. evaluate
            for (info, m), r in zip(cands, res):
                e = dict(info, tag=r["tag"], status=r.get("status"), rtl_pass=r.get("rtl_pass"),
                         seconds=r["seconds"], host=r["host"], diff_lines=m["diff_lines"],
                         param_changes=m["param_changes"])
                mm = metrics_of(r.get("ppa"))
                if r.get("status") == "ok" and r.get("rtl_pass") and mm:
                    e["metrics"] = mm
                    e["cost"] = round(cost(mm, self.ref, self.w), 4)
                    e["delta_pct"] = {q: round(100 * (mm[q] / cur["metrics"][q] - 1), 2) for q in METRICS}
                else:
                    e["verdict"] = "rejected: verification failed"
                step["evaluated"].append(e)

            ok = [e for e in step["evaluated"] if "cost" in e]           # 5. decide
            best = min(ok, key=lambda e: e["cost"]) if ok else None
            if best and best["cost"] < cur["cost"] * (1 - self.a.min_gain):
                step["decision"] = f"accept {best['tag']} ({best['title']}): cost {cur['cost']} -> {best['cost']}"
                cur = {"tag": best["tag"], "metrics": best["metrics"], "cost": best["cost"]}
                self.T["accepted"].append(dict(cur, step=k, change=best["title"]))
            elif any("deferred" in r["reason"] for r in step["rejected"]):
                step["decision"] = "no improvement; explore deferred actions from the same state" \
                                   + (f" (best {best['cost']})" if best else "")
            else:
                step["decision"] = "stop: no candidate improves cost by more than " \
                                   f"{100 * self.a.min_gain:.1f}%" + (f" (best {best['cost']})" if best else "")
            print(f"[agent] {step['decision']}", flush=True)
            self.save()
            if step["decision"].startswith("stop"):
                break

        self.T["status"] = "done"
        self.T["final"] = cur
        self.T["wall_seconds"] = round(time.time() - t0, 1)
        self.save()
        if hasattr(self.ex, "stop"):
            self.ex.stop()
        try:
            import dashboard
            dashboard.build()
        except Exception as e:
            print(f"[dashboard] {e}")
        print(f"[agent] done: cost 1.0 -> {cur['cost']}  ({self.dir / 'report.md'})")
        return self.T


def write_report(T: dict, out: Path):
    L = [f"# Agent session {T['session']}", "",
         f"base `{T['base_run']}` · proposer **{T['proposer']}** · executor **{T['executor']}** "
         f"(x{T['parallel']}) · window {T['pwr_cycles']:,} cycles · status **{T['status']}**", ""]
    if T.get("llm"):
        L += [f"LLM: {T['llm']['calls']} calls, ${T['llm']['spent_usd']} of ${T['llm']['budget_usd']} budget", ""]
    if T.get("accepted"):
        r = T["reference"]
        L += ["## Accepted trajectory", "", "| step | change | cost | runtime | power | area |", "|---|---|---|---|---|---|"]
        for a in T["accepted"]:
            m = a["metrics"]
            L.append(f"| {a['step']} | {a['change']} | {a['cost']} | {100 * (m['runtime'] / r['runtime'] - 1):+.1f}% | "
                     f"{100 * (m['power'] / r['power'] - 1):+.1f}% | {100 * (m['area'] / r['area'] - 1):+.1f}% |")
    for s in T["steps"]:
        L += ["", f"## Step {s['step']} (from `{s['from']}`, cost {s['from_cost']})", "",
              "Top bottlenecks: " + "; ".join(f"{c}: {v}" for c, v in (s.get("top_bottlenecks") or {}).items()), ""]
        if s["evaluated"]:
            L += ["| candidate | change | verdict | cost | Δruntime | Δpower | Δarea |", "|---|---|---|---|---|---|---|"]
            for e in s["evaluated"]:
                d = e.get("delta_pct", {})
                L.append(f"| {e['tag']} | {e['title']} | {e.get('verdict', 'pass')} | {e.get('cost', '-')} | "
                         + " | ".join(f"{d[q]:+.1f}%" if q in d else "-" for q in METRICS) + " |")
        if s["rejected"]:
            L += ["", "Rejected before running:"] + [f"- {r['title']}: {r['reason']}" for r in s["rejected"]]
        L += ["", f"**Decision:** {s['decision']}"]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="iter000_baseline", help="run tag to start from")
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--parallel", type=int, default=4, help="candidates evaluated in parallel per step")
    ap.add_argument("--executor", default="local", choices=["local", "spark", "docker"])
    ap.add_argument("--master")
    ap.add_argument("--pwr-cycles", type=int, default=20000)
    ap.add_argument("--min-gain", type=float, default=0.005, help="relative cost improvement to accept")
    ap.add_argument("--proposer", default="rules", choices=["rules", "llm"])
    ap.add_argument("--max-usd", type=float, default=0.0, help="hard LLM budget (required for --proposer llm)")
    ap.add_argument("--session")
    a = ap.parse_args()
    if a.proposer == "llm" and a.max_usd <= 0:
        ap.error("--proposer llm needs an explicit --max-usd budget (paid API)")
    PPAAgent(a).run()
