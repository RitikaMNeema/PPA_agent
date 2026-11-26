"""AI advisor: Claude reads the bottleneck report + the RTL around each
bottleneck and returns ranked, verifiable RTL / knob recommendations per
category (Power, Timing, Congestion).

    python flow/advisor.py --tag iter000_baseline           # Claude (needs ANTHROPIC_API_KEY)
    python flow/advisor.py --tag iter000_baseline --rules   # rule-based draft only

Output: runs/<tag>/advice.json  ->  {"rules": {...}, "llm": {...} | null}
The dashboard page runs/bottlenecks.html shows the LLM advice when present and
falls back to the (clearly labelled) rule-based draft otherwise.

This is the "diagnose -> propose" half of the agent loop; phase 3 adds
"apply -> verify -> accept/revert".
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from bottlenecks import RtlIndex, extract
from env import RUNS

MODEL = "claude-opus-5-5"
CATS = ("power", "timing", "congestion")

# what the agent may touch (mirrors the functional-safety rules of the flow)
ALLOWED_PARAMS = ["TWO_STAGE_SHIFT", "BARREL_SHIFTER", "TWO_CYCLE_ALU", "TWO_CYCLE_COMPARE",
                  "ENABLE_FAST_MUL", "ENABLE_REGS_DUALPORT"]
FORBIDDEN_PARAMS = ["ENABLE_DIV", "ENABLE_MUL", "COMPRESSED_ISA", "ENABLE_COUNTERS", "ENABLE_COUNTERS64",
                    "ENABLE_IRQ", "ENABLE_IRQ_QREGS", "ENABLE_IRQ_TIMER", "CATCH_MISALIGN", "CATCH_ILLINSN"]
SYNTH_KNOBS = ["abc_script: speed|area", "adder: ripple|kogge-stone|sklansky|han-carlson",
               "clockgate: on|off (Yosys clockgate -> sky130 dlclkp ICG)", "flatten: true|false",
               "retime: on|off"]

SUGGESTION = {
    "type": "object",
    "properties": {
        "bottleneck_ids": {"type": "array", "items": {"type": "string"}},
        "title": {"type": "string"},
        "kind": {"type": "string", "enum": ["rtl_rewrite", "param_knob", "synth_knob", "constraint"]},
        "rtl_location": {"type": "string", "description": "file:line or line range, or 'n/a' for knobs"},
        "rationale": {"type": "string", "description": "why this bottleneck exists, citing report numbers"},
        "change": {"type": "string", "description": "concrete Verilog sketch or knob setting"},
        "expected_power": {"type": "string"},
        "expected_timing": {"type": "string"},
        "expected_area": {"type": "string"},
        "functional_risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "verification": {"type": "string", "description": "which checks prove behaviour is unchanged"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "edits": {"type": "array", "description": "exact search/replace patch on the RTL; [] for pure knob changes",
                  "items": {"type": "object", "additionalProperties": False, "required": ["file", "search", "replace"],
                            "properties": {"file": {"type": "string"},
                                           "search": {"type": "string", "description": "verbatim RTL text, unique in the file, incl. indentation"},
                                           "replace": {"type": "string"}}}},
        "params": {"type": "array", "description": "core parameter changes; [] if none",
                   "items": {"type": "object", "additionalProperties": False, "required": ["name", "value"],
                             "properties": {"name": {"type": "string"}, "value": {"type": "integer"}}}},
    },
    "required": ["bottleneck_ids", "title", "kind", "rtl_location", "rationale", "change",
                 "expected_power", "expected_timing", "expected_area", "functional_risk",
                 "verification", "confidence", "edits", "params"],
    "additionalProperties": False,
}
SCHEMA = {
    "type": "object",
    "properties": {
        "overall_summary": {"type": "string"},
        "next_iteration_plan": {"type": "array", "items": {"type": "string"},
                                "description": "ordered list of suggestion titles to try first"},
        **{c: {"type": "object",
               "properties": {"diagnosis": {"type": "string"},
                              "suggestions": {"type": "array", "items": SUGGESTION}},
               "required": ["diagnosis", "suggestions"], "additionalProperties": False} for c in CATS},
    },
    "required": ["overall_summary", "next_iteration_plan", *CATS],
    "additionalProperties": False,
}

SYSTEM = f"""You are a senior RTL / physical-design engineer acting as the PPA advisor inside an
automated ASIC flow for the PicoRV32 RISC-V core (sky130_fd_sc_hd, tt 25C 1.80V, Yosys+ABC).
You receive measured bottlenecks (power, timing, pre-placement congestion proxy) anchored to RTL
lines, plus the RTL around each anchor. Recommend concrete changes that improve PPA.

