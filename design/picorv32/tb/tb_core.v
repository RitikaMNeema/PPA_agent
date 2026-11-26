// Native-memory-interface testbench for picorv32_top.
// Works for both RTL and the synthesized gate-level netlist (same ports), so
// one golden workload drives verification AND activity-based power estimation.
//
// Workload: upstream PicoRV32 firmware = riscv-tests ISA suite (rv32imc) +
// sieve + multiply self-test + timer/IRQ test.  Pass = firmware writes
// 123456789 to 0x2000_0000 then traps.
`timescale 1 ns / 1 ps

module tb_core;
	reg clk = 1;
	reg resetn = 0;
	always #5 clk = ~clk;

	// power-measurement window enable (read hierarchically by gate models)
	reg pwr_en = 0;
	integer act_fd;
`ifdef GLS
	initial act_fd = $fopen("activity.txt", "w");
`endif

	integer max_cycles, pwr_cycles;
	initial begin
		if (!$value$plusargs("max_cycles=%d", max_cycles)) max_cycles = 2000000;
		if (!$value$plusargs("pwr_cycles=%d", pwr_cycles)) pwr_cycles = 0;
		repeat (100) @(posedge clk);
		resetn <= 1;
		pwr_en <= 1;
	end

	// ---------------- DUT ----------------
	wire        trap, mem_valid, mem_instr;
	reg         mem_ready = 0;
	wire [31:0] mem_addr, mem_wdata;
	wire [ 3:0] mem_wstrb;
	reg  [31:0] mem_rdata = 0;
	wire [31:0] eoi;
	reg  [31:0] irq = 0;

	reg [15:0] count_cycle = 0;
	always @(posedge clk) count_cycle <= resetn ? count_cycle + 1 : 0;
	always @* begin
		irq = 0;
		irq[4] = &count_cycle[12:0];
		irq[5] = &count_cycle[15:0];
	end

	picorv32_top dut (
		.clk(clk), .resetn(resetn), .trap(trap),
		.mem_valid(mem_valid), .mem_instr(mem_instr), .mem_ready(mem_ready),
		.mem_addr(mem_addr), .mem_wdata(mem_wdata), .mem_wstrb(mem_wstrb),
		.mem_rdata(mem_rdata), .irq(irq), .eoi(eoi)
	);

	// ---------------- memory: 128 KB, 1 wait state ----------------
	reg [31:0] memory [0:32767];
	reg [1023:0] firmware_file;
	initial begin
		if (!$value$plusargs("firmware=%s", firmware_file))
			firmware_file = "firmware.hex";
		$readmemh(firmware_file, memory);
	end

	reg tests_passed = 0;
	integer n_instr = 0, n_mem = 0;
	always @(posedge clk) begin
		mem_ready <= 0;
		if (resetn && mem_valid && !mem_ready) begin
			mem_ready <= 1;
			n_mem = n_mem + 1;
			if (mem_instr) n_instr = n_instr + 1;
			if (mem_addr < 32'h0002_0000) begin
				mem_rdata <= memory[mem_addr >> 2];
				if (mem_wstrb[0]) memory[mem_addr >> 2][ 7: 0] <= mem_wdata[ 7: 0];
				if (mem_wstrb[1]) memory[mem_addr >> 2][15: 8] <= mem_wdata[15: 8];
				if (mem_wstrb[2]) memory[mem_addr >> 2][23:16] <= mem_wdata[23:16];
				if (mem_wstrb[3]) memory[mem_addr >> 2][31:24] <= mem_wdata[31:24];
			end else if (mem_addr == 32'h1000_0000 && |mem_wstrb) begin
				$write("%c", mem_wdata[7:0]);
				$fflush;
			end else if (mem_addr == 32'h2000_0000 && |mem_wstrb) begin
				if (mem_wdata == 123456789) tests_passed = 1;
			end else begin
				$display("\nOUT-OF-BOUNDS ACCESS addr=%08x wstrb=%b", mem_addr, mem_wstrb);
				$display("RESULT: FAIL oob");
				$finish;
			end
		end
	end

	// ---------------- end of test ----------------
	integer cycle = 0;
	event dump_activity;          // gate models print their toggle counters on this
	always @(posedge clk) begin
		if (resetn) cycle <= cycle + 1;
		if (resetn && trap) begin
			pwr_en <= 0;
			repeat (2) @(posedge clk);
			$display("\nCYCLES=%0d INSTR_FETCHES=%0d MEM_XFERS=%0d", cycle, n_instr, n_mem);
			-> dump_activity;
			#1;
			if (tests_passed) $display("RESULT: PASS");
			else              $display("RESULT: FAIL trap_without_pass");
			$finish;
		end
		if (pwr_cycles > 0 && cycle == pwr_cycles) begin   // fast power-window mode
			pwr_en <= 0;
			@(posedge clk);
			$display("\nCYCLES=%0d INSTR_FETCHES=%0d MEM_XFERS=%0d", cycle, n_instr, n_mem);
			-> dump_activity;
			#1;
			$display("RESULT: WINDOW");
			$finish;
		end
		if (cycle >= max_cycles) begin
			$display("\nCYCLES=%0d", cycle);
			$display("RESULT: FAIL timeout");
			$finish;
		end
	end
endmodule
