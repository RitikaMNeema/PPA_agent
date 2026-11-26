# PPA report: picorv32 / agent_rules_s1_1

inputs sha `38e0f9f458f81846` · status **ok** · wall 216.2 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 109,703 um2 (10,168 cells, 2,370 flops) |
| Timing | target 100.0 MHz, WNS -10.921 ns, TNS -1921.538 ns, Fmax 47.8 MHz |
| Performance | 622,382 cycles, CPI 6.82, 13,020.5 us @ Fmax |
| Power @ 100.0 MHz | 12.4335 mW (124.33 pJ/cycle, 77.381 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (622,382 cycles)
- gate-level sim: first_20000_cycles (20,001 cycles, 139.7 s)

## Area

- sequential 65,893 um2 (60%), combinational 43,810 um2
- top cell families: edfxtp x1843, o21ai x1112, nor2 x1090, a21oi x972, nand2 x911, dfxtp x527, clkbuf x390, xnor2 x244

## Timing (setup, ideal clock, wire-load model)

| endpoint group | WNS ns | failing/total |
|---|---|---|
| core.genblk1.genblk1.pcpi_mul.mul_waiting | -10.921 | 1/1 |
| core.genblk1.genblk1.pcpi_mul.mul_counter | -8.882 | 7/14 |
| core.genblk1.genblk1.pcpi_mul.rdx | -8.882 | 15/30 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | -8.882 | 63/126 |
| core.genblk1.genblk1.pcpi_mul.rd | -8.882 | 64/128 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | -8.882 | 63/126 |
| core.genblk1.genblk1.pcpi_mul.rs1 | -8.882 | 1/2 |
| core.genblk1.genblk1.pcpi_mul.rs2 | -8.882 | 1/2 |

Critical path: `core.genblk1.genblk1.pcpi_mul.mul_waiting` -> `core.genblk1.genblk1.pcpi_mul.mul_waiting (dfxtp_1/D)`, slack -10.921 ns, logic depth 2

```
  3.932  +3.932  dfxtp_1      core.genblk1.genblk1.pcpi_mul.mul_waiting
 18.362  +14.430  a21oi_1      _4256_
 20.579  +2.217  o21ai_0      _2173_
```

## Power (20,001-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 11.9066 | 95.8% |
| sequential | 0.0982 | 0.8% |
| combinational | 0.4286 | 3.4% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.038 uW | |

avg net toggle rate 0.0247 per cycle; clock pin cap 4.467 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.2269 | 1152 | 0.0002 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2904 | 64 | 0.0 |
| core.genblk2.pcpi_div.divisor | 0.2858 | 63 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2858 | 63 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.2858 | 63 | 0.0 |
| core.count_cycle | 0.2629 | 64 | 0.0312 |
| core.count_instr | 0.2556 | 64 | 0.0034 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1517 | 32 | 0.0354 |
| core.decoded_imm | 0.1501 | 32 | 0.0303 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1485 | 32 | 0.0127 |
| core.dbg_mem_wdata | 0.1454 | 32 | 0.0016 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rd | 0.1452 | 32 | 0.0 |
