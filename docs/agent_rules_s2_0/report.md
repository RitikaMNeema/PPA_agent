# PPA report: picorv32 / agent_rules_s2_0

inputs sha `b11e2d95c5f63c22` · status **ok** · wall 178.0 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 117,575 um2 (10,196 cells, 2,374 flops) |
| Timing | target 100.0 MHz, WNS -3.725 ns, TNS -453.282 ns, Fmax 72.9 MHz |
| Performance | 600,806 cycles, CPI 6.56, 8,241.5 us @ Fmax |
| Power @ 100.0 MHz | 12.4068 mW (124.07 pJ/cycle, 74.542 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (600,806 cycles)
- gate-level sim: first_20000_cycles (20,001 cycles, 112.7 s)

## Area

- sequential 65,973 um2 (56%), combinational 51,602 um2
- top cell families: edfxtp x1843, o21ai x970, nand2 x952, a21oi x945, nor2 x830, dfxtp x531, mux4 x376, mux2i x308

## Timing (setup, ideal clock, wire-load model)

| endpoint group | WNS ns | failing/total |
|---|---|---|
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | -3.725 | 32/64 |
| core.reg_sh | -3.665 | 5/7 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | -3.177 | 32/64 |
| core.reg_out | -3.136 | 32/32 |
| core.timer | -2.813 | 32/32 |
| core.irq_mask | -2.708 | 32/32 |
| core.reg_next_pc | -1.548 | 10/32 |
| core.alu_out_q | -0.223 | 1/32 |

Critical path: `_7106_` -> `core.genblk1.genblk1.pcpi_mul.pcpi_rs2[4] (edfxtp_1/D)`, slack -3.725 ns, logic depth 7

```
  7.392  +7.392  dfxtp_1      _7106_
 11.753  +4.360  mux4_2       _6912_
 11.925  +0.173  nor2_1       _6907_
 12.386  +0.461  a311oi_1     _6903_
 12.749  +0.363  a31oi_1      _6893_
 13.017  +0.268  a21oi_1      _6857_
 13.175  +0.158  nand2_1      _6855_
 13.243  +0.069  nand2_1      _6869_
```

## Power (20,001-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 11.9250 | 96.1% |
| sequential | 0.1265 | 1.0% |
| combinational | 0.3552 | 2.9% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.041 uW | |

avg net toggle rate 0.0206 per cycle; clock pin cap 4.475 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.227 | 1152 | 0.0002 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2904 | 64 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2878 | 63 | 0.0093 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.2869 | 63 | 0.0065 |
| core.genblk2.pcpi_div.divisor | 0.2858 | 63 | 0.0 |
| core.count_cycle | 0.2628 | 64 | 0.0312 |
| core.count_instr | 0.2557 | 64 | 0.0035 |
| core.decoded_imm | 0.1505 | 32 | 0.0333 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1488 | 32 | 0.0136 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1486 | 32 | 0.0183 |
| core.dbg_mem_wdata | 0.1454 | 32 | 0.0013 |
| core.genblk2.pcpi_div.dividend | 0.1452 | 32 | 0.0 |
