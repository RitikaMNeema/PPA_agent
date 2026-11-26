# PPA report: picorv32 / agent_rules_s0

inputs sha `35f328a1545143f9` · status **ok** · wall 188.4 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 109,186 um2 (10,100 cells, 2,361 flops) |
| Timing | target 100.0 MHz, WNS -1.353 ns, TNS -9.401 ns, Fmax 88.1 MHz |
| Performance | 622,382 cycles, CPI 6.82, 7,064.5 us @ Fmax |
| Power @ 100.0 MHz | 12.3924 mW (123.92 pJ/cycle, 77.126 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (622,382 cycles)
- gate-level sim: first_20000_cycles (20,001 cycles, 121.6 s)

## Area

- sequential 65,623 um2 (60%), combinational 43,563 um2
- top cell families: edfxtp x1834, o21ai x1055, nor2 x1049, a21oi x971, nand2 x925, dfxtp x527, clkbuf x379, xnor2 x252

## Timing (setup, ideal clock, wire-load model)

| endpoint group | WNS ns | failing/total |
|---|---|---|
| core.reg_out | -1.353 | 5/32 |
| core.reg_next_pc | -1.352 | 6/32 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | -0.775 | 3/64 |
| core.alu_out_q | -0.179 | 1/32 |
| core.genblk2.pcpi_div.dividend | 0.086 | 0/64 |
| core.dbg_mem_addr | 0.414 | 0/90 |
| core.mem_16bit_buffer | 0.866 | 0/32 |
| core.is_beq_bne_blt_bge_bltu_bgeu | 0.931 | 0/1 |

Critical path: `core.decoded_imm[1]` -> `core.reg_out[31] (dfxtp_1/D)`, slack -1.353 ns, logic depth 33

```
  0.543  +0.543  edfxtp_1     core.decoded_imm[1]
  0.775  +0.232  xnor2_4      _7037_
  0.962  +0.187  o21ai_2      _7039_
  1.321  +0.359  maj3_2       _7040_
  1.654  +0.333  maj3_2       _7041_
  1.989  +0.335  maj3_2       _7042_
  2.322  +0.333  maj3_2       _7043_
  2.653  +0.331  maj3_2       _7044_
  2.983  +0.331  maj3_2       _7045_
  3.314  +0.331  maj3_2       _7046_
  3.645  +0.331  maj3_2       _7047_
  3.975  +0.331  maj3_2       _7048_
  4.306  +0.331  maj3_2       _7049_
  4.637  +0.331  maj3_2       _7050_
  4.967  +0.331  maj3_2       _7051_
  5.298  +0.331  maj3_2       _7052_
  5.629  +0.331  maj3_2       _7053_
  5.959  +0.331  maj3_2       _7054_
  6.290  +0.331  maj3_2       _7055_
  6.621  +0.331  maj3_2       _7056_
  6.951  +0.331  maj3_2       _7057_
  7.282  +0.331  maj3_2       _7058_
  7.613  +0.331  maj3_2       _7059_
  7.943  +0.331  maj3_2       _7060_
  8.274  +0.331  maj3_2       _7061_
  8.605  +0.331  maj3_2       _7062_
  8.935  +0.331  maj3_2       _7063_
  9.266  +0.331  maj3_2       _7064_
  9.597  +0.331  maj3_2       _7065_
  9.927  +0.331  maj3_2       _7066_
 10.265  +0.338  maj3_2       _7067_
 10.527  +0.262  a221oi_1     _387_
 10.829  +0.302  a311oi_1     _388_
 11.011  +0.182  a2bb2oi_1    _6485_
```

## Power (20,001-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 11.8603 | 95.7% |
| sequential | 0.1011 | 0.8% |
| combinational | 0.4310 | 3.5% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.038 uW | |

avg net toggle rate 0.025 per cycle; clock pin cap 4.45 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.1861 | 1143 | 0.0002 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2904 | 64 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2896 | 63 | 0.018 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.2868 | 63 | 0.0061 |
| core.genblk2.pcpi_div.divisor | 0.2858 | 63 | 0.0 |
| core.count_cycle | 0.2629 | 64 | 0.0312 |
| core.count_instr | 0.2556 | 64 | 0.0034 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1514 | 32 | 0.0354 |
| core.decoded_imm | 0.1501 | 32 | 0.0303 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1486 | 32 | 0.0127 |
| core.dbg_mem_wdata | 0.1454 | 32 | 0.0016 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rd | 0.1452 | 32 | 0.0 |
