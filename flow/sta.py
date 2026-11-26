"""Minimal graph-based static timing analysis on the Yosys gate netlist.

* NLDM delay/transition tables from the liberty (bilinear interpolation)
* net load = sink pin caps + wire-load-model cap ("Small", from the liberty)
  + SDC set_load on primary outputs
* worst-of-rise/fall propagation (conservative, no unateness tracking)
* setup checks at flop data pins and primary outputs, SDC input/output delays,
  clock uncertainty, ideal clock (pre-CTS)

The point is not to replace OpenSTA; it is to give the agent named,
explainable critical paths (RTL register names) on a machine without Linux.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from libcache import build_cache, table_lookup

# wire_load("Small") from sky130_fd_sc_hd__tt_025C_1v80.lib
WL_CAP_PER_UM = 1.42e-05
WL_FANOUT_LEN = {1: 23.2746, 2: 32.1136, 3: 48.4862, 4: 64.0974, 5: 86.2649, 6: 84.2649}
WL_SLOPE = 8.3631


def wire_cap(fanout: int) -> float:
    if fanout <= 0:
        return 0.0
    length = WL_FANOUT_LEN.get(fanout, WL_FANOUT_LEN[6] + WL_SLOPE * (fanout - 6))
    return length * WL_CAP_PER_UM


def _bitnames(mod: dict) -> dict:
    names = {}
    for name, nn in mod["netnames"].items():
        hidden = nn.get("hide_name", 0)
        for i, b in enumerate(nn["bits"]):
            if isinstance(b, str):
                continue
            label = name if len(nn["bits"]) == 1 else f"{name}[{i}]"
            if b not in names or (names[b][1] and not hidden):
                names[b] = (label, hidden)
    return {b: n for b, (n, _) in names.items()}


def reg_group(name: str) -> str:
    """'core.reg_pc[5]' -> 'core.reg_pc' ; 'core.cpuregs[3][7]' -> 'core.cpuregs'."""
    return re.sub(r"(\[\d+\])+$", "", name.replace("\\", "")).strip()


class Netlist:
    def __init__(self, json_path: Path, top: str):
        mod = json.loads(Path(json_path).read_text())["modules"][top]
        self.lc = build_cache()["cells"]
        self.ports = mod["ports"]
        self.cells = mod["cells"]
        self.names = _bitnames(mod)
        self.driver = {}                     # bit -> (inst, pin) | ("<PI>", port)
        self.sinks = defaultdict(list)       # bit -> [(inst, pin)]
        self.po_bits = set()
        for pname, p in self.ports.items():
            for b in p["bits"]:
                if isinstance(b, str):
                    continue
                if p["direction"] == "input":
                    self.driver[b] = ("<PI>", pname)
                else:
                    self.po_bits.add(b)
        for inst, c in self.cells.items():
            lib = self.lc[c["type"]]
            for pin, bits in c["connections"].items():
                d = lib["pins"].get(pin, {}).get("dir") or c.get("port_directions", {}).get(pin)
                for b in bits:
                    if isinstance(b, str):
                        continue
                    if d == "output":
                        self.driver[b] = (inst, pin)
                    else:
                        self.sinks[b].append((inst, pin))

    def name(self, b) -> str:
        return self.names.get(b, f"n{b}").replace("\\", "")

    def load(self, b, po_load: float) -> float:
        cap = sum(self.lc[self.cells[i]["type"]]["pins"][p]["cap"] for i, p in self.sinks.get(b, []))
        fo = len(self.sinks.get(b, [])) + (1 if b in self.po_bits else 0)
        return cap + wire_cap(fo) + (po_load if b in self.po_bits else 0.0)

    def is_seq(self, inst) -> bool:
        return self.lc[self.cells[inst]["type"]]["ff"] is not None


def parse_sdc(sdc_text: str) -> dict:
    g = lambda pat, d: float(m.group(1)) if (m := re.search(pat, sdc_text)) else d
    period = g(r"set\s+clk_period\s+([\d.]+)", 10.0)
    io_frac = g(r"set\s+io_delay\s+\[expr\s+\$clk_period\s*\*\s*([\d.]+)\]", 0.2)
    return {"period": period, "uncertainty": g(r"set_clock_uncertainty\s+([\d.]+)", 0.0),
            "clk_slew": g(r"set_clock_transition\s+([\d.]+)", 0.1),
            "io_delay": period * io_frac, "po_load": g(r"set_load\s+([\d.]+)", 0.0),
            "false_from": re.findall(r"set_false_path\s+-from\s+\[get_ports\s+(\w+)\]", sdc_text),
            "clock_port": (re.search(r"create_clock.*get_ports\s+(\w+)", sdc_text) or [None, "clk"])[1]}


def run_sta(netlist_json: Path, top: str, sdc_path: Path, n_paths: int = 1) -> dict:
    sdc = parse_sdc(Path(sdc_path).read_text())
    nl = Netlist(netlist_json, top)
    lc = nl.lc
    T, unc = sdc["period"], sdc["uncertainty"]
    arr, slew, pred = {}, {}, {}          # bit -> arrival ns / slew ns / (prev_bit, inst, incr)
    load = {}
    L = lambda b: load.setdefault(b, nl.load(b, sdc["po_load"]))

    # --- startpoints ---
    for pname, p in nl.ports.items():
        if p["direction"] != "input" or pname == sdc["clock_port"] or pname in sdc["false_from"]:
            continue
        for b in p["bits"]:
            if not isinstance(b, str):
                arr[b], slew[b], pred[b] = sdc["io_delay"], 0.05, None
    for inst, c in nl.cells.items():
        if not nl.is_seq(inst):
            continue
        for pin, bits in c["connections"].items():
            pl = lc[c["type"]]["pins"][pin]
            if pl["dir"] != "output":
                continue
            for b in bits:
                if isinstance(b, str):
                    continue
                d = s = 0.0
                for a in pl["arcs"]:
                    d = max(d, *(table_lookup(a[k], sdc["clk_slew"], L(b)) for k in ("cell_rise", "cell_fall") if k in a))
                    s = max(s, *(table_lookup(a[k], sdc["clk_slew"], L(b)) for k in ("rise_transition", "fall_transition") if k in a))
                arr[b], slew[b], pred[b] = d, s, (None, inst, d)

    # --- topological propagation through combinational cells ---
    comb = [i for i in nl.cells if not nl.is_seq(i)]
    indeg, users = {}, defaultdict(list)
    for inst in comb:
        c = nl.cells[inst]
        deps = set()
        for pin, bits in c["connections"].items():
            if lc[c["type"]]["pins"][pin]["dir"] == "output":
                continue
            for b in bits:
                if isinstance(b, str):
                    continue
                drv = nl.driver.get(b)
                if drv and drv[0] != "<PI>" and not nl.is_seq(drv[0]):
                    deps.add(drv[0])
        indeg[inst] = len(deps)
        for d in deps:
            users[d].append(inst)
    queue = [i for i in comb if indeg[i] == 0]
    n_done = 0
    while queue:
        inst = queue.pop()
        n_done += 1
        c = nl.cells[inst]
        pins = lc[c["type"]]["pins"]
        conn = c["connections"]
        for opin, obits in conn.items():
            if pins[opin]["dir"] != "output":
                continue
            ob = obits[0]
            if isinstance(ob, str):
                continue
            best, best_s, best_from = None, 0.0, None
            for a in pins[opin]["arcs"]:
                ib = conn.get(a["from"], [None])[0]
                if ib is None or isinstance(ib, str) or ib not in arr:
                    continue
                d = max(table_lookup(a[k], slew[ib], L(ob)) for k in ("cell_rise", "cell_fall") if k in a)
                s = max(table_lookup(a[k], slew[ib], L(ob)) for k in ("rise_transition", "fall_transition") if k in a)
                best_s = max(best_s, s)
                if best is None or arr[ib] + d > best:
                    best, best_from = arr[ib] + d, (ib, inst, d)
            if best is not None:
                arr[ob], slew[ob], pred[ob] = best, best_s, best_from
        for u in users[inst]:
            indeg[u] -= 1
            if indeg[u] == 0:
                queue.append(u)
    loops = len(comb) - n_done

    # --- endpoints ---
    ends = []   # (slack, bit, endpoint label, required)
    for inst, c in nl.cells.items():
        if not nl.is_seq(inst):
            continue
        pins = lc[c["type"]]["pins"]
        qname = next((nl.name(b[0]) for p, b in c["connections"].items()
                      if pins[p]["dir"] == "output" and not isinstance(b[0], str)), inst)
        for pin, bits in c["connections"].items():
            pl = pins[pin]
            if pl["dir"] != "input" or pl["clock"]:
                continue
            b = bits[0]
            if isinstance(b, str) or b not in arr:
                continue
            req = T - (pl["setup_ns"] or 0.0) - unc
            ends.append((req - arr[b], b, f"{qname} ({c['type'].split('__')[1]}/{pin})", req, qname))
    for b in nl.po_bits:
        if b in arr:
            req = T - sdc["io_delay"] - unc
            ends.append((req - arr[b], b, f"{nl.name(b)} (output port)", req, nl.name(b)))
    ends.sort(key=lambda e: e[0])

    def trace(b):
        path = []
        while b is not None and b in pred:
            p = pred[b]
            if p is None:
                path.append({"net": nl.name(b), "cell": "input port", "incr": round(arr[b], 3), "arrival": round(arr[b], 3)})
                break
            prev, inst, incr = p
            path.append({"net": nl.name(b), "cell": nl.cells[inst]["type"].split("__")[1],
                         "incr": round(incr, 3), "arrival": round(arr[b], 3)})
            b = prev
        return list(reversed(path))

    worst_by_group = {}
    for s, b, label, req, q in ends:
        g = reg_group(q)
        if g not in worst_by_group:
            worst_by_group[g] = {"endpoint_group": g, "wns_ns": round(s, 3), "n_failing": 0, "n_endpoints": 0}
        worst_by_group[g]["n_endpoints"] += 1
        worst_by_group[g]["n_failing"] += int(s < 0)
    start_groups = defaultdict(lambda: 1e9)
    for s, b, *_ in ends[:300]:
        tr = trace(b)
        if tr:
            start_groups[reg_group(tr[0]["net"])] = min(start_groups[reg_group(tr[0]["net"])], s)

    wns = ends[0][0] if ends else 0.0
    paths = []
    for s, b, label, req, q in ends[:n_paths]:
        p = trace(b)
        paths.append({"endpoint": label, "startpoint": p[0]["net"] if p else None,
                      "slack_ns": round(s, 3), "required_ns": round(req, 3),
                      "arrival_ns": round(arr[b], 3), "logic_depth": len(p) - 1, "path": p})
    crit_arrival = arr[ends[0][1]] if ends else 0.0
    # min period: the worst path must fit in (T - setup - unc)  => T_min = T - wns
    return {
        "clock_period_ns": T, "uncertainty_ns": unc,
        "wns_ns": round(wns, 3), "tns_ns": round(sum(min(0, e[0]) for e in ends), 3),
        "n_endpoints": len(ends), "n_failing": sum(1 for e in ends if e[0] < 0),
        "min_period_ns": round(T - wns, 3), "fmax_mhz": round(1000.0 / (T - wns), 1),
        "critical_arrival_ns": round(crit_arrival, 3),
        "comb_loops_skipped": loops,
        "critical_paths": paths,
        "worst_endpoint_groups": sorted(worst_by_group.values(), key=lambda g: g["wns_ns"])[:15],
        "worst_startpoint_groups": [{"startpoint_group": g, "wns_ns": round(s, 3)}
                                    for g, s in sorted(start_groups.items(), key=lambda x: x[1])[:10]],
    }


if __name__ == "__main__":
    import sys
    r = run_sta(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), n_paths=1)
    print(json.dumps({k: v for k, v in r.items() if k != "critical_paths"}, indent=1))
    for st in r["critical_paths"][0]["path"]:
        print(f"  {st['arrival']:7.3f} (+{st['incr']:.3f})  {st['cell']:14s} {st['net']}")
