# VLSI PPA Agent — LLM-guided RTL optimization with verification-gated changes

An AI agent that improves the **Power / Performance / Area (PPA)** of a real RISC-V
CPU core (PicoRV32). It runs an open-source ASIC flow, reads the reports,
**diagnoses bottlenecks**, asks an LLM (Claude) for **RTL rewrites and tuning
changes as machine-applicable patches**, and accepts a change only after it
passes lint and a full firmware regression.

*Author: Ritika Neema, M.S. student (AI/ML). This is a personal project on applying LLM agents to
chip design flows (AI for CAD / flow methodology).*

```
config.json + RTL + SDC
        │
        ▼
 lint ─► RTL sim ─► synth ─► STA ─► gate-level sim ─► power ─► metrics.json / report.md
(Verilator) (Icarus,  (Yosys+ABC, (NLDM,     (same firmware,   (toggles x liberty
          firmware)   sky130hd)  wire-load)   netlist)          energy + leakage)
        ▲                                                        │
        │        bottleneck extraction (power / timing / congestion, RTL-anchored)
        │                                                        │
        │        LLM advisor ──► structured suggestions + patches ◄┘
        │                                                        │
        └── candidate RTL ◄── patch apply + guardrails ◄── verify (lint + regression)
```

## Why this project
Design-flow teams spend a lot of engineering time on the loop *run flow → read
reports → find the bottleneck → change RTL/constraints → re-run*. The question I
wanted to answer: **can an LLM take part in that loop safely?** "Safely" means
every change it proposes is grounded in report evidence, can be applied by a
machine, and is verified before it is trusted.

## AI / ML components
| Component | What it does | Where |
|---|---|---|
| **Evidence extraction (LLM grounding)** | Turns raw EDA reports into a compact, ranked bottleneck list. Each item is anchored to exact RTL lines (module/register resolution, port tracing through hierarchy). Only this evidence goes into the prompt, not 40 MB of logs. | `flow/bottlenecks.py` |
| **LLM advisor with structured outputs** | Claude receives the bottlenecks plus the RTL windows around them and returns suggestions that must match a strict JSON schema: kind, rationale, expected PPA impact, risk, verification plan, confidence, and a **search/replace patch**. | `flow/advisor.py` |
| **Guardrails** | Each patch's search text must match the RTL exactly once (no fuzzy edits). Parameters that remove features (e.g. turning off the multiplier) are forbidden. There is a hard rule against changing behaviour at the core's ports. | `flow/advisor.py`, `flow/candidates.py` |
| **Verification-gated generation** | Every candidate is linted. Patches are run through the full firmware regression, and the cycle count must be identical so the visible behaviour is unchanged. Bad LLM output is rejected, not silently fixed. | `flow/candidates.py`, `flow/verify_patches.py` |
| **Rule-based expert fallback** | A deterministic baseline in the same schema. It keeps the system usable without an API key, and it is the reference the LLM's suggestions are compared against. | `flow/advisor.py` (`rule_based`) |
| **Human-in-the-loop UI** | The engineer reviews each suggestion and its RTL diff, ticks the ones to apply, generates a candidate and launches the next iteration from the browser. | `flow/serve.py`, `runs/bottlenecks.html` |
| **Experiment tracking** | Every iteration is a reproducible run directory (an input snapshot with its sha256, logs, metrics.json). A live dashboard compares iterations. | `flow/run_flow.py`, `flow/dashboard.py` |

## Baseline results (iteration 0, sky130hd, 100 MHz target)
| Metric | Value |
|---|---|
| Area | 109,186 µm² (10,100 cells, 2,361 flops) |
| Timing | WNS −1.353 ns → Fmax 88.1 MHz (critical path: immediate → adder → `reg_out`) |
| Power | 12.81 mW (93% clock/flop internal power; register file 40%) |
| Verification | lint OK, RTL sim PASS, gate-level sim PASS (622,382 cycles) |

