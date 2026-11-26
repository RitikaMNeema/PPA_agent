# PPA report: picorv32 / agent_rules_s1_3

inputs sha `b5063bb735ac3ebc` · status **ok** · wall 218.4 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 110,199 um2 (10,066 cells, 2,406 flops) |
| Timing | target 100.0 MHz, WNS -0.982 ns, TNS -3.0 ns, Fmax 91.1 MHz |
| Performance | 677,612 cycles, CPI 7.34, 7,438.1 us @ Fmax |
| Power @ 100.0 MHz | 12.5657 mW (125.66 pJ/cycle, 85.149 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (677,612 cycles)
- gate-level sim: first_20000_cycles (20,001 cycles, 133.1 s)

## Area

- sequential 66,614 um2 (60%), combinational 43,586 um2
- top cell families: edfxtp x1843, nand2 x1020, o21ai x1007, a21oi x922, nor2 x863, dfxtp x563, clkbuf x375, o22ai x264

## Timing (setup, ideal clock, wire-load model)

| endpoint group | WNS ns | failing/total |
|---|---|---|
| core.reg_next_pc | -0.982 | 6/32 |
| core.alu_add_sub | 0.393 | 0/32 |
| core.genblk2.pcpi_div.dividend | 0.547 | 0/64 |
| core.dbg_mem_addr | 0.718 | 0/90 |
| core.reg_out | 1.192 | 0/32 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 1.397 | 0/64 |
| core.count_cycle | 1.692 | 0/64 |
| core.mem_16bit_buffer | 2.255 | 0/32 |

Critical path: `core.irq_state[0]` -> `core.reg_next_pc[30] (dfxtp_1/D)`, slack -0.982 ns, logic depth 34

```
  1.004  +1.004  dfxtp_1      core.irq_state[0]
  1.381  +0.377  nand2b_1     _2569_
  1.619  +0.238  and2_1       _2570_
  1.892  +0.273  clkbuf_1     _2571_
  2.314  +0.422  a22oi_2      _2649_
  2.783  +0.469  maj3_1       _2695_
  3.002  +0.219  o211ai_1     _2699_
  3.284  +0.282  a31oi_1      _2701_
  3.740  +0.457  maj3_1       _2702_
  3.950  +0.210  o221ai_1     _2706_
  4.218  +0.269  and3_1       _2707_
  4.399  +0.180  o21bai_1     _2708_
  4.850  +0.451  maj3_1       _2709_
  5.249  +0.399  maj3_1       _2710_
  5.649  +0.399  maj3_1       _2711_
  6.048  +0.399  maj3_1       _2712_
  6.442  +0.394  maj3_1       _2713_
  6.662  +0.220  a21oi_1      _2716_
  6.903  +0.241  o21ai_1      _2718_
  7.337  +0.434  maj3_1       _2719_
  7.731  +0.394  maj3_1       _2720_
  7.948  +0.217  a21oi_1      _2722_
  8.195  +0.247  o21a_1       _2724_
  8.308  +0.114  nor2_1       _2725_
  8.488  +0.180  and2_1       _2727_
  8.581  +0.093  nand3_1      _2731_
  8.785  +0.204  a31oi_1      _2736_
  8.910  +0.125  nand2_1      _2738_
  9.305  +0.395  or3b_1       _2742_
  9.492  +0.187  a31oi_1      _2748_
  9.789  +0.297  nor3b_1      _2750_
 10.162  +0.372  or3_1        _5975_
 10.246  +0.084  nand3_1      _5977_
 10.440  +0.194  o2bb2ai_1    _5979_
 10.640  +0.201  a22o_1       _1084_
```

## Power (20,001-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 12.0722 | 96.1% |
| sequential | 0.0947 | 0.8% |
| combinational | 0.3988 | 3.2% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.039 uW | |

avg net toggle rate 0.0226 per cycle; clock pin cap 4.536 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.2269 | 1152 | 0.0002 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2904 | 64 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2893 | 63 | 0.0164 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.2866 | 63 | 0.0052 |
| core.genblk2.pcpi_div.divisor | 0.2858 | 63 | 0.0 |
| core.count_cycle | 0.2625 | 64 | 0.0312 |
| core.count_instr | 0.2556 | 64 | 0.0031 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1514 | 32 | 0.0323 |
| core.decoded_imm | 0.1496 | 32 | 0.0282 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1484 | 32 | 0.011 |
| core.dbg_mem_wdata | 0.1454 | 32 | 0.0013 |
| core.genblk2.pcpi_div.quotient | 0.1452 | 32 | 0.0 |