Hard rules:
- Never change architectural behaviour: same ISA (RV32IMC + PicoRV32 IRQ extensions), same
  register-visible results, same memory-interface protocol. Cycle counts MAY change only via the
  allowed parameters.
- Allowed core parameters: {", ".join(ALLOWED_PARAMS)}.
  Forbidden (feature removal is not optimisation): {", ".join(FORBIDDEN_PARAMS)}.
- Available synthesis knobs: {"; ".join(SYNTH_KNOBS)}.
- Every suggestion must name its verification: Verilator lint, the self-checking firmware
  regression (RTL + gate-level), and eqy RTL-vs-RTL equivalence when the change is meant to be
  cycle-exact.
- Cite the report numbers you rely on, reference RTL by line number, and give a Verilog sketch
  for RTL rewrites. Quantify expected impact as a range and say what it depends on.
- Absolute numbers are pre-placement estimates (wire-load model, no clock tree); reason in deltas.
- Prefer 2-4 high-value suggestions per category over long lists. Mark low confidence honestly.
- For every rtl_rewrite give a machine-applicable patch in `edits`: each `search` must be copied
  verbatim from the RTL excerpts (same tabs/spaces, no line-number prefixes) and occur exactly once
  in the file; keep searches short (1-4 lines) but unique. New declarations go next to existing
  ones. Patches are applied in order and rejected if any search does not match exactly once.
  Use `params` for core-parameter knobs. Synthesis knobs need no patch (edits=[], params=[]).