Top bottlenecks found automatically, each with an RTL suggestion:
- **Power:** `cpuregs` written rarely but clocked every cycle → clock gating; idle multiplier operands still toggling → operand isolation.
- **Timing:** `reg_pc + decoded_imm` ripple-carry adder on the critical path → precompute the target one state earlier.
- **Congestion:** the `reg_out` input cone holds 24% of all pins; high-fanout `resetn` (471) and `mul_waiting` (232).

All three automatic RTL patches pass lint and the full regression, alone and combined,
with an unchanged cycle count.

## Run
```
.venv\Scripts\python flow\run_flow.py --tag iter000_baseline            # full workload (~40 min)
.venv\Scripts\python flow\run_flow.py --tag quick --pwr-cycles 100000   # windowed power (~3 min)

.venv\Scripts\python flow\bottlenecks.py --tag iter000_baseline   # bottleneck report
.venv\Scripts\python flow\advisor.py --tag iter000_baseline       # LLM advice (needs ANTHROPIC_API_KEY); --rules = no LLM
.venv\Scripts\python flow\serve.py                                # http://127.0.0.1:8765/bottlenecks.html
.venv\Scripts\python flow\candidates.py --tag iter000_baseline --ids power:2,timing:1
.venv\Scripts\python flow\verify_patches.py                       # regression of the patch library
```

## Setup (native Windows, no WSL)
1. Python 3.12+: `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`
2. [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) → `tools/oss-cad-suite` (Yosys, ABC, Icarus, Verilator)
3. [xPack RISC-V GCC](https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack) → `tools/xpack-riscv-none-elf-gcc-*`
4. Optional: set `ANTHROPIC_API_KEY` for the LLM advisor (without it, the rule-based advisor is used)

## Layout
| Path | Contents |
|---|---|
| `flow/` | flow stages, bottleneck extraction, advisor, candidate generation, dashboard/server |
| `design/picorv32/rtl` | working RTL the agent edits |
| `design/picorv32/config.json` | tuning knobs: core parameters + synthesis options |
| `design/picorv32/tb`, `fw` | testbench (RTL and gate level) + self-checking firmware (riscv-tests rv32imc, sieve, mul/div, IRQ) |
| `constraints/picorv32.sdc` | clock, I/O delays, drive/load |
| `pdk/sky130hd` | SkyWater 130nm HD liberty, tt / 25C / 1.80V |
| `runs/<tag>/` | one reproducible iteration: inputs snapshot, metrics, report, bottlenecks, advice |

## Design decisions
- **The LLM proposes, the flow decides.** The model never edits files directly. It emits patches, and the code applies them, checks them and accepts or rejects them.
- **Small grounded context instead of raw logs.** Bottleneck extraction is deterministic and cheap. The LLM only reasons over pre-digested evidence with RTL line anchors, which keeps prompts small and suggestions specific.
- **No proprietary tools.** OpenSTA was not available natively on Windows, so I wrote a small graph-based STA (NLDM tables, wire-load model) and an activity-based power estimator driven by gate-level toggle counts.

## Known limitations
* Timing is pre-placement (ideal clock, wire-load model). Next step: OpenROAD placement/CTS/route.
* Power is zero-delay activity × liberty energies; clock-tree buffers are not modelled (pre-CTS).
* Congestion is a pre-placement proxy (cone pin density, fanout).

These limits are the same in every iteration, so the deltas between iterations are still meaningful.

## Roadmap
- [x] Reproducible flow + PPA reports + live dashboard
- [x] RTL-anchored bottleneck extraction, LLM advisor with structured patches, guardrails
- [x] Candidate generation + human-in-the-loop UI
- [ ] Closed agent loop: propose → verify → run → accept/revert, with a budget and stopping rule
- [ ] Formal equivalence (eqy) for patches that preserve behaviour
- [ ] Clock-gating and prefix-adder synthesis knobs
- [ ] Evaluation: LLM vs rule-based advisor on accepted-patch rate and PPA gain per iteration

## Third-party
PicoRV32 RTL and firmware © Claire Xenia Wolf (ISC license, header retained).
SkyWater sky130 PDK liberty (Apache-2.0). riscv-tests (BSD).
