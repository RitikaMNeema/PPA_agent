# PPA report: picorv32 / agent_rules_s1_2

inputs sha `a9bbbd4ffcdb79e0` · status **ok** · wall 224.3 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 110,557 um2 (10,080 cells, 2,402 flops) |
| Timing | target 100.0 MHz, WNS -1.211 ns, TNS -4.584 ns, Fmax 89.2 MHz |
| Performance | 622,382 cycles, CPI 6.82, 6,977.4 us @ Fmax |
| Power @ 100.0 MHz | 12.6055 mW (126.06 pJ/cycle, 78.457 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (622,382 cycles)
- gate-level sim: first_20000_cycles (20,001 cycles, 139.5 s)

## Area

- sequential 66,854 um2 (60%), combinational 43,703 um2
- top cell families: edfxtp x1875, o21ai x1023, nor2 x980, a21oi x979, nand2 x904, dfxtp x527, clkbuf x385, xnor2 x296

## Timing (setup, ideal clock, wire-load model)

| endpoint group | WNS ns | failing/total |
|---|---|---|
| core.pc_imm_q | -1.211 | 4/64 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | -0.706 | 3/64 |
| core.reg_next_pc | -0.333 | 2/32 |
| core.alu_out_q | 0.201 | 0/32 |
| core.genblk2.pcpi_div.dividend | 0.31 | 0/64 |
| core.dbg_mem_addr | 0.691 | 0/90 |
| core.is_beq_bne_blt_bge_bltu_bgeu | 1.686 | 0/1 |
| core.count_cycle | 1.907 | 0/64 |

Critical path: `core.reg_pc[1]` -> `core.pc_imm_q[31] (edfxtp_1/D)`, slack -1.211 ns, logic depth 32

```
  0.562  +0.562  dfxtp_1      core.reg_pc[1]
  0.753  +0.191  nor2_8       _903_
  0.918  +0.165  o21ai_2      _905_
  1.277  +0.359  maj3_2       _906_
  1.610  +0.333  maj3_2       _907_
  1.943  +0.333  maj3_2       _908_
  2.276  +0.333  maj3_2       _909_
  2.609  +0.333  maj3_2       _910_
  2.943  +0.333  maj3_2       _911_
  3.276  +0.333  maj3_2       _912_
  3.609  +0.333  maj3_2       _913_
  3.942  +0.333  maj3_2       _914_
  4.275  +0.333  maj3_2       _915_
  4.609  +0.333  maj3_2       _916_
  4.942  +0.333  maj3_2       _917_
  5.275  +0.333  maj3_2       _918_
  5.608  +0.333  maj3_2       _972_
  5.941  +0.333  maj3_2       _973_
  6.275  +0.333  maj3_2       _974_
  6.608  +0.333  maj3_2       _975_
  6.941  +0.333  maj3_2       _976_
  7.274  +0.333  maj3_2       _977_
  7.607  +0.333  maj3_2       _978_
  7.940  +0.333  maj3_2       _979_
  8.274  +0.333  maj3_2       _980_
  8.607  +0.333  maj3_2       _981_
  8.940  +0.333  maj3_2       _982_
  9.273  +0.333  maj3_2       _983_
  9.606  +0.333  maj3_2       _984_
  9.940  +0.333  maj3_2       _3218_
 10.273  +0.333  maj3_2       _3219_
 10.590  +0.317  maj3_2       _3220_
 10.730  +0.140  xnor2_1      _1691_
```

## Power (20,001-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 12.0713 | 95.8% |
| sequential | 0.0988 | 0.8% |
| combinational | 0.4354 | 3.5% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.038 uW | |

avg net toggle rate 0.0243 per cycle; clock pin cap 4.527 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.2269 | 1152 | 0.0002 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2904 | 64 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2896 | 63 | 0.018 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.2868 | 63 | 0.0061 |
| core.genblk2.pcpi_div.divisor | 0.2858 | 63 | 0.0 |
| core.count_cycle | 0.2625 | 64 | 0.0312 |
| core.count_instr | 0.2556 | 64 | 0.0034 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1516 | 32 | 0.0354 |
| core.decoded_imm | 0.1502 | 32 | 0.0303 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1486 | 32 | 0.0127 |
| core.pc_imm_q | 0.146 | 32 | 0.0101 |
| core.dbg_mem_wdata | 0.1454 | 32 | 0.0016 |
