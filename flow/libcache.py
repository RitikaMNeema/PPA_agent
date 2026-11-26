"""Parse the liberty file once and cache a compact per-cell summary as JSON.

Per cell we keep what the PPA estimators need:
  area, leakage (nW), pin directions/caps (pF)/functions, ff/latch semantics,
  internal energy per output toggle (pJ), clock-pin energy per edge (pJ),
  flop clk->Q delay and setup time (ns) at nominal slew/load.
Table lookups use a nominal operating point (input slew ~0.05 ns, load ~5 fF)
rather than per-instance interpolation: good enough for iteration-to-iteration
*deltas*, which is what the agent optimizes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from env import BUILD, LIB

NOM_SLEW = 0.05   # ns
NOM_LOAD = 0.005  # pF


def _floats(s) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", str(s))]


def _interp1(xs, ys, x):
    if len(xs) == 1:
        return ys[0]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1] or i == len(xs) - 2:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])


def _lookup(group) -> float:
    """Look up an NLDM/power table at the nominal point (index_1=slew, index_2=load)."""
    vals = [_floats(v) for v in _as_list(group.get("values"))]
    flat = [x for row in vals for x in row]
    i1 = _floats(group.get("index_1")) if group.get("index_1") is not None else []
    i2 = _floats(group.get("index_2")) if group.get("index_2") is not None else []
    if not i1:
        return flat[0] if flat else 0.0
    if not i2:
        return _interp1(i1, flat, NOM_SLEW)
    rows = [flat[r * len(i2):(r + 1) * len(i2)] for r in range(len(i1))]
    col = [_interp1(i2, row, NOM_LOAD) for row in rows]
    return _interp1(i1, col, NOM_SLEW)


def _table(group) -> dict:
    vals = [x for v in _as_list(group.get("values")) for x in _floats(v)]
    i1 = _floats(group.get("index_1")) if group.get("index_1") is not None else []
    i2 = _floats(group.get("index_2")) if group.get("index_2") is not None else []
    return {"i1": i1, "i2": i2, "v": vals}


def table_lookup(t: dict, slew: float, load: float) -> float:
    """Bilinear NLDM lookup (index_1 = input slew, index_2 = output load), with extrapolation."""
    i1, i2, v = t["i1"], t["i2"], t["v"]
    if not i1:
        return v[0] if v else 0.0
    if not i2:
        return _interp1(i1, v, slew)
    n2 = len(i2)
    col = [_interp1(i2, v[r * n2:(r + 1) * n2], load) for r in range(len(i1))]
    return _interp1(i1, col, slew)


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _str(v):
    return str(v).strip('"') if v is not None else None


def build_cache(force: bool = False) -> dict:
    out = BUILD / "libcache.json"
    if out.exists() and not force:
        return json.loads(out.read_text())
    from liberty.parser import parse_liberty
    lib = parse_liberty(LIB.read_text())
    cells = {}
    for cell in lib.get_groups("cell"):
        name = _str(cell.args[0])
        c = {"area": float(cell.get("area", 0)), "leak_nw": float(cell.get("cell_leakage_power", 0)),
             "pins": {}, "ff": None, "latch": None, "dont_use": _str(cell.get("dont_use")) == "true"}
        for ff in cell.get_groups("ff"):
            c["ff"] = {"q": _str(ff.args[0]), "qn": _str(ff.args[1]),
                       "clocked_on": _str(ff.get("clocked_on")), "next_state": _str(ff.get("next_state")),
                       "clear": _str(ff.get("clear")), "preset": _str(ff.get("preset"))}
        for la in cell.get_groups("latch"):
            c["latch"] = {"q": _str(la.args[0]), "enable": _str(la.get("enable")),
                          "data_in": _str(la.get("data_in"))}
        for pin in cell.get_groups("pin"):
            pname = _str(pin.args[0])
            p = {"dir": _str(pin.get("direction")), "cap": float(pin.get("capacitance", 0) or 0),
                 "func": _str(pin.get("function")), "clock": _str(pin.get("clock")) == "true",
                 "e_pj": 0.0, "clkq_ns": None, "setup_ns": None}
            # internal energy: average rise/fall over all arcs on this pin
            es = []
            for ip in pin.get_groups("internal_power"):
                rf = [_lookup(g) for kind in ("rise_power", "fall_power") for g in ip.get_groups(kind)]
                if rf:
                    es.append(sum(rf) / len(rf))
            if es:
                p["e_pj"] = max(0.0, sum(es) / len(es))
            p["arcs"] = []
            p["max_cap"] = float(pin.get("max_capacitance", 0) or 0)
            for t in pin.get_groups("timing"):
                tt = _str(t.get("timing_type")) or "combinational"
                if p["dir"] == "output" and tt in ("combinational", "rising_edge"):
                    arc = {"from": _str(t.get("related_pin")), "type": tt}
                    for k in ("cell_rise", "cell_fall", "rise_transition", "fall_transition"):
                        gs = t.get_groups(k)
                        if gs:
                            arc[k] = _table(gs[0])
                    if "cell_rise" in arc or "cell_fall" in arc:
                        p["arcs"].append(arc)
                if tt == "rising_edge" and p["dir"] == "output":
                    ds = [_lookup(g) for k in ("cell_rise", "cell_fall") for g in t.get_groups(k)]
                    if ds:
                        p["clkq_ns"] = max(ds)
                if tt == "setup_rising":
                    ds = [_lookup(g) for k in ("rise_constraint", "fall_constraint") for g in t.get_groups(k)]
                    if ds:
                        p["setup_ns"] = max(ds)
            c["pins"][pname] = p
        cells[name] = c
    data = {"lib": LIB.name, "vdd": 1.8, "cells": cells}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data))
    return data


if __name__ == "__main__":
    import time
    t = time.time()
    d = build_cache(force=True)
    print(len(d["cells"]), "cells in", round(time.time() - t, 1), "s")
    print(json.dumps(d["cells"]["sky130_fd_sc_hd__dfxtp_1"], indent=1)[:1500])
    print(json.dumps(d["cells"]["sky130_fd_sc_hd__nand2_1"], indent=1)[:800])
