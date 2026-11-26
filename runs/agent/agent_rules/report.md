# Agent session agent_rules

base `iter000_baseline` · proposer **rules** · executor **local** (x4) · window 20,000 cycles · status **done**

## Accepted trajectory

| step | change | cost | runtime | power | area |
|---|---|---|---|---|---|
| 0 | baseline | 1.0 | +0.0% | +0.0% | +0.0% |

## Step 1 (from `agent_rules_s0`, cost 1.0)

Top bottlenecks: power: P1 cpuregs; timing: T1 decoded_imm[1] -> reg_out[31]; congestion: C1 reg_out

| candidate | change | verdict | cost | Δruntime | Δpower | Δarea |
|---|---|---|---|---|---|---|
| agent_rules_s1_0 | Gate upper halves of 64-bit counters | pass | 1.0041 | +0.3% | +0.4% | +0.6% |
| agent_rules_s1_1 | Operand isolation for the idle multiplier | pass | 1.3395 | +84.3% | +0.3% | +0.5% |
| agent_rules_s1_2 | Precompute branch/jump target one state earlier | pass | 1.0045 | -1.2% | +1.7% | +1.3% |
| agent_rules_s1_3 | Try TWO_CYCLE_ALU / TWO_CYCLE_COMPARE | pass | 1.0286 | +5.3% | +1.4% | +0.9% |

Rejected before running:
- Clock-gate rarely-written registers: no machine-applicable patch
- Per-word write-enable clock gating of the register file: no machine-applicable patch
- Parallel-prefix adder for the PC/immediate adder: no machine-applicable patch
- Decouple the register-file read mux from the ALU operand cones: over parallel budget (deferred)
- Replicate / pipeline high-fanout control nets: no machine-applicable patch

**Decision:** no improvement; explore deferred actions from the same state (best 1.0041)

## Step 2 (from `agent_rules_s0`, cost 1.0)

Top bottlenecks: power: P1 cpuregs; timing: T1 decoded_imm[1] -> reg_out[31]; congestion: C1 reg_out

| candidate | change | verdict | cost | Δruntime | Δpower | Δarea |
|---|---|---|---|---|---|---|
| agent_rules_s2_0 | Decouple the register-file read mux from the ALU operand cones | pass | 1.0825 | +16.7% | +0.1% | +7.7% |

Rejected before running:
- Gate upper halves of 64-bit counters: already tried
- Clock-gate rarely-written registers: no machine-applicable patch
- Per-word write-enable clock gating of the register file: no machine-applicable patch
- Operand isolation for the idle multiplier: already tried
- Parallel-prefix adder for the PC/immediate adder: no machine-applicable patch
- Precompute branch/jump target one state earlier: already tried
- Try TWO_CYCLE_ALU / TWO_CYCLE_COMPARE: already tried
- Replicate / pipeline high-fanout control nets: no machine-applicable patch

**Decision:** stop: no candidate improves cost by more than 0.5% (best 1.0825)
