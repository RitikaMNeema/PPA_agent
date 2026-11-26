# PPA report: picorv32 / iter000_baseline

inputs sha `ba2cfe5e67b2a252` · status **ok** · wall 2275.9 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 109,186 um2 (10,100 cells, 2,361 flops) |
| Timing | target 100.0 MHz, WNS -1.353 ns, TNS -9.401 ns, Fmax 88.1 MHz |
| Performance | 622,382 cycles, CPI 6.82, 7,064.5 us @ Fmax |
| Power @ 100.0 MHz | 12.8145 mW (128.15 pJ/cycle, 79.758 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (622,382 cycles)
- gate-level sim: PASS (622,382 cycles, 2245.2 s)

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
  0.775  +0.232  xnor2_4      _6778_
  0.962  +0.187  o21ai_2      _6780_
  1.321  +0.359  maj3_2       _6781_
  1.654  +0.333  maj3_2       _6782_
  1.989  +0.335  maj3_2       _6783_
  2.322  +0.333  maj3_2       _6784_
  2.653  +0.331  maj3_2       _6785_
  2.983  +0.331  maj3_2       _6786_
  3.314  +0.331  maj3_2       _6787_
  3.645  +0.331  maj3_2       _6788_
  3.975  +0.331  maj3_2       _6789_
  4.306  +0.331  maj3_2       _6790_
  4.637  +0.331  maj3_2       _6791_
  4.967  +0.331  maj3_2       _6792_
  5.298  +0.331  maj3_2       _6793_
  5.629  +0.331  maj3_2       _6794_
  5.959  +0.331  maj3_2       _6795_
  6.290  +0.331  maj3_2       _6796_
  6.621  +0.331  maj3_2       _6797_
  6.951  +0.331  maj3_2       _6798_
  7.282  +0.331  maj3_2       _6799_
  7.613  +0.331  maj3_2       _6800_
  7.943  +0.331  maj3_2       _6801_
  8.274  +0.331  maj3_2       _6802_
  8.605  +0.331  maj3_2       _6803_
  8.935  +0.331  maj3_2       _6804_
  9.266  +0.331  maj3_2       _6805_
  9.597  +0.331  maj3_2       _6806_
  9.927  +0.331  maj3_2       _6807_
 10.265  +0.338  maj3_2       _6808_
 10.527  +0.262  a221oi_1     _387_
 10.829  +0.302  a311oi_1     _388_
 11.011  +0.182  a2bb2oi_1    _7356_
```

## Power (622,382-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 11.8603 | 92.6% |
| sequential | 0.1683 | 1.3% |
| combinational | 0.7859 | 6.1% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.038 uW | |

avg net toggle rate 0.0476 per cycle; clock pin cap 4.45 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.187 | 1143 | 0.0005 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2919 | 63 | 0.0287 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2905 | 64 | 0.0007 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.289 | 63 | 0.0199 |
| core.genblk2.pcpi_div.divisor | 0.2864 | 63 | 0.0026 |
| core.count_cycle | 0.2629 | 64 | 0.0312 |
| core.count_instr | 0.2561 | 64 | 0.0052 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1555 | 32 | 0.0393 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1544 | 32 | 0.0523 |
| core.decoded_imm | 0.1537 | 32 | 0.053 |
| core.dbg_mem_wdata | 0.1456 | 32 | 0.0026 |
| core.genblk2.pcpi_div.dividend | 0.1453 | 32 | 0.0006 |
