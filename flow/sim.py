"""Verification stages: lint (Verilator) and RTL simulation (Icarus) of the
self-checking firmware.  Produces structured results for the agent."""
from __future__ import annotations

import re
from pathlib import Path

from env import TB_DIR, run
from firmware import build_firmware


def lint(rtl: list[Path], top_v: Path, top: str, rundir: Path) -> dict:
    # PicoRV32 is old-style Verilog with many benign width warnings; we gate on
    # errors and report the warning count as a code-quality signal.
    res = run(["verilator_bin", "--lint-only", "-Wall", "-Wno-fatal", "--top-module", top,
               *rtl, top_v], cwd=rundir, log=rundir / "logs" / "lint.log", check=False)
    errors = len(re.findall(r"^%Error", res.stdout, re.M))
    warnings = len(re.findall(r"^%Warning", res.stdout, re.M))
    return {"ok": res.returncode == 0 and errors == 0, "errors": errors, "warnings": warnings,
            "seconds": round(res.seconds, 1)}


def parse_sim(out: str) -> dict:
    m = re.search(r"RESULT: (PASS|FAIL|WINDOW)\s*(\S*)", out)
    cyc = re.search(r"CYCLES=(\d+)", out)
    fetch = re.search(r"INSTR_FETCHES=(\d+)", out)
    return {"pass": bool(m and m.group(1) == "PASS"),
            "fail_reason": (m.group(2) if m and m.group(1) == "FAIL" else (None if m else "no_result")),
            "cycles": int(cyc.group(1)) if cyc else None,
            "instr_fetches": int(fetch.group(1)) if fetch else None}


def rtl_sim(rtl: list[Path], top_v: Path, rundir: Path, timeout: int = 1800) -> dict:
    hexf = build_firmware()
    vvp = rundir / "rtl_sim.vvp"
    run(["iverilog", "-g2005-sv", "-o", vvp, TB_DIR / "tb_core.v", *rtl, top_v],
        cwd=rundir, log=rundir / "logs" / "rtl_compile.log")
    res = run(["vvp", "-n", vvp, f"+firmware={hexf.as_posix()}"], cwd=rundir,
              log=rundir / "logs" / "rtl_sim.log", timeout=timeout, check=False)
    r = parse_sim(res.stdout)
    r["seconds"] = round(res.seconds, 1)
    return r
