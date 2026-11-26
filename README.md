# PPA_agent — AI-driven PPA optimization on a distributed ASIC flow

[![ci](https://github.com/RitikaMNeema/PPA_agent/actions/workflows/ci.yml/badge.svg)](https://github.com/RitikaMNeema/PPA_agent/actions/workflows/ci.yml)

An AI system that improves the **Power / Performance / Area (PPA)** of a real RISC-V
CPU core (PicoRV32), built on an open-source ASIC flow. It combines three things:

1. a **closed-loop agent**: diagnose bottlenecks → propose RTL patches (rule library or LLM) → verify → evaluate → accept or revert;
2. **Bayesian optimization** of the tuning knobs, with Gaussian-process surrogate models of PPA;
3. a **distributed job layer** that fans flow runs out to a local process pool, **Apache Spark** or **Docker** containers, the way a design house uses its compute farm.

*Author: Ritika Neema, M.S. student (AI/ML). This is a personal project on applying ML and LLM agents to
chip design flows (AI for CAD / flow methodology).*

```
                        ┌──────────────────────── driver ────────────────────────┐
                        │  agent.py  (observe → propose → guard → evaluate → decide)│
                        │  dse.py    (GP surrogates + Expected-Improvement batches) │
                        └───────────────┬──────────────────────────▲──────────────┘
                              FlowJob   │  executor.py             │  metrics summary
                       (JSON, portable) ▼  local | spark | docker  │
        ┌────────────── worker (one flow run, isolated scratch dir) ──────────────┐
        │ lint ─► RTL sim ─► synth ─► STA ─► gate-level sim ─► power ─► metrics.json │
        │(Verilator)(Icarus) (Yosys+ABC)(NLDM)   (same firmware)  (toggles×liberty)  │
        └───────────────────────────── shared filesystem: runs/<tag>/ ───────────┘
```

## Why this project
Design-flow teams spend much of their time on the loop *run flow → read reports →
find the bottleneck → change RTL/knobs → re-run*. On a real chip each run takes hours,
so the loop is limited by compute and by how many runs you can afford. I wanted to know:

- **Can an LLM agent take part in that loop safely?** Every change must be grounded in report evidence, applicable by a machine, and verified before it is trusted.
- **Can ML cut the number of expensive runs?** A surrogate model predicts PPA, so only the promising configurations get run.
- **What infrastructure does this need at scale?** Many runs at once, on many machines, from a reproducible toolchain image.

## AI / ML components
| Component | What it does | Where |
|---|---|---|
| **Closed-loop agent** | Greedy hill-climbing over RTL patches. It evaluates the top-k candidates **in parallel** on the executor and accepts one only if the PPA cost drops by more than a threshold. Stopping rules cover the step budget, no improving action, and the LLM dollar budget. Every decision is logged to `trajectory.json`. | `flow/agent.py` |
| **Bayesian optimization** | One Gaussian process per metric (RBF kernel with ARD, hyperparameters fit by marginal likelihood, written from scratch in numpy). Monte-Carlo Expected Improvement of the combined cost; batches picked by kriging believer so they can run in parallel. | `flow/surrogate.py`, `flow/dse.py` |
| **Model evaluation** | Leave-one-out CV (MAPE, R²) every round. GP length-scales show which knob drives which metric. A Pareto front shows the trade-offs between metrics. | `flow/surrogate.py`, `flow/objective.py` |
| **Evidence extraction (LLM grounding)** | Reduces raw EDA reports to a ranked list of bottlenecks, each tied to exact RTL lines. Only that list goes into the prompt, not 40 MB of logs. | `flow/bottlenecks.py` |
| **LLM advisor, structured outputs** | Claude returns suggestions in a strict JSON schema: rationale, expected PPA impact, risk, confidence and a **search/replace patch**. A hard dollar budget applies in the agent. | `flow/advisor.py` |
| **Guardrails** | Exact-match patching (no fuzzy edits), a forbidden-parameter list, no repeated actions, lint before any compute is spent, and the firmware regression before a candidate is scored. | `flow/candidates.py`, `flow/agent.py` |
| **Human-in-the-loop UI** | Review the diffs, generate a candidate, launch the next iteration, and watch the DSE and agent progress. | `flow/serve.py`, `runs/*.html` |

## Compute-farm layer (Spark / Docker)
- **One job format.** `FlowJob` is plain JSON (tag, config, power window). `run_job` uses only the standard library, so it ships to Spark executors without the rest of the package.
- **Backends.**
  - `local`: process pool on one machine.
  - `spark`: one Spark task per flow run. Runs as `local[N]` on a laptop or `spark://master:7077` on a cluster, with task retry and placement handled by Spark.
  - `docker`: one container per run, for a hermetic toolchain.
- **Hermetic toolchain.** `docker/Dockerfile` bundles Yosys/ABC, Icarus, Verilator, RISC-V GCC, Python and Spark. `docker/docker-compose.yml` brings up a Spark master, N workers and a driver from that one image, with the repo on a shared volume (standing in for NFS).
- **Lessons learned.**
  - *Shared scratch space.* At 10× parallelism, concurrent Yosys/ABC processes collided in the shared temp directory and runs failed spuriously. Each job now gets its own scratch directory.
  - *Shared caches.* Firmware and the liberty cache are built once on the driver before fan-out, so workers never race to create them.
  - *Shipping code to executors.* The worker module must be importable on the executors: `PYTHONPATH` in local mode, `addPyFile` on a cluster.

## Results

**Baseline (iteration 0, sky130hd, 100 MHz target):** 109,186 µm², Fmax 88.1 MHz (WNS −1.353 ns), 12.8 mW
(93% clock/flop internal power), full firmware regression and gate-level sim pass (622,382 cycles).

**Bayesian optimization on Spark** (`runs/dse/report.md`, 20k-cycle power window):

| | value |
|---|---|
| configurations evaluated | 26 of 128 (10 random + 4 BO rounds × 5) |
| wall time | 17.6 min for 87 min of flow time (**4.9× speed-up**, 6 Spark workers) |
| best found | `BARREL_SHIFTER=1, TWO_CYCLE_COMPARE=1, TWO_STAGE_SHIFT=0`: **runtime −4.4%**, power −0.2%, area +1.8%, cost 0.986 |
| who found it | BO round 3. None of the 10 random configurations beat the baseline; both improving configs came from BO |
| surrogate LOO error | runtime 4.7% (R² 0.84), power 0.25% (R² 0.98), area 0.4% (R² 0.997) |
| learned relevance | area is driven almost entirely by `ENABLE_FAST_MUL`; runtime by the shifter and multiplier choices |

**Agent session with the rule proposer** (`runs/agent/agent_rules/report.md`): 5 candidate patches over 2 steps,
all verified, **none accepted**. The timing patch (precompute branch target) made the design 1.2% faster, but its power and area cost cancelled the gain.
Multiplier operand isolation passed the regression but dropped Fmax (+84% runtime), and the gate rejected it.
That is the intended behaviour: the hand-written rule library does not improve this design under the combined score.
Two things should change that: clock-gating support in the flow, and LLM-proposed patches (`--proposer llm --max-usd N`).

## Run
```
# one flow iteration
.venv\Scripts\python flow\run_flow.py --tag quick --pwr-cycles 20000

# Bayesian-optimization DSE on Spark (local[6] here; --master spark://host:7077 on a cluster)
.venv\Scripts\python flow\dse.py --executor spark --workers 6 --init 10 --rounds 3 --batch 5

# closed-loop agent (rules = free; llm = paid API, hard budget required)
.venv\Scripts\python flow\agent.py --base iter000_baseline --steps 4 --parallel 4
.venv\Scripts\python flow\agent.py --proposer llm --max-usd 2.00

# UI: dashboard, bottlenecks + RTL feedback, exploration + agent
.venv\Scripts\python flow\serve.py        # http://127.0.0.1:8765/dashboard.html

# tests (no EDA tools needed)
.venv\Scripts\python -m pytest -q tests
```

### On a cluster (Docker)
```
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d --scale spark-worker=4 spark-master spark-worker
docker compose -f docker/docker-compose.yml run --rm dse      # Spark UI: http://localhost:8080
docker compose -f docker/docker-compose.yml run --rm agent
```

## Setup (native Windows, no WSL)
1. Python 3.12+: `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`
2. Java 17+ (for Spark)
3. [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) → `tools/oss-cad-suite`; [xPack RISC-V GCC](https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack) → `tools/xpack-riscv-none-elf-gcc-*`
4. Optional: `ANTHROPIC_API_KEY` for the LLM proposer/advisor

## Layout
| Path | Contents |
|---|---|
| `flow/run_flow.py` … `power.py` | flow stages (lint, sim, synth, STA, power) |
| `flow/executor.py` | FlowJob + local / Spark / Docker backends |
| `flow/dse.py`, `surrogate.py`, `objective.py` | design-space exploration, GP surrogates, BO, Pareto |
| `flow/agent.py` | closed-loop agent |
| `flow/bottlenecks.py`, `advisor.py`, `candidates.py` | evidence, LLM/rule proposals, guarded patching |
| `flow/dashboard.py`, `serve.py`, `*_page.py` | UI |
| `docker/` | toolchain image + Spark cluster compose |
| `tests/`, `.github/workflows/ci.yml` | unit tests + CI (unit tests, Docker build and container smoke test) |
| `design/picorv32`, `constraints`, `pdk/sky130hd` | RTL, testbench, firmware, SDC, liberty |
| `runs/` | iterations, `dse/` (dataset, report), `agent/<session>/` (trajectory, report) |

## Known limitations
* Timing is pre-placement (ideal clock, wire-load model); power is zero-delay activity × liberty energy, pre-CTS.
* DSE and agent use a 20k-cycle power window for speed, measured against a reference with the same window.
* The Docker image is built and smoke-tested in CI (Linux: lint, RTL sim, synth, STA in the container).
  Spark was tested in local mode; the multi-node compose cluster has not yet been run.

## Roadmap
- [x] Reproducible flow, PPA reports, live dashboard
- [x] RTL-anchored bottlenecks, LLM advisor with structured patches, guardrails
- [x] Closed-loop agent with parallel candidate evaluation
- [x] GP surrogate + Bayesian optimization over knobs
- [x] Distributed execution: Spark, Docker, compose cluster, CI
- [ ] Clock-gating and prefix-adder synthesis knobs (unlocks the biggest power suggestion)
- [ ] LLM-vs-rules evaluation: accepted-patch rate and PPA gain per $ and per run
- [ ] Formal equivalence (eqy) as a verification gate
- [ ] OpenROAD placement/routing and real congestion; multi-corner jobs

## Third-party
PicoRV32 RTL and firmware © Claire Xenia Wolf (ISC license, header retained).
SkyWater sky130 PDK liberty (Apache-2.0). riscv-tests (BSD).
