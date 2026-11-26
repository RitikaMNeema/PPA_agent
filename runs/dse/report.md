# Design-space exploration (2026-11-25 22:46:23)

26 of 128 configurations evaluated on **spark** (6 workers): wall 1054 s for 5197 s of flow time (x4.9 parallel speed-up). Power window 20,000 cycles. Weights {'runtime': 0.4, 'power': 0.4, 'area': 0.2}.

## Best configuration

`dse_0110000` cost **0.9855** (reference = 1.0): runtime -4.4%, power -0.2%, area +1.8%

| knob | value |
|---|---|
| TWO_STAGE_SHIFT | 0 |
| BARREL_SHIFTER | 1 |
| TWO_CYCLE_COMPARE | 1 |
| TWO_CYCLE_ALU | 0 |
| ENABLE_REGS_DUALPORT | 0 |
| ENABLE_FAST_MUL | 0 |
| abc_script | speed |

## Surrogate model quality (leave-one-out)

| metric | MAPE | R² |
|---|---|---|
| runtime | 4.68% | 0.844 |
| power | 0.25% | 0.975 |
| area | 0.4% | 0.997 |

## Knob relevance (GP 1/length-scale, normalised)

| knob | runtime | power | area |
|---|---|---|---|
| TWO_STAGE_SHIFT | 0.21 | 0.01 | 0.00 |
| BARREL_SHIFTER | 0.15 | 0.23 | 0.01 |
| TWO_CYCLE_COMPARE | 0.02 | 0.03 | 0.00 |
| TWO_CYCLE_ALU | 0.10 | 0.34 | 0.00 |
| ENABLE_REGS_DUALPORT | 0.10 | 0.02 | 0.01 |
| ENABLE_FAST_MUL | 0.22 | 0.31 | 0.98 |
| abc_script | 0.19 | 0.07 | 0.00 |

## Bayesian-optimisation rounds

| round | train | picked | predicted cost | actual cost |
|---|---|---|---|---|
| 1 | 11 | dse_0000000 | 1.0049 | 1.0879 |
| 1 | 11 | dse_1000001 | 1.0755 | 1.0505 |
| 1 | 11 | dse_1010000 | 1.0106 | 1.005 |
| 1 | 11 | dse_1100000 | 1.0214 | 0.9968 |
| 1 | 11 | dse_1101000 | 1.0949 | 1.0802 |
| 2 | 16 | dse_0110010 | 1.1630 | 1.1644 |
| 2 | 16 | dse_1110000 | 1.0186 | 1.0126 |
| 2 | 16 | dse_0000001 | 1.0825 | 1.1249 |
| 2 | 16 | dse_0001000 | 1.1035 | 1.1106 |
| 2 | 16 | dse_1010001 | 1.0577 | 1.0654 |
| 3 | 21 | dse_0110000 | 1.0365 | 0.9855 |
| 3 | 21 | dse_0000010 | 1.2289 | 1.2555 |
| 3 | 21 | dse_0000011 | 1.2811 | 1.4844 |
| 3 | 21 | dse_0000100 | 1.1132 | 1.1348 |
| 3 | 21 | dse_0000101 | 1.1495 | 1.1 |

## All evaluated (Pareto-optimal marked ★)

| tag | src | runtime us | power mW | area um² | cost | host |
|---|---|---|---|---|---|---|
| dse_0110000 ★ | bo | 6756 | 12.372 | 111,158 | 0.9855 | SDxbattle |
| dse_1100000 ★ | bo | 6986 | 12.335 | 110,888 | 0.9968 | SDxbattle |
| dse_1000000 ★ | init | 7064 | 12.392 | 109,186 | 1.0 | SDxbattle |
| dse_1010000 | bo | 7097 | 12.440 | 110,068 | 1.005 | SDxbattle |
| dse_1110000 | bo | 7206 | 12.408 | 111,381 | 1.0126 | SDxbattle |
| dse_1100100 | init | 7432 | 12.343 | 119,044 | 1.0373 | SDxbattle |
| dse_1000001 | bo | 7731 | 12.507 | 114,154 | 1.0505 | SDxbattle |
| dse_0110100 | init | 7813 | 12.352 | 119,069 | 1.0592 | SDxbattle |
| dse_1110100 | init | 7802 | 12.366 | 119,259 | 1.0594 | SDxbattle |
| dse_1010001 | bo | 7950 | 12.535 | 115,018 | 1.0654 | SDxbattle |
| dse_1101000 | bo | 8098 | 12.836 | 113,180 | 1.0802 | SDxbattle |
| dse_0000000 ★ | bo | 8597 | 12.430 | 109,155 | 1.0879 | SDxbattle |
| dse_0000101 | bo | 8371 | 12.440 | 122,576 | 1.1 | SDxbattle |
| dse_0001000 | bo | 8892 | 12.560 | 110,083 | 1.1106 | SDxbattle |
| dse_1001100 | init | 8810 | 12.527 | 118,378 | 1.12 | SDxbattle |
| dse_0000001 | bo | 9032 | 12.534 | 114,013 | 1.1249 | SDxbattle |
| dse_0000100 | bo | 9183 | 12.386 | 117,383 | 1.1348 | SDxbattle |
| dse_0110010 ★ | bo | 9275 | 11.696 | 142,882 | 1.1644 | SDxbattle |
| dse_0011101 | init | 9676 | 12.573 | 123,385 | 1.1797 | SDxbattle |
| dse_0101110 | init | 9763 | 12.124 | 153,233 | 1.2248 | SDxbattle |
| dse_1101010 | init | 10380 | 12.168 | 144,824 | 1.2458 | SDxbattle |
| dse_0000010 ★ | bo | 10849 | 11.789 | 142,305 | 1.2555 | SDxbattle |
| dse_1011010 ★ | init | 10882 | 11.858 | 141,240 | 1.2576 | SDxbattle |
| dse_0001110 | init | 11182 | 11.855 | 149,436 | 1.2895 | SDxbattle |
| dse_1111011 | init | 13290 | 12.242 | 150,711 | 1.4237 | SDxbattle |
| dse_0000011 | bo | 14607 | 11.920 | 148,832 | 1.4844 | SDxbattle |
