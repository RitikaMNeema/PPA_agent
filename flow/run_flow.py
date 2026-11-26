"""One flow iteration:  lint -> RTL sim -> synth -> STA -> gate-level sim + power.

Every iteration is a self-contained, reproducible directory runs/<tag>/:
  inputs/        snapshot of config.json, SDC and RTL actually used (+ sha256)
  logs/          raw tool logs
  synth/         netlist, stats
  power/         cell models, activity
  metrics.json   structured PPA + verification results (what the agent consumes)
  report.md      human/agent-readable summary

Usage:  python run_flow.py --tag iter000 [--config path] [--pwr-cycles N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

from design import load_config, write_top
from env import ROOT, RUNS, dashboard_enabled
from power import estimate_power, gate_sim
from sim import lint, rtl_sim
from sta import parse_sdc, run_sta
from synth import run_synth


def _sha(paths) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


def run_iteration(tag: str, config: Path | None = None, pwr_cycles: int = 0,
                  skip_power: bool = False) -> dict:
    cfg = load_config(config)
    rd = RUNS / tag
    if rd.exists():
        shutil.rmtree(rd)
    (rd / "inputs").mkdir(parents=True)
    (rd / "inputs" / "config.json").write_text(json.dumps(cfg.to_json(), indent=2))
    shutil.copy(cfg.sdc, rd / "inputs" / cfg.sdc.name)
    for f in cfg.rtl:
        shutil.copy(f, rd / "inputs" / f.name)
    top_v = write_top(cfg, rd / "inputs" / "top.v")

    t0 = time.time()
    m = {"tag": tag, "design": cfg.design, "status": "running",
         "inputs_sha": _sha([*cfg.rtl, cfg.sdc, rd / "inputs" / "config.json"]),
         "params": cfg.params, "synth_opts": cfg.synth,
         "constraints": parse_sdc(cfg.sdc.read_text()), "stages": {}}

    def save():
        m["wall_seconds"] = round(time.time() - t0, 1)
        (rd / "metrics.json").write_text(json.dumps(m, indent=2))
        if not dashboard_enabled():
            return
        try:
            import dashboard
            dashboard.build()
        except Exception as e:  # dashboard must never break the flow
            print(f"[dashboard] {e}")

    save()
    print(f"[{tag}] lint ...", flush=True)
    m["stages"]["lint"] = lint(cfg.rtl, top_v, cfg.top, rd)
    if not m["stages"]["lint"]["ok"]:
        m["status"] = "fail_lint"; save(); return m

    print(f"[{tag}] RTL simulation (firmware test suite) ...", flush=True)
    m["stages"]["rtl_sim"] = rtl_sim(cfg.rtl, top_v, rd)
    if not m["stages"]["rtl_sim"]["pass"]:
        m["status"] = "fail_rtl_sim"; save(); return m

    print(f"[{tag}] synthesis (yosys/abc -> sky130hd) ...", flush=True)
    sy = run_synth(cfg.rtl, top_v, cfg.top, cfg.clock_period_ns, cfg.clock_uncertainty_ns, cfg.synth, rd)
    m["stages"]["synth"] = {k: v for k, v in sy.items() if k != "pre_map_cells"}
    if not sy["ok"]:
        m["status"] = "fail_synth"; save(); return m

    print(f"[{tag}] static timing analysis ...", flush=True)
    sta = run_sta(rd / "synth" / "netlist.json", cfg.top, cfg.sdc, n_paths=3)
    m["stages"]["sta"] = sta
    save()

    if not skip_power:
        print(f"[{tag}] gate-level simulation + power ({'full workload' if not pwr_cycles else pwr_cycles} cycles) ...", flush=True)
        nj = json.loads((rd / "synth" / "netlist.json").read_text())["modules"][cfg.top]["cells"]
        gls = gate_sim(rd / "synth" / "netlist.v", {c["type"] for c in nj.values()}, rd, pwr_cycles)
        m["stages"]["gls"] = gls
        ok = gls["pass"] or gls["fail_reason"] is None and pwr_cycles
        if not ok:
            m["status"] = "fail_gls"; save(); return m
        pw = estimate_power(rd / "synth" / "netlist.json", cfg.top, Path(gls["activity_file"]),
                            gls["cycles"], cfg.clock_period_ns, m["constraints"]["po_load"])
        m["stages"]["power"] = pw

    # ---- headline PPA ----
    rs = m["stages"]["rtl_sim"]
    fmax = sta["fmax_mhz"]
    ppa = {
        "area_um2": sy["area_um2"], "num_cells": sy["num_cells"], "num_ff": sy["num_ff"],
        "target_mhz": round(1000 / cfg.clock_period_ns, 1), "wns_ns": sta["wns_ns"], "tns_ns": sta["tns_ns"],
        "fmax_mhz": fmax, "timing_met": sta["wns_ns"] >= 0,
        "workload_cycles": rs["cycles"], "cpi": round(rs["cycles"] / max(1, rs["instr_fetches"]), 2),
        "workload_runtime_us_at_fmax": round(rs["cycles"] / fmax, 1),
    }
    if "power" in m["stages"]:
        pw = m["stages"]["power"]
        ppa.update({"power_mw_at_target": pw["total_mw"], "energy_per_cycle_pj": pw["energy_per_cycle_pj"],
                    "workload_energy_uj": round(pw["energy_per_cycle_pj"] * rs["cycles"] * 1e-6, 3)})
    m["ppa"] = ppa
    m["status"] = "ok"
    save()
    write_report(m, rd / "report.md")
    print(f"[{tag}] done in {m['wall_seconds']} s -> {rd / 'report.md'}", flush=True)
    return m


def write_report(m: dict, out: Path):
    p, st = m["ppa"], m["stages"]
    sy, sta = st["synth"], st["sta"]
    L = [f"# PPA report: {m['design']} / {m['tag']}", "",
         f"inputs sha `{m['inputs_sha']}` · status **{m['status']}** · wall {m['wall_seconds']} s", "",
         "## Headline", "", "| metric | value |", "|---|---|",
         f"| Area (cell) | {p['area_um2']:,.0f} um2 ({p['num_cells']:,} cells, {p['num_ff']:,} flops) |",
         f"| Timing | target {p['target_mhz']} MHz, WNS {p['wns_ns']} ns, TNS {p['tns_ns']} ns, Fmax {p['fmax_mhz']} MHz |",
         f"| Performance | {p['workload_cycles']:,} cycles, CPI {p['cpi']}, {p['workload_runtime_us_at_fmax']:,} us @ Fmax |"]
    if "power_mw_at_target" in p:
        pw = st["power"]
        L += [f"| Power @ {pw['freq_mhz']} MHz | {p['power_mw_at_target']} mW ({p['energy_per_cycle_pj']} pJ/cycle, "
              f"{p['workload_energy_uj']} uJ per workload) |"]
    L += ["", "## Verification", "",
          f"- lint: {'OK' if st['lint']['ok'] else 'FAIL'} ({st['lint']['warnings']} warnings)",
          f"- RTL sim: {'PASS' if st['rtl_sim']['pass'] else 'FAIL'} ({st['rtl_sim']['cycles']:,} cycles)"]
    if "gls" in st:
        g = st["gls"]
        L += [f"- gate-level sim: {'PASS' if g['pass'] else g['window']} ({g['cycles']:,} cycles, {g['seconds']} s)"]
    L += ["", "## Area", "", f"- sequential {sy['seq_area_um2']:,.0f} um2 "
          f"({100 * sy['seq_area_um2'] / sy['area_um2']:.0f}%), combinational {sy['comb_area_um2']:,.0f} um2",
          "- top cell families: " + ", ".join(f"{f} x{n}" for f, n in sy["cell_families_top"][:8]),
          "", "## Timing (setup, ideal clock, wire-load model)", "",
          "| endpoint group | WNS ns | failing/total |", "|---|---|---|"]
    L += [f"| {g['endpoint_group']} | {g['wns_ns']} | {g['n_failing']}/{g['n_endpoints']} |"
          for g in sta["worst_endpoint_groups"][:8]]
    cp = sta["critical_paths"][0]
    L += ["", f"Critical path: `{cp['startpoint']}` -> `{cp['endpoint']}`, slack {cp['slack_ns']} ns, "
          f"logic depth {cp['logic_depth']}", "", "```"]
    L += [f"{s['arrival']:7.3f}  +{s['incr']:.3f}  {s['cell']:12s} {s['net']}" for s in cp["path"]]
    L += ["```"]
    if "power" in st:
        pw = st["power"]
        tot = pw["total_mw"] or 1
        L += ["", f"## Power ({pw['window_cycles']:,}-cycle window, {pw['freq_mhz']} MHz, tt 1.8V)", "",
              "| component | mW | share |", "|---|---|---|"]
        for k in ("clock_mw", "sequential_mw", "combinational_mw", "leakage_mw"):
            L.append(f"| {k[:-3]} | {pw[k]:.4f} | {100 * pw[k] / tot:.1f}% |")
        L += [f"| (leakage in uW) | {pw['leakage_uw']:.3f} uW | |"]
        L += ["", f"avg net toggle rate {pw['avg_net_toggle_rate']} per cycle; clock pin cap {pw['clock_pin_cap_pf']} pF", "",
              "| register | mW | flops | toggle rate |", "|---|---|---|---|"]
        L += [f"| {r['register']} | {r['power_mw']} | {r['n_ff']} | {r['toggle_rate']} |"
              for r in pw["top_registers_by_power"][:12]]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--config", type=Path)
    ap.add_argument("--pwr-cycles", type=int, default=0)
    ap.add_argument("--skip-power", action="store_true")
    a = ap.parse_args()
    r = run_iteration(a.tag, a.config, a.pwr_cycles, a.skip_power)
    print(json.dumps(r.get("ppa", {"status": r["status"]}), indent=1))
