"""Synthesis (Yosys + ABC -> sky130_fd_sc_hd) and timing.

Timing: ABC's liberty-based STA (`stime`) on the mapped combinational logic
between registers, plus flop clk->Q and setup from the liberty, plus SDC clock
uncertainty.  This is a pre-placement estimate (no wires/CTS); the OpenSTA /
OpenROAD path replaces it once the flow runs on Linux.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from env import LIB, run
from libcache import build_cache

# Cells we never want the mapper to pick (same idea as OpenROAD's DONT_USE_CELLS).
DONT_USE = ["*probe*", "*lpflow*", "*_ka*", "*sdf*", "*sedf*", "*dlclkp*", "*dlxbn*",
            "*dlxtn*", "*dlxtp*", "*dlrbn*", "*dlrbp*", "*dlrtn*", "*dlrtp*", "*einv*", "*ebuf*",
            "*clkdly*", "*_bleeder*", "*dlygate*", "*dlymetal*", "*macro_sparecell*", "*conb*"]


# ABC recipes (synthesis knob "abc_script").  {D} = target delay in ps.
ABC_SCRIPTS = {
    # delay-driven mapping + fanout buffering + gate sizing (like ORFS "speed")
    "speed": "strash; &get -n; &fraig -x; &put; scorr; dc2; dretime; strash; &get -n; &dch -f; "
             "&nf {D}; &put; buffer -p; upsize {D}; dnsize {D}; stime -p",
    # area-recovery mapping, light buffering, no upsizing
    "area": "strash; &get -n; &fraig -x; &put; scorr; dc2; strash; &get -n; &dch -f; "
            "&nf -R 1000; &put; buffer -p; stime -p",
}


def synth_script(rtl: list[Path], top_v: Path, top: str, period_ps: float, cfg_synth: dict,
                 out: Path) -> str:
    du = " ".join(f"-dont_use {p}" for p in DONT_USE)
    files = " ".join(p.as_posix() for p in [*rtl, top_v])
    lib = LIB.as_posix()
    flatten = "-flatten" if cfg_synth.get("flatten", True) else ""
    recipe = cfg_synth.get("abc_script", "speed")
    abc_file = out / "abc.script"
    abc_file.write_text("\n".join(c.strip() for c in ABC_SCRIPTS[recipe].split(";")) + "\n")
    d = f"-D {int(period_ps)}"
    return f"""
read_liberty -lib -ignore_miss_dir -setattr blackbox {lib}
read_verilog -DSYNTHESIS {files}
hierarchy -check -top {top}
synth -top {top} {flatten}
tee -q -o {out.as_posix()}/pre_map_stat.json stat -json
dfflibmap -liberty {lib} {du}
abc -liberty {lib} {d} -script {abc_file.as_posix()} {du}
setundef -zero
hilomap -singleton -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
splitnets
opt_clean -purge
tee -q -o {out.as_posix()}/stat.json stat -json -liberty {lib}
tee -q -o {out.as_posix()}/stat.txt stat -liberty {lib}
check -assert
rename -enumerate
write_verilog -noattr -noexpr -nohex -nodec {out.as_posix()}/netlist.v
write_json {out.as_posix()}/netlist.json
"""


def parse_abc_timing(log: str) -> dict:
    # ABC prints e.g.:  ... Area = 123456.78 ( 98.1 %)  Delay = 4321.00 ps ( ...)
    delays = [float(x) for x in re.findall(r"Delay\s*=\s*([\d.]+)\s*ps", log)]
    # critical path listing from `stime -p` (last occurrence)
    path = []
    blocks = log.split("Critical path:")
    if len(blocks) > 1:
        for line in blocks[-1].splitlines()[1:60]:
            m = re.match(r"\s*ABC:\s*(?:Path|Start|End|)\s*\d*\s*:?\s*(.*)", line)
            if not line.strip().startswith("ABC:"):
                break
            path.append(line.replace("ABC:", "").rstrip())
    return {"comb_delay_ps": delays[-1] if delays else None, "abc_path": path[:40]}


def run_synth(rtl: list[Path], top_v: Path, top: str, period_ns: float, uncertainty_ns: float,
              cfg_synth: dict, rundir: Path) -> dict:
    out = rundir / "synth"
    out.mkdir(parents=True, exist_ok=True)
    ys = out / "synth.ys"
    ys.write_text(synth_script(rtl, top_v, top, period_ns * 1000, cfg_synth, out))
    res = run(["yosys", "-q", "-l", out / "yosys.log", "-s", ys], cwd=out,
              log=rundir / "logs" / "synth.log", check=False)
    if res.returncode != 0:
        tail = "\n".join(res.stdout.splitlines()[-30:])
        return {"ok": False, "error": tail, "seconds": round(res.seconds, 1)}
    log = (out / "yosys.log").read_text(errors="replace")
    stat = json.loads((out / "stat.json").read_text())
    pre = json.loads((out / "pre_map_stat.json").read_text())
    top_stat = stat["design"]
    cells = top_stat.get("num_cells_by_type", {})
    lc = build_cache()["cells"]

    # --- area breakdown ---
    area = float(top_stat.get("area", 0))
    seq_cells = {c: n for c, n in cells.items() if c in lc and lc[c]["ff"]}
    n_ff = sum(seq_cells.values())
    seq_area = sum(lc[c]["area"] * n for c, n in seq_cells.items())
    families = Counter()
    for c, n in cells.items():
        fam = re.sub(r"^sky130_fd_sc_hd__", "", c).rsplit("_", 1)[0]
        families[fam] += n

    # --- timing ---
    t = parse_abc_timing(log)
    ff_types = list(seq_cells) or ["sky130_fd_sc_hd__dfxtp_1"]
    clkq = max(lc[c]["pins"][p]["clkq_ns"] or 0 for c in ff_types for p in lc[c]["pins"])
    setup = max(lc[c]["pins"][p]["setup_ns"] or 0 for c in ff_types for p in lc[c]["pins"])
    comb = (t["comb_delay_ps"] or 0) / 1000.0
    arrival = clkq + comb
    required = period_ns - setup - uncertainty_ns
    min_period = clkq + comb + setup + uncertainty_ns
    return {
        "ok": True, "seconds": round(res.seconds, 1),
        "area_um2": round(area, 1), "seq_area_um2": round(seq_area, 1),
        "comb_area_um2": round(area - seq_area, 1),
        "num_cells": int(top_stat.get("num_cells", 0)), "num_ff": n_ff,
        "cell_families_top": families.most_common(12),
        "pre_map_cells": pre["design"].get("num_cells_by_type", {}),
        "timing": {
            "clock_period_ns": period_ns, "clk_to_q_ns": round(clkq, 3), "setup_ns": round(setup, 3),
            "uncertainty_ns": uncertainty_ns, "comb_delay_ns": round(comb, 3),
            "arrival_ns": round(arrival, 3), "required_ns": round(required, 3),
            "wns_ns": round(required - arrival, 3), "min_period_ns": round(min_period, 3),
            "fmax_mhz": round(1000.0 / min_period, 1) if min_period else None,
            "abc_critical_path": t["abc_path"],
        },
    }
