# PicoRV32 timing constraints, sky130_fd_sc_hd, tt corner (25C, 1.80V)
# Single synchronous clock domain.  Same format OpenSTA/OpenROAD consume.

set clk_period 10.0
create_clock -name clk -period $clk_period [get_ports clk]
set_clock_uncertainty 0.25 [get_clocks clk]
set_clock_transition  0.15 [get_clocks clk]

# I/O budget: 20% of the cycle is assumed to be spent outside the core.
set io_delay [expr $clk_period * 0.2]
set non_clk_inputs [lsearch -inline -all -not -exact [all_inputs] [get_ports clk]]
set_input_delay  $io_delay -clock clk $non_clk_inputs
set_output_delay $io_delay -clock clk [all_outputs]

# Drive / load: a sky130 buffer drives each input; each output sees ~4 fanout loads.
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -pin X $non_clk_inputs
set_load 0.0175 [all_outputs]

# resetn is synchronous inside PicoRV32 but comes from an off-chip synchronizer.
set_false_path -from [get_ports resetn]
