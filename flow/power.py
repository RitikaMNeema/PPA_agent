"""Activity-based power estimation from gate-level simulation.

1. Generate Verilog models for the sky130 cells used in the netlist directly
   from the liberty `function` / `ff` statements, instrumented with toggle
   counters (sampled once per cycle -> zero-delay glitches are filtered out,
   like a SAIF from a functional simulation).
2. Run the gate-level netlist on the same firmware workload (this also checks
   the synthesized netlist is functionally correct).
3. Combine per-net toggle counts with liberty data:
     switching  = toggles * 1/2 * C_load * Vdd^2     (C_load = pin caps + wire load)
     internal   = toggles * E_internal(output pin)    (liberty internal_power)
     clock      = cycles * 2 * E_internal(CLK pin)  +  cycles * C_clk * Vdd^2
     leakage    = sum(cell_leakage_power)
   Power is reported at the SDC target clock frequency.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from env import TB_DIR, run
from firmware import build_firmware
from libcache import build_cache
from sim import parse_sim
from sta import Netlist, reg_group, wire_cap


def _vexpr(f: str) -> str:
    f = f.strip().strip('"')
    f = re.sub(r"(\w+)'", r"(!\1)", f)          # postfix negation A' -> !A
    f = f.replace("!", "~").replace("*", "&").replace("+", "|")
    f = re.sub(r"(\w|\))\s+(?=[\w(~])", r"\1 & ", f)  # implicit AND by whitespace
    return {"1": "1'b1", "0": "1'b0"}.get(f.strip(), f)


def gen_cell_models(cell_types: set[str], out: Path) -> Path:
    lc = build_cache()["cells"]
    lines = ["// AUTO-GENERATED from liberty by flow/power.py (functional + toggle counters)",
             "`timescale 1ns/1ps"]
    for ct in sorted(cell_types):
        c = lc[ct]
        pins = {n: p for n, p in c["pins"].items() if p["dir"] in ("input", "output")}
        outs = [n for n, p in pins.items() if p["dir"] == "output"]
        lines.append(f"module {ct} ({', '.join(pins)});")
        for n, p in pins.items():
            lines.append(f"  {p['dir']} {n};")
        if c["ff"]:
            ff = c["ff"]
            q, qn = ff["q"], ff["qn"]
            lines.append(f"  reg {q} = 1'b0; wire {qn} = ~{q};")
            clk = _vexpr(ff["clocked_on"])
            edge = f"posedge {clk}" if not clk.startswith("~") else f"negedge {clk[1:]}"
            sens = [edge]
            body = []
            if ff["clear"]:
                cl = _vexpr(ff["clear"])
                sens.append(f"negedge {cl[1:]}" if cl.startswith("~") else f"posedge {cl}")
                body.append(f"if ({cl}) {q} <= 1'b0; else")
            if ff["preset"]:
                pr = _vexpr(ff["preset"])
                sens.append(f"negedge {pr[1:]}" if pr.startswith("~") else f"posedge {pr}")
                body.append(f"if ({pr}) {q} <= 1'b1; else")
            body.append(f"{q} <= {_vexpr(ff['next_state'])};")
            lines.append(f"  always @({' or '.join(sens)}) {' '.join(body)}")
        for o in outs:
            f = pins[o]["func"]
            lines.append(f"  assign {o} = {_vexpr(f) if f else chr(49) + chr(39) + 'bx'};")
        # Event-driven toggle counters with a zero-delay glitch filter: a toggle is
        # counted only if the net's *settled* value differs between consecutive
        # active timesteps (intra-timestep delta glitches are ignored).
        for o in outs:
            lines.append(f"  integer t_{o} = 0; reg s_{o} = 1'b0, c_{o} = 1'b0; time l_{o} = 0;")
            lines.append(f"  always @({o}) begin if ($time != l_{o}) begin "
                         f"if (c_{o} !== s_{o} && tb_core.pwr_en) t_{o} = t_{o} + 1; "
                         f"s_{o} = c_{o}; l_{o} = $time; end c_{o} = {o}; end")
        cnts = " ".join(f"{o}=%0d" for o in outs)
        fin = " ".join(f"if (c_{o} !== s_{o}) t_{o} = t_{o} + 1;" for o in outs)
        lines.append(f"  always @(tb_core.dump_activity) begin {fin} $fdisplay(tb_core.act_fd, \"%m {cnts}\", "
                     f"{', '.join('t_' + o for o in outs)}); end")
        lines.append("endmodule\n")
    out.write_text("\n".join(lines))
    return out


def gate_sim(netlist_v: Path, cell_types: set[str], rundir: Path, pwr_cycles: int = 0,
             timeout: int = 7200) -> dict:
    hexf = build_firmware()
    pdir = rundir / "power"
    pdir.mkdir(parents=True, exist_ok=True)
    models = gen_cell_models(cell_types, pdir / "cells_sim.v")
    vvp = pdir / "gls.vvp"
    run(["iverilog", "-g2005-sv", "-DGLS", "-o", vvp, TB_DIR / "tb_core.v", netlist_v, models],
        cwd=pdir, log=rundir / "logs" / "gls_compile.log")
    res = run(["vvp", "-n", vvp, f"+firmware={hexf.as_posix()}", f"+pwr_cycles={pwr_cycles}"],
              cwd=pdir, log=rundir / "logs" / "gls_sim.log", timeout=timeout, check=False)
    r = parse_sim(res.stdout)
    r["window"] = "full_workload" if pwr_cycles == 0 else f"first_{pwr_cycles}_cycles"
    r["seconds"] = round(res.seconds, 1)
    r["activity_file"] = str(pdir / "activity.txt")
    return r


def estimate_power(netlist_json: Path, top: str, activity: Path, cycles: int,
                   period_ns: float, po_load: float = 0.0175) -> dict:
    nl = Netlist(netlist_json, top)
    lc = nl.lc
    vdd = 1.8
    t_s = cycles * period_ns * 1e-9
    # toggles per instance output pin
    tog = {}
    for line in Path(activity).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        inst = parts[0].split(".", 1)[1] if "." in parts[0] else parts[0]   # strip tb_core.
        inst = inst.split(".", 1)[1] if inst.startswith("dut.") else inst
        tog[inst] = {k: int(v) for k, v in (kv.split("=") for kv in parts[1:])}

    # map escaped Verilog instance names (iverilog prints them with the backslash removed)
    def lookup(inst):
        return tog.get(inst) or tog.get(inst.lstrip("\\")) or tog.get(inst.replace("\\", ""))

    E = defaultdict(float)                         # category -> pJ
    by_reg = defaultdict(lambda: {"pj": 0.0, "n_ff": 0, "toggles": 0})
    clk_cap = 0.0
    missing = 0
    total_out_toggles = 0
    for inst, c in nl.cells.items():
        cl = lc[c["type"]]
        is_ff = cl["ff"] is not None
        E["leakage_nw"] += cl["leak_nw"]
        t = lookup(inst)
        if t is None:
            missing += 1
            t = {}
        for pin, bits in c["connections"].items():
            p = cl["pins"][pin]
            if p["dir"] == "output":
                b = bits[0]
                n = t.get(pin, 0)
                total_out_toggles += n
                if isinstance(b, str):
                    continue
                cload = nl.load(b, po_load)
                e_int = n * p["e_pj"]
                e_sw = n * 0.5 * cload * vdd * vdd
                cat = "sequential" if is_ff else "combinational"
                E[cat + "_internal"] += e_int
                E[cat + "_switching"] += e_sw
                if is_ff:
                    g = reg_group(nl.name(b))
                    by_reg[g]["pj"] += e_int + e_sw
                    by_reg[g]["n_ff"] += 1
                    by_reg[g]["toggles"] += n
            elif p["clock"] or (is_ff and pin == "CLK"):
                e_clk = cycles * 2 * p["e_pj"]
                clk_cap += p["cap"]
                E["clock_internal"] += e_clk
                if is_ff:
                    q = next((bb[0] for pp, bb in c["connections"].items()
                              if cl["pins"][pp]["dir"] == "output" and not isinstance(bb[0], str)), None)
                    if q is not None:
                        by_reg[reg_group(nl.name(q))]["pj"] += e_clk
    n_clk_sinks = sum(1 for c in nl.cells.values() if lc[c["type"]]["ff"])
    clk_cap += wire_cap(n_clk_sinks)
    E["clock_net"] = cycles * clk_cap * vdd * vdd  # full charge+discharge each cycle

    mw = lambda pj: pj * 1e-12 / t_s * 1e3 if t_s else 0.0
    comp = {
        "clock_mw": mw(E["clock_internal"] + E["clock_net"]),
        "sequential_mw": mw(E["sequential_internal"] + E["sequential_switching"]),
        "combinational_mw": mw(E["combinational_internal"] + E["combinational_switching"]),
        "leakage_mw": E["leakage_nw"] * 1e-6,
        "leakage_uw": E["leakage_nw"] * 1e-3,
    }
    comp["internal_mw"] = mw(E["clock_internal"] + E["sequential_internal"] + E["combinational_internal"])
    comp["switching_mw"] = mw(E["clock_net"] + E["sequential_switching"] + E["combinational_switching"])
    total = comp["clock_mw"] + comp["sequential_mw"] + comp["combinational_mw"] + comp["leakage_mw"]
    regs = sorted(({"register": g, "power_mw": round(mw(v["pj"]), 4), "n_ff": v["n_ff"],
                    "toggle_rate": round(v["toggles"] / max(1, v["n_ff"] * cycles), 4)}
                   for g, v in by_reg.items()), key=lambda r: -r["power_mw"])
    return {
        "freq_mhz": round(1000 / period_ns, 1), "window_cycles": cycles,
        "total_mw": round(total, 4), **{k: round(v, 4) for k, v in comp.items()},
        "energy_per_cycle_pj": round(total * 1e-3 * period_ns * 1e-9 * 1e12, 2),
        "avg_net_toggle_rate": round(total_out_toggles / max(1, len(nl.cells) * cycles), 4),
        "clock_pin_cap_pf": round(clk_cap, 3), "n_ff": n_clk_sinks,
        "instances_without_activity": missing,
        "top_registers_by_power": regs[:15],
    }
