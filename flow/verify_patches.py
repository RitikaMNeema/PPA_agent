"""Regression-check the rule-library patches: lint + full firmware RTL sim, each
patch alone and all RTL patches combined.  Results -> build/patch_verify.json

    python flow/verify_patches.py --tag iter000_baseline
"""
from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor

from advisor import PATCHES
from candidates import CAND_DIR, make_candidate
from design import load_config, write_top
from env import BUILD
from sim import rtl_sim


def check(tag: str, name: str, keys: list[str]) -> dict:
    sugs = [dict(PATCHES[k], title=k) for k in keys]
    m = make_candidate(tag, sugs, name=f"_verify_{name}")
    out = CAND_DIR / f"_verify_{name}"
    c = load_config(out / "config.json")
    top_v = write_top(c, out / "top.v")
    sim = rtl_sim(c.rtl, top_v, out)
    r = {"patches": keys, "lint_ok": m["lint"]["ok"], "lint_errors": m["lint"]["errors"],
         "sim_pass": sim.get("pass"), "cycles": sim.get("cycles"), "seconds": sim.get("seconds")}
    print(name, r, flush=True)
    return r


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="iter000_baseline")
    a = ap.parse_args()
    rtl = ["counters_hi_gate", "mul_operand_hold", "pc_imm_precompute"]
    jobs = {k: [k] for k in rtl} | {"all_rtl": rtl}
    with ThreadPoolExecutor(4) as ex:
        res = dict(zip(jobs, ex.map(lambda kv: check(a.tag, *kv), jobs.items())))
    BUILD.mkdir(exist_ok=True)
    (BUILD / "patch_verify.json").write_text(json.dumps(res, indent=2))
    for k in jobs:
        shutil.rmtree(CAND_DIR / f"_verify_{k}", ignore_errors=True)
    print(json.dumps(res, indent=1))
