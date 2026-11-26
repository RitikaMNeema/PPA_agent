"""Bottleneck extraction: turn a run's reports into a ranked, RTL-anchored list
of Power / Timing / Congestion bottlenecks.  Deterministic (no LLM) — this is the
evidence the AI advisor reasons over, and what the dashboard shows.

Congestion note: there is no placement in the Windows flow, so congestion is a
*pre-placement proxy* computed from the netlist graph:
  * high-fanout nets        (long, wide nets -> routing demand + buffering)
  * per-register logic cones (cells / pins feeding a register group -> local
                              pin density, mux-heavy read/write networks)
These correlate well with post-route hot spots for flop-based register files.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from sta import Netlist, reg_group

SUBMOD = {"pcpi_mul": "picorv32_pcpi_mul", "pcpi_div": "picorv32_pcpi_div"}


# ----------------------------------------------------------------- RTL anchors
class RtlIndex:
    def __init__(self, rtl: Path):
        self.path = rtl
        self.lines = rtl.read_text(errors="replace").splitlines()
        self.mods = {}
        cur = None
        for i, l in enumerate(self.lines):
            m = re.match(r"\s*module\s+(\w+)", l)
            if m:
                cur = m.group(1)
                self.mods[cur] = [i, len(self.lines)]
            elif re.match(r"\s*endmodule", l) and cur:
                self.mods[cur][1] = i
                cur = None

    @staticmethod
    def split(name: str) -> tuple[str, str]:
        """'core.genblk1.genblk1.pcpi_mul.next_rs2[3]' -> ('picorv32_pcpi_mul', 'next_rs2')"""
        n = reg_group(name.split(" ")[0])
        parts = [p for p in n.split(".") if p not in ("core",) and not p.startswith("genblk")]
        mod = "picorv32"
        for p in parts[:-1]:
            mod = SUBMOD.get(p, mod)
        return mod, parts[-1] if parts else n

    def locate(self, name: str, max_assign: int = 6, _depth: int = 0, prefer: str | None = None) -> dict:
        mod, leaf = self.split(name)
        lo, hi = self.mods.get(mod, (0, len(self.lines)))
        decl, assigns = None, []
        rd = re.compile(rf"^\s*(reg|wire|input|output\s+reg|output)\b.*\b{re.escape(leaf)}\b")
        ra = re.compile(rf"(?<![.\w]){re.escape(leaf)}\s*(\[[^\]]*\])*\s*(<=|=(?!=))")
        for i in range(lo, hi):
            l = self.lines[i]
            if decl is None and rd.search(l):
                decl = i
            if ra.search(l) and not re.match(r"\s*(//|(input|output|reg|wire|integer)\b)", l):
                assigns.append(i)
        # non-blocking (flop) assignments first; for a timing path, lines that also
        # mention the startpoint signal first of all
        assigns.sort(key=lambda i: (not (prefer and re.search(rf"\b{re.escape(prefer)}\b", self.lines[i])),
                                    "<=" not in self.lines[i], i))
        # a submodule input port (flattened netlist named the flop after the port):
        # follow it to the core-level driver, e.g. pcpi_rs1 -> assign pcpi_rs1 = reg_op1
        if decl is not None and self.lines[decl].lstrip().startswith("input") and _depth == 0:
            clo, chi = self.mods.get("picorv32", (0, 0))
            for i in range(clo, chi):
                mm = re.match(rf"\s*assign\s+{re.escape(leaf)}\s*=\s*(\w+)\s*;", self.lines[i])
                if mm:
                    r = self.locate("core." + mm.group(1), max_assign, 1)
                    r["note"] = (f"netlist name '{leaf}' is the {mod} input port; "
                                 f"the flops are core register '{mm.group(1)}' (line {i + 1})")
                    return r
        anchor = assigns[0] if assigns else decl
        snippet = []
        if anchor is not None:
            for i in range(max(lo, anchor - 3), min(hi, anchor + 4)):
                snippet.append(f"{i + 1:5d}: {self.lines[i]}")
        return {"rtl_name": leaf, "module": mod, "file": self.path.name,
                "decl_line": decl + 1 if decl is not None else None,
                "decl": self.lines[decl].strip() if decl is not None else None,
                "assign_lines": [a + 1 for a in assigns[:max_assign]], "n_assigns": len(assigns),
                "snippet": "\n".join(snippet)}

    def window(self, line: int, before: int = 6, after: int = 6) -> str:
        return "\n".join(f"{i + 1:5d}: {self.lines[i]}"
                         for i in range(max(0, line - 1 - before), min(len(self.lines), line + after)))


def short(name: str) -> str:
    return re.sub(r"^core\.(genblk\d+\.)*", "", name)


# ------------------------------------------------------------------- power
def power_bottlenecks(m: dict, rtl: RtlIndex, n: int = 8) -> dict:
    pw = m["stages"].get("power")
    if not pw:
        return {"available": False, "items": []}
    tot = pw["total_mw"]
    f = pw["freq_mhz"]
    items = []
    for r in pw["top_registers_by_power"][:n]:
        # with a 0..1 toggle rate per flop/cycle, a register is a clock-gating
        # candidate when it is clocked every cycle but rarely changes
        tr = r["toggle_rate"]
        kind = ("clock_gating" if tr < 0.05 else
                "operand_isolation" if "pcpi" in r["register"] else "activity")
        items.append({
            "id": f"P{len(items) + 1}", "name": short(r["register"]), "full_name": r["register"],
            "metric": r["power_mw"], "unit": "mW", "share_pct": round(100 * r["power_mw"] / tot, 1),
            "detail": f"{r['n_ff']} flops, toggle rate {tr}/cycle"
                      f" -> {100 * (1 - min(tr, 1)):.1f}% of clock edges do no useful work",
            "n_ff": r["n_ff"], "toggle_rate": tr, "signature": kind,
            "rtl": rtl.locate(r["register"])})
    return {"available": True, "total_mw": tot, "freq_mhz": f,
            "clock_share_pct": round(100 * pw["clock_mw"] / tot, 1),
            "summary": f"{pw['clock_mw']:.2f} of {tot:.2f} mW ({100 * pw['clock_mw'] / tot:.0f}%) is clock power;"
                       f" average net toggle rate {pw['avg_net_toggle_rate']}/cycle",
            "items": items}


# ------------------------------------------------------------------ timing
def _path_signature(path: list[dict]) -> tuple[str, dict]:
    fam = Counter(re.sub(r"_\d+$", "", s["cell"]) for s in path[1:])
    maj = fam.get("maj3", 0) + fam.get("fa", 0)
    if maj >= 8:
        sig = f"ripple-carry adder chain ({maj} carry cells in series)"
    elif fam.get("mux2", 0) + fam.get("mux4", 0) >= 6:
        sig = "deep mux tree"
    else:
        sig = "random logic"
    return sig, dict(fam.most_common(6))


def timing_bottlenecks(m: dict, rtl: RtlIndex, n: int = 8) -> dict:
    sta = m["stages"].get("sta")
    if not sta:
        return {"available": False, "items": []}
    cps = sta["critical_paths"]
    items = []
    for cp in cps:
        sig, fam = _path_signature(cp["path"])
        items.append({
            "id": f"T{len(items) + 1}", "kind": "path",
            "name": f"{short(cp['startpoint'])} -> {short(cp['endpoint'].split(' ')[0])}",
            "metric": cp["slack_ns"], "unit": "ns slack",
            "detail": f"logic depth {cp['logic_depth']}, arrival {cp['path'][-1]['arrival']:.2f} ns; {sig}",
            "signature": sig, "cell_mix": fam, "logic_depth": cp["logic_depth"],
            "rtl": rtl.locate(cp["endpoint"], prefer=rtl.split(cp["startpoint"])[1]),
            "rtl_start": rtl.locate(cp["startpoint"])})
    for g in sta["worst_endpoint_groups"]:
        if g["wns_ns"] >= 0.5 or len(items) >= n:
            break
        items.append({
            "id": f"T{len(items) + 1}", "kind": "endpoint_group", "name": short(g["endpoint_group"]),
            "metric": g["wns_ns"], "unit": "ns WNS",
            "detail": f"{g['n_failing']}/{g['n_endpoints']} bits failing" if g["n_failing"] else
                      f"near-critical ({g['n_endpoints']} bits, {g['wns_ns']} ns margin)",
            "signature": "failing" if g["wns_ns"] < 0 else "near-critical",
            "rtl": rtl.locate(g["endpoint_group"])})
    return {"available": True, "wns_ns": sta["wns_ns"], "tns_ns": sta["tns_ns"], "fmax_mhz": sta["fmax_mhz"],
            "period_ns": sta["clock_period_ns"],
            "summary": f"WNS {sta['wns_ns']} ns / TNS {sta['tns_ns']} ns, {sta['n_failing']}/{sta['n_endpoints']}"
                       f" endpoints failing, Fmax {sta['fmax_mhz']} MHz",
            "startpoint_groups": [{"name": short(s["startpoint_group"]), "wns_ns": s["wns_ns"]}
                                  for s in sta["worst_startpoint_groups"][:5]],
            "items": items}


# -------------------------------------------------------------- congestion
def congestion_bottlenecks(rd: Path, top: str, rtl: RtlIndex, n: int = 8) -> dict:
    nj = rd / "synth" / "netlist.json"
    if not nj.exists():
        return {"available": False, "items": []}
    nl = Netlist(nj, top)
    area = {i: nl.lc[c["type"]]["area"] for i, c in nl.cells.items()}
    npins = {i: sum(len(b) for b in c["connections"].values()) for i, c in nl.cells.items()}
    seq = {i for i in nl.cells if nl.is_seq(i)}

    # 1) high-fanout nets, grouped by RTL signal
    fo_group = defaultdict(lambda: [0, 0, 0])   # group -> [max fanout, total sinks, n bits]
    for b, sinks in nl.sinks.items():
        drv = nl.driver.get(b)
        if not drv or drv[0] == "<PI>" and drv[1] == "clk":
            continue
        g = reg_group(nl.name(b))
        if re.match(r"^_\d+_$", g) or g.startswith("n"):
            g = f"(unnamed net, driver {nl.cells[drv[0]]['type'].replace('sky130_fd_sc_hd__', '')})" \
                if drv[0] != "<PI>" else g
        e = fo_group[g]
        e[0] = max(e[0], len(sinks)); e[1] += len(sinks); e[2] += 1
    hf = sorted(fo_group.items(), key=lambda kv: -kv[1][0])[:n]

    # 2) per-register-group input logic cone (stops at flops / PIs)
    ff_by_group = defaultdict(list)
    for i in seq:
        q = [b for p, bits in nl.cells[i]["connections"].items() if p in ("Q", "Q_N") for b in bits]
        nm = reg_group(nl.name(q[0])) if q else i
        ff_by_group[nm].append(i)
    cones = []
    for g, ffs in ff_by_group.items():
        seen, stack = set(), []
        for ff in ffs:
            for p, bits in nl.cells[ff]["connections"].items():
                if p in ("CLK", "Q", "Q_N"):
                    continue
                stack += [b for b in bits if not isinstance(b, str)]
        while stack:
            b = stack.pop()
            d = nl.driver.get(b)
            if not d or d[0] == "<PI>" or d[0] in seq or d[0] in seen:
                continue
            seen.add(d[0])
            for p, bits in nl.cells[d[0]]["connections"].items():
                if p != d[1]:
                    stack += [x for x in bits if not isinstance(x, str)]
        if not seen:
            continue
        cell_area = sum(area[c] for c in seen) + sum(area[f] for f in ffs)
        pins = sum(npins[c] for c in seen) + sum(npins[f] for f in ffs)
        mux = sum(1 for c in seen if "mux" in nl.cells[c]["type"])
        cones.append({"group": g, "n_ff": len(ffs), "cone_cells": len(seen), "mux_cells": mux,
                      "pins": pins, "area": cell_area, "pin_density": pins / cell_area})
    total_pins = sum(npins.values())
    total_area = sum(area.values())
    avg_pd = total_pins / total_area
    cones.sort(key=lambda c: -c["pins"])

    items = []
    for c in cones[:max(3, n // 2)]:
        items.append({
            "id": f"C{len(items) + 1}", "kind": "logic_cone", "name": short(c["group"]),
            "metric": c["pins"], "unit": "pins",
            "share_pct": round(100 * c["pins"] / total_pins, 1),
            "detail": f"{c['cone_cells']:,} cells feed {c['n_ff']} flops ({c['mux_cells']:,} muxes);"
                      f" pin density {c['pin_density']:.2f}/um2 vs design avg {avg_pd:.2f}",
            "signature": "mux-heavy cone" if c["mux_cells"] > 0.3 * c["cone_cells"] else "wide cone",
            "rtl": rtl.locate(c["group"])})
    for g, (mx, tot, nb) in hf[:max(3, n - len(items))]:
        items.append({
            "id": f"C{len(items) + 1}", "kind": "high_fanout", "name": short(g),
            "metric": mx, "unit": "fanout",
            "detail": f"max fanout {mx} on one bit ({nb} bits, {tot:,} sinks total)",
            "signature": "high-fanout net",
            "rtl": rtl.locate(g) if not g.startswith("(") else None})
    return {"available": True, "proxy": True,
            "summary": f"pre-placement proxy: {total_pins:,} pins over {total_area:,.0f} um2 cell area"
                       f" (avg {avg_pd:.2f} pins/um2); largest cone {short(cones[0]['group'])}"
                       f" = {100 * cones[0]['pins'] / total_pins:.0f}% of all pins",
            "avg_pin_density": round(avg_pd, 3), "items": items}


def extract(rd: Path) -> dict:
    m = json.loads((rd / "metrics.json").read_text())
    rtl_files = sorted((rd / "inputs").glob("*.v"))
    core = next((f for f in rtl_files if f.name == "picorv32.v"), rtl_files[0])
    rtl = RtlIndex(core)
    top = "picorv32_top"
    return {"tag": m["tag"], "inputs_sha": m.get("inputs_sha"), "rtl_file": core.name,
            "ppa": m.get("ppa", {}), "params": m.get("params", {}), "synth_opts": m.get("synth_opts", {}),
            "power": power_bottlenecks(m, rtl), "timing": timing_bottlenecks(m, rtl),
            "congestion": congestion_bottlenecks(rd, top, rtl)}


if __name__ == "__main__":
    import argparse, sys
    from env import RUNS
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    b = extract(RUNS / a.tag)
    out = RUNS / a.tag / "bottlenecks.json"
    out.write_text(json.dumps(b, indent=2))
    for k in ("power", "timing", "congestion"):
        print(f"== {k}: {b[k].get('summary')}")
        for it in b[k]["items"]:
            r = it.get("rtl") or {}
            print(f"  {it['id']} {it['name']:40s} {it['metric']} {it['unit']}  L{r.get('assign_lines', [])[:3]}  {it['detail']}")
    print(out, file=sys.stderr)
