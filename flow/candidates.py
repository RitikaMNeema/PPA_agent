"""Candidate RTL generation: apply suggestion patches to the RTL of a finished
run and produce a ready-to-run design candidate for the next iteration.

A patch (from the rule library or from Claude) is
    {"edits":  [{"file": "picorv32.v", "search": "<exact text>", "replace": "<new text>"}, ...],
     "params": [{"name": "TWO_CYCLE_ALU", "value": 1}, ...]}          # optional knob changes
Every `search` must match the base RTL exactly once (LLM edits that do not
apply cleanly are rejected, never fuzzily patched).

Output: design/picorv32/candidates/<name>/
    picorv32.v     new RTL            config.json   points at the new RTL + knobs
    patch.diff     unified diff       meta.json     provenance (base run, suggestions, lint)
then:  python flow/run_flow.py --tag <name> --config design/picorv32/candidates/<name>/config.json
"""
from __future__ import annotations

import difflib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from env import DESIGN, ROOT, RUNS

CAND_DIR = DESIGN / "candidates"
FORBIDDEN = {"ENABLE_DIV", "ENABLE_MUL", "COMPRESSED_ISA", "ENABLE_COUNTERS", "ENABLE_COUNTERS64",
             "ENABLE_IRQ", "ENABLE_IRQ_QREGS", "ENABLE_IRQ_TIMER", "CATCH_MISALIGN", "CATCH_ILLINSN",
             "ENABLE_PCPI", "ENABLE_TRACE", "REGS_INIT_ZERO"}


class PatchError(Exception):
    pass


def base_files(tag: str) -> tuple[dict, dict[str, str]]:
    """config + {filename: text} of the RTL actually used by run <tag>."""
    rd = RUNS / tag / "inputs"
    cfg = json.loads((rd / "config.json").read_text())
    texts = {Path(p).name: (rd / Path(p).name).read_text() for p in cfg["rtl"]}
    return cfg, texts


def apply_patch(texts: dict[str, str], patch: dict) -> dict[str, str]:
    out = dict(texts)
    for e in patch.get("edits", []):
        f = e.get("file") or next(iter(out))
        if f not in out:
            raise PatchError(f"unknown file {f}")
        n = out[f].count(e["search"])
        if n != 1:
            raise PatchError(f"search text matches {n} times in {f} (must be exactly 1): "
                             f"{e['search'].strip().splitlines()[0][:70]!r}")
        out[f] = out[f].replace(e["search"], e["replace"])
    for p in patch.get("params", []):
        if p["name"] in FORBIDDEN:
            raise PatchError(f"parameter {p['name']} is on the forbidden list (changes functionality)")
    return out


def diff(old: dict[str, str], new: dict[str, str], ctx: int = 3) -> str:
    d = []
    for f in old:
        if old[f] != new[f]:
            d += difflib.unified_diff(old[f].splitlines(keepends=True), new[f].splitlines(keepends=True),
                                      f"a/{f}", f"b/{f}", n=ctx)
    return "".join(d)


def preview(tag: str, sug: dict, _cache={}) -> dict:
    """Diff of one suggestion against the run's RTL (for the dashboard)."""
    patch = {"edits": sug.get("edits", []), "params": sug.get("params", [])}
    if not patch["edits"] and not patch["params"]:
        return {"ok": False, "reason": "no automatic patch"}
    key = (tag, json.dumps(patch, sort_keys=True))
    if key in _cache:
        return _cache[key]
    cfg, texts = base_files(tag)
    try:
        new = apply_patch(texts, patch)
        r = {"ok": True, "diff": diff(texts, new),
             "params": {p["name"]: f"{cfg['params'].get(p['name'])} -> {p['value']}" for p in patch["params"]}}
    except PatchError as e:
        r = {"ok": False, "reason": str(e)}
    _cache[key] = r
    return r


def make_candidate(tag: str, suggestions: list[dict], name: str | None = None, lint: bool = True) -> dict:
    cfg, texts = base_files(tag)
    new, applied = dict(texts), []
    params = dict(cfg["params"])
    for s in suggestions:
        new = apply_patch(new, s)                     # raises PatchError -> nothing written
        for p in s.get("params", []):
            params[p["name"]] = p["value"]
        applied.append(s.get("title", "?"))
    if new == texts and params == cfg["params"]:
        raise PatchError("selected suggestions contain no applicable change")

    n = len([d for d in CAND_DIR.glob("cand*")]) + 1 if CAND_DIR.exists() else 1
    name = name or f"cand{n:03d}_{re.sub(r'[^a-z0-9]+', '_', applied[0].lower())[:28].strip('_')}"
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        raise PatchError("bad candidate name")
    out = CAND_DIR / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for f, t in new.items():
        (out / f).write_text(t)
    rel = lambda p: str(p.relative_to(ROOT)).replace("\\", "/")
    ncfg = dict(cfg, params=params, rtl=[rel(out / Path(p).name) for p in cfg["rtl"]])
    (out / "config.json").write_text(json.dumps(ncfg, indent=2))
    d = diff(texts, new)
    pd = "".join(f"# param {k}: {cfg['params'].get(k)} -> {v}\n" for k, v in params.items() if cfg["params"].get(k) != v)
    (out / "patch.diff").write_text(pd + d)
    meta = {"name": name, "base_run": tag, "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "applied": applied, "param_changes": {k: v for k, v in params.items() if cfg["params"].get(k) != v},
            "diff_lines": d.count("\n"), "config": rel(out / "config.json"),
            "next_command": f"python flow/run_flow.py --tag {name} --config {rel(out / 'config.json')} --pwr-cycles 100000"}
    if lint:
        meta["lint"] = _lint(out, ncfg)
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    meta["diff"] = pd + d
    return meta


def _lint(out: Path, ncfg: dict) -> dict:
    from design import load_config, write_top
    from sim import lint
    c = load_config(out / "config.json")
    (out / "logs").mkdir(exist_ok=True)
    top_v = write_top(c, out / "top.v")
    return lint(c.rtl, top_v, c.top, out)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="build a candidate from advice suggestions")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--source", choices=["llm", "rules"], default="rules")
    ap.add_argument("--ids", required=True, help="comma list of category:index, e.g. power:1,timing:1")
    ap.add_argument("--name")
    a = ap.parse_args()
    adv = json.loads((RUNS / a.tag / "advice.json").read_text())[a.source]
    sel = [adv[c]["suggestions"][int(i)] for c, i in (x.split(":") for x in a.ids.split(","))]
    m = make_candidate(a.tag, sel, a.name)
    print(m["diff"])
    print(json.dumps({k: v for k, v in m.items() if k != "diff"}, indent=2))