- Edits from different suggestions should not overlap so they can be combined."""


def _context(b: dict, rtl: RtlIndex) -> str:
    """Bottleneck JSON + de-duplicated RTL windows around each anchor."""
    lines_seen, windows = set(), []
    for c in CATS:
        for it in b[c]["items"]:
            for key in ("rtl", "rtl_start"):
                r = it.get(key) or {}
                for ln in (r.get("assign_lines") or [])[:2] + ([r["decl_line"]] if r.get("decl_line") else []):
                    if any(abs(ln - s) < 8 for s in lines_seen):
                        continue
                    lines_seen.add(ln)
                    windows.append(f"--- {r['module']} / {r['rtl_name']} (for {it['id']}) ---\n" + rtl.window(ln))
    slim = {c: {k: v for k, v in b[c].items() if k != "items"} | {
        "items": [{k: v for k, v in it.items() if k not in ("rtl", "rtl_start")} | {
            "rtl": {k: (it.get("rtl") or {}).get(k) for k in ("module", "rtl_name", "decl", "decl_line",
                                                               "assign_lines", "note")}}
                  for it in b[c]["items"]]} for c in CATS}
    return (f"# Run {b['tag']}\nHeadline PPA: {json.dumps(b['ppa'])}\n"
            f"Current core parameters: {json.dumps(b['params'])}\nSynthesis options: {json.dumps(b['synth_opts'])}\n\n"
            f"# Bottlenecks\n{json.dumps(slim, indent=1)}\n\n# RTL excerpts ({b['rtl_file']})\n" + "\n\n".join(windows))


def ask_claude(b: dict, rtl: RtlIndex) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    t0 = time.time()
    prompt = _context(b, rtl)
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt + "\n\nProduce the advice JSON."}],
        thinking={"type": "adaptive"},
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"model declined: {getattr(msg, 'stop_details', None)}")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("response truncated (max_tokens)")
    text = next(blk.text for blk in msg.content if blk.type == "text")
    out = json.loads(text)
    out["_meta"] = {"model": msg.model, "seconds": round(time.time() - t0, 1),
                    "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
                    "prompt_chars": len(prompt)}
    return out


# ------------------------------------------------------------- rule-based draft
def _S(ids, title, kind, loc, why, change, p, t, a, risk, ver, conf="medium", patch=None):
    patch_key = patch
    patch = PATCHES.get(patch, {}) if isinstance(patch, str) else (patch or {})
    return {"bottleneck_ids": ids, "title": title, "kind": kind, "rtl_location": loc, "rationale": why,
            "change": change, "expected_power": p, "expected_timing": t, "expected_area": a,
            "functional_risk": risk, "verification": ver, "confidence": conf,
            "edits": patch.get("edits", []), "params": patch.get("params", []),
            "patch_id": patch_key if isinstance(patch_key, str) else None}


# Hand-written, regression-verified patches for the rule table (exact search/replace on picorv32.v).
_F = "picorv32.v"
PATCHES = {
    "counters_hi_gate": {"edits": [
        {"file": _F, "search": "\t\t\tcount_cycle <= resetn ? count_cycle + 1 : 0;\n",
         "replace": "\t\t\t// PPA: upper word only updates on carry-out of the lower word (enable-only, gatable)\n"
                    "\t\t\tcount_cycle[31:0] <= resetn ? count_cycle[31:0] + 1 : 0;\n"
                    "\t\t\tif (!resetn) count_cycle[63:32] <= 0;\n"
                    "\t\t\telse if (&count_cycle[31:0]) count_cycle[63:32] <= count_cycle[63:32] + 1;\n"},
        {"file": _F, "search": "\t\t\t\t\t\tcount_instr <= count_instr + 1;\n",
         "replace": "\t\t\t\t\t\t// PPA: upper word only updates on carry-out of the lower word\n"
                    "\t\t\t\t\t\tcount_instr[31:0] <= count_instr[31:0] + 1;\n"
                    "\t\t\t\t\t\tif (&count_instr[31:0]) count_instr[63:32] <= count_instr[63:32] + 1;\n"}]},
    "mul_operand_hold": {"edits": [
        {"file": _F, "search": "\t\tif (mul_waiting) begin\n\t\t\tif (instr_rs1_signed)\n",
         "replace": "\t\tif (mul_waiting) begin\n"
                    "\t\t\t// PPA: operand isolation - only capture operands when a MUL actually starts,\n"
                    "\t\t\t// instead of copying pcpi_rs1/rs2 into the 64-bit shift registers every idle cycle\n"
                    "\t\t\tif (mul_start) begin\n"
                    "\t\t\tif (instr_rs1_signed)\n"},
        {"file": _F, "search": "\t\t\tmul_waiting <= !mul_start;\n",
         "replace": "\t\t\tend\n\t\t\tmul_waiting <= !mul_start;\n"}]},
    "pc_imm_precompute": {"edits": [
        {"file": _F, "search": "\treg [7:0] cpu_state;\n",
         "replace": "\treg [7:0] cpu_state;\n\n"
                    "\t// PPA (timing): branch/JAL target precomputed while in ld_rs1/ld_rs2. exec is only\n"
                    "\t// entered from those states and reg_pc/decoded_imm are stable there, so the 32-bit\n"
                    "\t// adder leaves the exec-cycle reg_out path.\n"
                    "\treg [31:0] pc_imm_q;\n"
                    "\talways @(posedge clk)\n"
                    "\t\tif (cpu_state == cpu_state_ld_rs1 || cpu_state == cpu_state_ld_rs2)\n"
                    "\t\t\tpc_imm_q <= reg_pc + decoded_imm;\n"},
        {"file": _F, "search": "\t\t\t\treg_out <= reg_pc + decoded_imm;\n",
         "replace": "\t\t\t\treg_out <= pc_imm_q;\n"}]},
    "two_cycle_alu": {"params": [{"name": "TWO_CYCLE_ALU", "value": 1}]},
    "regs_dualport": {"params": [{"name": "ENABLE_REGS_DUALPORT", "value": 1}]},
}


def rule_based(b: dict) -> dict:
    """Pattern -> fix table.  Deterministic, no LLM; the baseline the LLM must beat."""
    V_EQ = "lint + firmware regression (RTL & gate-level) + eqy (cycle-exact)"
    V_FW = "lint + firmware regression (RTL & gate-level); cycle count may change"
    out = {c: {"diagnosis": b[c].get("summary", "no data"), "suggestions": []} for c in CATS}
    loc = lambda it: f"{(it.get('rtl') or {}).get('file', '?')}:{','.join(map(str, ((it.get('rtl') or {}).get('assign_lines') or [])[:3])) or (it.get('rtl') or {}).get('decl_line')}"

    pw = b["power"]
    if pw["available"]:
        cg = [it for it in pw["items"] if it["signature"] == "clock_gating"]
        if cg:
            tot = sum(it["metric"] for it in cg)
            out["power"]["suggestions"].append(_S(
                [it["id"] for it in cg], "Clock-gate rarely-written registers", "synth_knob", "n/a",
                f"{len(cg)} register groups ({tot:.2f} mW) are clocked every cycle but toggle on <5% of "
                f"cycles; their power is almost entirely clock-pin energy.",
                "synth: clockgate=on (Yosys `clockgate -liberty ... -pos sky130_fd_sc_hd__dlclkp_1 CLK GATE GCLK`); "
                "registers with an enable (edfxtp/mux feedback) become ICG-gated groups",
                f"up to -{0.7 * tot:.1f} mW (most of the clock-pin share of these groups)",
                "neutral; ICG enable path adds a setup check", "slightly smaller (enable muxes removed)",
                "low", V_EQ))
        rf = next((it for it in pw["items"] if it["name"].endswith("cpuregs")), None)
        if rf:
            out["power"]["suggestions"].append(_S(
                [rf["id"]], "Per-word write-enable clock gating of the register file", "rtl_rewrite", loc(rf),
                f"cpuregs = {rf['metric']} mW ({rf['share_pct']}% of total), {rf['n_ff']} flops, toggle "
                f"rate {rf['toggle_rate']}: only one 32-bit word is written per instruction.",
                "generate one ICG per word: `sky130_fd_sc_hd__dlclkp_1 icg_i (.CLK(clk), .GATE(cpuregs_write && latched_rd==i), .GCLK(gclk[i]));`\n"
                "always @(posedge gclk[i]) cpuregs[i] <= cpuregs_wrdata;",
                f"-{0.8 * rf['metric']:.1f} to -{0.9 * rf['metric']:.1f} mW", "neutral",
                "~36 ICG cells added, enable muxes removed", "low", V_EQ))
        iso = [it for it in pw["items"] if "pcpi_mul" in it["name"] or "pcpi_div" in it["name"]]
        if iso:
            out["power"]["suggestions"].append(_S(
                [it["id"] for it in iso], "Operand isolation for the idle multiplier", "rtl_rewrite", loc(iso[0]),
                "while idle (mul_waiting) the multiplier copies pcpi_rs1/pcpi_rs2 into its 64-bit rs1/rs2 shift "
                "registers and zeroes rd/rdx every cycle, even when no MUL is in flight.",
                "capture operands only on `mul_start`; otherwise hold. (The divider has the same pattern - "
                "not patched yet.)",
                "less data switching in the mul datapath (clock-pin power remains until clock gating)",
                "neutral", "neutral", "low", "lint + firmware regression (RTL & gate-level); outputs cycle-exact, "
                "internal rs1/rs2/rd state differs while idle", "medium", "mul_operand_hold"))
        cnt = [it for it in pw["items"] if it["name"] in ("count_cycle", "count_instr")]
        if cnt:
            out["power"]["suggestions"].append(_S(
                [it["id"] for it in cnt], "Gate upper halves of 64-bit counters", "rtl_rewrite", loc(cnt[0]),
                "upper 32 bits of count_cycle/count_instr change once per 2^32 increments but are clocked every cycle.",
                "split into lo/hi; `if (&lo) hi <= hi + 1;` so the hi word is enable-only (gatable)",
                "small now (adder switching); large once clock gating is on (hi word becomes enable-only)",
                "32-bit instead of 64-bit increment carry chain", "neutral", "low", V_EQ, "high", "counters_hi_gate"))

    tm = b["timing"]
    if tm["available"]:
        rc = [it for it in tm["items"] if "ripple-carry" in it.get("signature", "")]
        if rc:
            it = rc[0]
            out["timing"]["suggestions"].append(_S(
                [x["id"] for x in rc], "Parallel-prefix adder for the PC/immediate adder", "synth_knob", loc(it),
                f"critical path {it['name']} has slack {it['metric']} ns, depth {it['logic_depth']}: {it['signature']}.",
                "synth: adder=kogge-stone (or sklansky) via Yosys `techmap -map +/choices/kogge-stone.v` before abc",
                "small increase (more cells toggling)", f"recover the {abs(it['metric']):.2f} ns deficit; 32-bit KS ~= 6-7 levels vs 32",
                "+1-3% comb area", "low", V_EQ))
        if any(it["name"].startswith("reg_out") or "reg_next_pc" in it["name"] for it in tm["items"]):
            it = next(it for it in tm["items"] if "reg_out" in it["name"] or "reg_next_pc" in it["name"])
            out["timing"]["suggestions"].append(_S(
                [x["id"] for x in tm["items"] if x["kind"] == "path"], "Precompute branch/jump target one state earlier",
                "rtl_rewrite", loc(it),
                "reg_pc + decoded_imm and the next-PC mux are evaluated in the same cycle as their use; both "
                "operands are stable from decode.",
                "add `reg [31:0] pc_plus_imm; always @(posedge clk) pc_plus_imm <= reg_pc + decoded_imm;` "
                "in the fetch/decode state and use it in cpu_state_exec",
                "+32 flops (~+0.1 mW)", "removes the adder from the exec-cycle reg_out path", "+32 flops", "medium",
                "lint + firmware regression (RTL & gate-level) + STA; cycle-exact at the ports", "medium",
                "pc_imm_precompute"))
        out["timing"]["suggestions"].append(_S(
            [], "Try TWO_CYCLE_ALU / TWO_CYCLE_COMPARE", "param_knob", "n/a",
            "the ALU result path is near-critical (alu_out_q) and shares the operand muxes.",
            "params: TWO_CYCLE_ALU=1 and/or TWO_CYCLE_COMPARE=1", "neutral",
            "cuts ALU/compare paths; CPI rises slightly", "+~70 flops", "low", V_FW, "medium", "two_cycle_alu"))

    cg = b["congestion"]
    if cg["available"]:
        cones = [it for it in cg["items"] if it["kind"] == "logic_cone"]
        if cones:
            out["congestion"]["suggestions"].append(_S(
                [it["id"] for it in cones], "Decouple the register-file read mux from the ALU operand cones",
                "rtl_rewrite", loc(cones[0]),
                f"the largest cones ({', '.join(it['name'] for it in cones[:3])}) each hold ~2k cells and ~2x the "
                f"design-average pin density - they share the 36:1 cpuregs read mux plus the ALU.",
                "register the read data (`reg_op1/reg_op2` from a dedicated read stage) or enable "
                "ENABLE_REGS_DUALPORT=1 so rs1/rs2 reads are separate, narrower muxes",
                "neutral", "shortens operand paths", "dual-port: +~1-2% area", "low", V_FW, "medium", "regs_dualport"))
        hf = [it for it in cg["items"] if it["kind"] == "high_fanout"]
        if hf:
            out["congestion"]["suggestions"].append(_S(
                [it["id"] for it in hf], "Replicate / pipeline high-fanout control nets", "rtl_rewrite", loc(hf[0]),
                "; ".join(f"{it['name']}: {it['detail']}" for it in hf[:3]),
                "resetn: synchronise once and fan out from a buffered reset tree (or drop reset on datapath "
                "flops that do not need it); mul_waiting/cpu_state: one-hot decode registered per consumer group",
                "slightly lower (fewer buffers)", "removes buffer chains on control nets", "fewer buffers",
                "medium", V_EQ, "medium"))
    plan = [s["title"] for c in CATS for s in out[c]["suggestions"][:1]]
    out["overall_summary"] = (f"Rule-based draft for {b['tag']}: clock power dominates "
                              f"({pw.get('clock_share_pct', '?')}%), timing is limited by "
                              f"{tm['items'][0]['signature'] if tm.get('items') else '?'}.")
    out["next_iteration_plan"] = plan
    return out


def advise(tag: str, use_llm: bool = True) -> dict:
    rd = RUNS / tag
    b = extract(rd)
    (rd / "bottlenecks.json").write_text(json.dumps(b, indent=2))
    res = {"tag": tag, "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "bottlenecks": b, "rules": rule_based(b), "llm": None, "llm_error": None}
    if use_llm:
        try:
            core = next(f for f in (rd / "inputs").glob("*.v") if f.name == b["rtl_file"])
            res["llm"] = ask_claude(b, RtlIndex(core))
        except Exception as e:
            res["llm_error"] = f"{type(e).__name__}: {e}"[:400]
            if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
                res["llm_error"] = "no Anthropic credentials (set ANTHROPIC_API_KEY) - " + res["llm_error"]
    (rd / "advice.json").write_text(json.dumps(res, indent=2))
    try:
        import dashboard
        dashboard.build()
    except Exception as e:
        print(f"[dashboard] {e}")
    return res


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--rules", action="store_true", help="skip the LLM, rule-based draft only")
    a = ap.parse_args()
    r = advise(a.tag, not a.rules)
    src = "claude" if r["llm"] else "rules"
    print(f"advice source: {src}" + (f"  (LLM: {r['llm_error']})" if r["llm_error"] else ""))
    adv = r["llm"] or r["rules"]
    for c in CATS:
        print(f"== {c}: {len(adv[c]['suggestions'])} suggestions")
        for s in adv[c]["suggestions"]:
            print(f"   - [{s['kind']}] {s['title']}  ({s['rtl_location']})")
