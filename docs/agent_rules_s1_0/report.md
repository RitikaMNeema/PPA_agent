# PPA report: picorv32 / agent_rules_s1_0

inputs sha `533a873173d515e0` · status **ok** · wall 224.4 s

## Headline

| metric | value |
|---|---|
| Area (cell) | 109,815 um2 (10,193 cells, 2,370 flops) |
| Timing | target 100.0 MHz, WNS -1.389 ns, TNS -10.619 ns, Fmax 87.8 MHz |
| Performance | 622,382 cycles, CPI 6.82, 7,088.6 us @ Fmax |
| Power @ 100.0 MHz | 12.4422 mW (124.42 pJ/cycle, 77.437 uJ per workload) |

## Verification

- lint: OK (58 warnings)
- RTL sim: PASS (622,382 cycles)
- gate-level sim: first_20000_cycles (20,001 cycles, 139.3 s)

## Area

- sequential 65,893 um2 (60%), combinational 43,922 um2
- top cell families: edfxtp x1843, nor2 x1086, o21ai x1002, nand2 x965, a21oi x940, dfxtp x527, clkbuf x387, xnor2 x282

## Timing (setup, ideal clock, wire-load model)

| endpoint group | WNS ns | failing/total |
|---|---|---|
| core.reg_out | -1.389 | 4/32 |
| core.reg_next_pc | -1.361 | 7/32 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | -1.19 | 5/64 |
| core.alu_out_q | -0.026 | 1/32 |
| core.genblk2.pcpi_div.dividend | 0.633 | 0/64 |
| core.dbg_mem_addr | 0.64 | 0/90 |
| core.is_beq_bne_blt_bge_bltu_bgeu | 1.762 | 0/1 |
| core.decoder_trigger | 2.099 | 0/1 |

Critical path: `core.reg_pc[1]` -> `core.reg_out[31] (dfxtp_1/D)`, slack -1.389 ns, logic depth 33

```
  0.519  +0.519  dfxtp_1      core.reg_pc[1]
  0.778  +0.259  xnor2_4      _7191_
  0.967  +0.189  o21ai_2      _7193_
  1.327  +0.361  maj3_2       _7194_
  1.660  +0.333  maj3_2       _7195_
  1.995  +0.335  maj3_2       _7196_
  2.315  +0.321  maj3_2       _7197_
  2.643  +0.328  maj3_2       _7198_
  2.974  +0.331  maj3_2       _7199_
  3.304  +0.331  maj3_2       _7200_
  3.635  +0.331  maj3_2       _7201_
  3.966  +0.331  maj3_2       _7202_
  4.296  +0.331  maj3_2       _7203_
  4.627  +0.331  maj3_2       _7204_
  4.958  +0.331  maj3_2       _7205_
  5.288  +0.331  maj3_2       _7206_
  5.619  +0.331  maj3_2       _7207_
  5.950  +0.331  maj3_2       _7208_
  6.280  +0.331  maj3_2       _7209_
  6.611  +0.331  maj3_2       _7210_
  6.942  +0.331  maj3_2       _7211_
  7.272  +0.331  maj3_2       _7212_
  7.603  +0.331  maj3_2       _7213_
  7.934  +0.331  maj3_2       _7214_
  8.264  +0.331  maj3_2       _7215_
  8.595  +0.331  maj3_2       _7216_
  8.926  +0.331  maj3_2       _7217_
  9.256  +0.331  maj3_2       _7218_
  9.587  +0.331  maj3_2       _7219_
  9.918  +0.331  maj3_2       _7220_
 10.256  +0.338  maj3_2       _7221_
 10.518  +0.262  a221oi_1     _409_
 10.818  +0.300  a311oi_1     _410_
 11.047  +0.229  o22a_1       _6889_
```

## Power (20,001-cycle window, 100.0 MHz, tt 1.8V)

| component | mW | share |
|---|---|---|
| clock | 11.9066 | 95.7% |
| sequential | 0.1024 | 0.8% |
| combinational | 0.4332 | 3.5% |
| leakage | 0.0000 | 0.0% |
| (leakage in uW) | 0.038 uW | |

avg net toggle rate 0.0249 per cycle; clock pin cap 4.467 pF

| register | mW | flops | toggle rate |
|---|---|---|---|
| core.cpuregs | 5.2269 | 1152 | 0.0002 |
| core.genblk1.genblk1.pcpi_mul.rd | 0.2904 | 64 | 0.0 |
| core.genblk1.genblk1.pcpi_mul.next_rs2 | 0.2896 | 63 | 0.018 |
| core.genblk1.genblk1.pcpi_mul.next_rs1 | 0.2868 | 63 | 0.0061 |
| core.genblk2.pcpi_div.divisor | 0.2858 | 63 | 0.0 |
| core.count_cycle | 0.2624 | 64 | 0.0312 |
| core.count_instr | 0.2556 | 64 | 0.0034 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs2 | 0.1516 | 32 | 0.0354 |
| core.decoded_imm | 0.15 | 32 | 0.0303 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rs1 | 0.1485 | 32 | 0.0127 |
| core.dbg_mem_wdata | 0.1454 | 32 | 0.0016 |
| core.genblk1.genblk1.pcpi_mul.pcpi_rd | 0.1452 | 32 | 0.0 |
