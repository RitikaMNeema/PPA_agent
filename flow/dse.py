"""Design-space exploration of tuning knobs with Bayesian optimisation, executed
on a distributed backend (local pool / Spark / Docker).

    python flow/dse.py --executor spark --workers 8 --init 8 --rounds 3 --batch 4

Knob space: functionality-preserving core parameters + synthesis recipe
(2^7 = 128 configurations).  Each evaluation is a full flow run with a fixed
gate-level power window, so results are comparable to each other and to the
reference (baseline config, same window).

Loop:  random initial design  ->  [fit GP surrogates -> pick batch by Expected
Improvement -> run batch in parallel -> append to dataset] x rounds.
Runs already in the dataset (same knobs, same window) are reused, never re-run.

Outputs (runs/dse/):  dataset.jsonl  configs/<tag>.json  summary.json  report.md
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from env import DESIGN, ROOT, RUNS
from executor import FlowJob, get_executor, host_info
from objective import DEFAULT_WEIGHTS, METRICS, cost, metrics_of, pareto_front
from surrogate import PPASurrogate, propose_batch

DSE = RUNS / "dse"
# (name, kind, values) - all preserve ISA-level behaviour (verified by the firmware regression)
SPACE = [("TWO_STAGE_SHIFT", "param", [0, 1]),
         ("BARREL_SHIFTER", "param", [0, 1]),
         ("TWO_CYCLE_COMPARE", "param", [0, 1]),
         ("TWO_CYCLE_ALU", "param", [0, 1]),
         ("ENABLE_REGS_DUALPORT", "param", [0, 1]),
         ("ENABLE_FAST_MUL", "param", [0, 1]),
         ("abc_script", "synth", ["speed", "area"])]
NAMES = [s[0] for s in SPACE]


def base_cfg() -> dict:
    return json.loads((DESIGN / "config.json").read_text())


def encode(cfg: dict) -> list[int]:
    return [vals.index(cfg["params"][n] if kind == "param" else cfg["synth"].get(n, vals[0]))
            for n, kind, vals in SPACE]


def decode(x, base: dict) -> dict:
    c = json.loads(json.dumps(base))
    for (n, kind, vals), i in zip(SPACE, x):
        (c["params"] if kind == "param" else c["synth"])[n] = vals[i]
    return c


def tag_of(x) -> str:
    return "dse_" + "".join(map(str, x))


def all_points():
    return [list(x) for x in itertools.product(*[range(len(s[2])) for s in SPACE])]


def load_dataset(window: int) -> list[dict]:
    p = DSE / "dataset.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return [r for r in rows if r.get("pwr_cycles") == window]


def evaluate(xs, ex, window, round_no, source, base) -> list[dict]:
    (DSE / "configs").mkdir(parents=True, exist_ok=True)
    jobs = []
    for x in xs:
        t = tag_of(x)
        cp = DSE / "configs" / f"{t}.json"
        cp.write_text(json.dumps(decode(x, base), indent=2))
        jobs.append(FlowJob(t, str(cp.relative_to(ROOT)).replace("\\", "/"), window,
                            meta={"x": x, "round": round_no, "source": source}))
    print(f"[dse] round {round_no}: {len(jobs)} runs on {ex.name} ...", flush=True)
    t0 = time.time()
    res = ex.map(jobs)
    rows = []
    for r in res:
        x = r["meta"]["x"]
        rows.append({"tag": r["tag"], "x": x, "knobs": {n: vals[v] for (n, _, vals), v in zip(SPACE, x)},
                     "round": round_no, "source": source, "status": r.get("status"),
                     "metrics": metrics_of(r.get("ppa")), "ppa": r.get("ppa"), "seconds": r["seconds"],
                     "host": r["host"], "executor": ex.name, "pwr_cycles": window})
    with open(DSE / "dataset.jsonl", "a") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    print(f"[dse] round {round_no} done in {time.time() - t0:.0f} s "
          f"({sum(r['status'] == 'ok' for r in rows)}/{len(rows)} ok)", flush=True)
    return rows


def run(a):
    DSE.mkdir(parents=True, exist_ok=True)
    base, w = base_cfg(), DEFAULT_WEIGHTS
    ex = get_executor(a.executor, a.workers, master=a.master)
    rng = random.Random(a.seed)
    data = load_dataset(a.pwr_cycles)
    seen = {tuple(r["x"]) for r in data}
    x_ref = encode(base)
    t_start = time.time()

    # round 0: reference (baseline knobs) + random initial design
    init = [] if tuple(x_ref) in seen else [x_ref]
    pool = [x for x in all_points() if tuple(x) not in seen and x != x_ref]
    rng.shuffle(pool)
    need = max(0, a.init - len([r for r in data if r["source"] in ("init", "ref")]))
    init += pool[:need]
    if init:
        data += evaluate(init, ex, a.pwr_cycles, 0, "init", base)

    log = []
    for rnd in range(1, a.rounds + 1):
        ok = [r for r in data if r["metrics"]]
        ref = next(r["metrics"] for r in ok if r["x"] == x_ref)
        X = [r["x"] for r in ok]
        Y = {m: [r["metrics"][m] for r in ok] for m in METRICS}
        tried = {tuple(r["x"]) for r in data}
        cand = [x for x in all_points() if tuple(x) not in tried]
        if not cand:
            break
        sur = PPASurrogate(a.seed).fit(X, {m: np.array(v) for m, v in Y.items()})
        batch = propose_batch(X, Y, cand, ref, w, k=a.batch, seed=a.seed)
        log.append({"round": rnd, "n_train": len(X), "loo": sur.loo(),
                    "relevance": sur.relevance(NAMES), "batch": batch})
        print(f"[dse] surrogate LOO: {log[-1]['loo']}", flush=True)
        data += evaluate([b["x"] for b in batch], ex, a.pwr_cycles, rnd, "bo", base)
        for b in batch:                                       # record prediction vs actual
            got = next((r for r in data if r["x"] == b["x"] and r["metrics"]), None)
            b["actual_cost"] = round(cost(got["metrics"], ref, w), 4) if got else None

    if hasattr(ex, "stop"):
        ex.stop()
    summarize(data, x_ref, w, log, a, time.time() - t_start)


def summarize(data, x_ref, w, log, a, wall):
    ok = [r for r in data if r["metrics"]]
    ref = next(r["metrics"] for r in ok if r["x"] == x_ref)
    for r in ok:
        r["cost"] = round(cost(r["metrics"], ref, w), 4)
    ok.sort(key=lambda r: r["cost"])
    front = [ok[i]["tag"] for i in pareto_front([r["metrics"] for r in ok])]
    best = ok[0]
    final_sur = PPASurrogate(a.seed).fit([r["x"] for r in ok],
                                         {m: np.array([r["metrics"][m] for r in ok]) for m in METRICS})
    s = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "executor": a.executor,
         "workers": a.workers, "host": host_info(), "pwr_cycles": a.pwr_cycles, "weights": w,
         "space": [{"name": n, "values": v} for n, _, v in SPACE], "space_size": len(all_points()),
         "evaluated": len(data), "ok": len(ok), "wall_seconds": round(wall, 1),
         "cpu_seconds": round(sum(r["seconds"] for r in data), 1),
         "reference": {"tag": tag_of(x_ref), **ref},
         "best": {"tag": best["tag"], "knobs": best["knobs"], "cost": best["cost"], **best["metrics"]},
         "pareto": front, "loo_final": final_sur.loo(), "relevance_final": final_sur.relevance(NAMES),
         "rounds": log,
         "table": [{k: r[k] for k in ("tag", "round", "source", "knobs", "metrics", "cost", "seconds", "host")}
                   for r in ok]}
    (DSE / "summary.json").write_text(json.dumps(s, indent=2))
    write_report(s)
    print(f"[dse] best {best['tag']} cost {best['cost']} (ref 1.0) {best['knobs']}")
    print(f"[dse] report -> {DSE / 'report.md'}")
    try:
        import dashboard
        dashboard.build()
    except Exception as e:
        print(f"[dashboard] {e}")


def write_report(s):
    r, b = s["reference"], s["best"]
    pct = lambda k: f"{100 * (b[k] / r[k] - 1):+.1f}%"
    L = [f"# Design-space exploration ({s['generated']})", "",
         f"{s['evaluated']} of {s['space_size']} configurations evaluated on **{s['executor']}** "
         f"({s['workers']} workers): wall {s['wall_seconds']:.0f} s for {s['cpu_seconds']:.0f} s of flow time "
         f"(x{s['cpu_seconds'] / max(1, s['wall_seconds']):.1f} parallel speed-up). "
         f"Power window {s['pwr_cycles']:,} cycles. Weights {s['weights']}.", "",
         "## Best configuration", "",
         f"`{b['tag']}` cost **{b['cost']}** (reference = 1.0): runtime {pct('runtime')}, "
         f"power {pct('power')}, area {pct('area')}", "",
         "| knob | value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in b["knobs"].items()]
    L += ["", "## Surrogate model quality (leave-one-out)", "", "| metric | MAPE | R² |", "|---|---|---|"]
    L += [f"| {k} | {v['mape_pct']}% | {v['r2']} |" for k, v in s["loo_final"].items()]
    L += ["", "## Knob relevance (GP 1/length-scale, normalised)", "",
          "| knob | " + " | ".join(METRICS) + " |", "|---|" + "---|" * len(METRICS)]
    for n, _, _ in SPACE:
        L.append(f"| {n} | " + " | ".join(f"{s['relevance_final'][m][n]:.2f}" for m in METRICS) + " |")
    L += ["", "## Bayesian-optimisation rounds", "", "| round | train | picked | predicted cost | actual cost |",
          "|---|---|---|---|---|"]
    for rd in s["rounds"]:
        for bt in rd["batch"]:
            L.append(f"| {rd['round']} | {rd['n_train']} | {tag_of(bt['x'])} | {bt['pred_cost']:.4f} | {bt['actual_cost']} |")
    L += ["", f"## All evaluated (Pareto-optimal marked ★)", "",
          "| tag | src | runtime us | power mW | area um² | cost | host |", "|---|---|---|---|---|---|---|"]
    for t in s["table"]:
        m = t["metrics"]
        L.append(f"| {t['tag']}{' ★' if t['tag'] in s['pareto'] else ''} | {t['source']} | {m['runtime']:.0f} | "
                 f"{m['power']:.3f} | {m['area']:,.0f} | {t['cost']} | {t['host']} |")
    (DSE / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--executor", default="local", choices=["local", "spark", "docker"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--master", help="Spark master URL (default local[workers])")
    ap.add_argument("--init", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--pwr-cycles", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    run(ap.parse_args())
