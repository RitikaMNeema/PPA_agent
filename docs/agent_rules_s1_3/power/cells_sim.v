// AUTO-GENERATED from liberty by flow/power.py (functional + toggle counters)
`timescale 1ns/1ps
module sky130_fd_sc_hd__a2111oi_0 (A1, A2, B1, C1, D1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  input D1;
  output Y;
  assign Y = (~A1&~B1&~C1&~D1) | (~A2&~B1&~C1&~D1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a211o_1 (A1, A2, B1, C1, X);
  input A1;
  input A2;
  input B1;
  input C1;
  output X;
  assign X = (A1&A2) | (B1) | (C1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a211oi_1 (A1, A2, B1, C1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  output Y;
  assign Y = (~A1&~B1&~C1) | (~A2&~B1&~C1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a21boi_0 (A1, A2, B1_N, Y);
  input A1;
  input A2;
  input B1_N;
  output Y;
  assign Y = (~A1&B1_N) | (~A2&B1_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a21boi_1 (A1, A2, B1_N, Y);
  input A1;
  input A2;
  input B1_N;
  output Y;
  assign Y = (~A1&B1_N) | (~A2&B1_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a21o_1 (A1, A2, B1, X);
  input A1;
  input A2;
  input B1;
  output X;
  assign X = (A1&A2) | (B1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a21oi_1 (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a21oi_2 (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a221o_1 (A1, A2, B1, B2, C1, X);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output X;
  assign X = (B1&B2) | (A1&A2) | (C1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a221oi_1 (A1, A2, B1, B2, C1, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output Y;
  assign Y = (~A1&~B1&~C1) | (~A1&~B2&~C1) | (~A2&~B1&~C1) | (~A2&~B2&~C1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a222oi_1 (A1, A2, B1, B2, C1, C2, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  input C2;
  output Y;
  assign Y = (~A1&~B1&~C1) | (~A1&~B1&~C2) | (~A1&~B2&~C1) | (~A2&~B1&~C1) | (~A1&~B2&~C2) | (~A2&~B1&~C2) | (~A2&~B2&~C1) | (~A2&~B2&~C2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a22o_1 (A1, A2, B1, B2, X);
  input A1;
  input A2;
  input B1;
  input B2;
  output X;
  assign X = (B1&B2) | (A1&A2);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a22oi_1 (A1, A2, B1, B2, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  output Y;
  assign Y = (~A1&~B1) | (~A1&~B2) | (~A2&~B1) | (~A2&~B2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a22oi_2 (A1, A2, B1, B2, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  output Y;
  assign Y = (~A1&~B1) | (~A1&~B2) | (~A2&~B1) | (~A2&~B2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a2bb2oi_1 (A1_N, A2_N, B1, B2, Y);
  input A1_N;
  input A2_N;
  input B1;
  input B2;
  output Y;
  assign Y = (A1_N&~B1) | (A1_N&~B2) | (A2_N&~B1) | (A2_N&~B2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a311o_1 (A1, A2, A3, B1, C1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input C1;
  output X;
  assign X = (A1&A2&A3) | (B1) | (C1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a311oi_1 (A1, A2, A3, B1, C1, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  input C1;
  output Y;
  assign Y = (~A1&~B1&~C1) | (~A2&~B1&~C1) | (~A3&~B1&~C1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a31o_2 (A1, A2, A3, B1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  output X;
  assign X = (A1&A2&A3) | (B1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a31oi_1 (A1, A2, A3, B1, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1) | (~A3&~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a32o_1 (A1, A2, A3, B1, B2, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output X;
  assign X = (A1&A2&A3) | (B1&B2);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__a32oi_1 (A1, A2, A3, B1, B2, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output Y;
  assign Y = (~A1&~B1) | (~A1&~B2) | (~A2&~B1) | (~A3&~B1) | (~A2&~B2) | (~A3&~B2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__a41oi_1 (A1, A2, A3, A4, B1, Y);
  input A1;
  input A2;
  input A3;
  input A4;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1) | (~A3&~B1) | (~A4&~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__and2_0 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A&B);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__and2_1 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A&B);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__and3_1 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (A&B&C);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__and4_1 (A, B, C, D, X);
  input A;
  input B;
  input C;
  input D;
  output X;
  assign X = (A&B&C&D);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__and4b_1 (A_N, B, C, D, X);
  input A_N;
  input B;
  input C;
  input D;
  output X;
  assign X = (~A_N&B&C&D);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__buf_1 (A, X);
  input A;
  output X;
  assign X = (A);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__buf_4 (A, X);
  input A;
  output X;
  assign X = (A);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__buf_6 (A, X);
  input A;
  output X;
  assign X = (A);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__clkbuf_1 (A, X);
  input A;
  output X;
  assign X = (A);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__clkinv_1 (A, Y);
  input A;
  output Y;
  assign Y = (~A);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__conb_1 (HI, LO);
  output HI;
  output LO;
  assign HI = 1'b1;
  assign LO = 1'b0;
  integer t_HI = 0; reg s_HI = 1'b0, c_HI = 1'b0; time l_HI = 0;
  always @(HI) begin if ($time != l_HI) begin if (c_HI !== s_HI && tb_core.pwr_en) t_HI = t_HI + 1; s_HI = c_HI; l_HI = $time; end c_HI = HI; end
  integer t_LO = 0; reg s_LO = 1'b0, c_LO = 1'b0; time l_LO = 0;
  always @(LO) begin if ($time != l_LO) begin if (c_LO !== s_LO && tb_core.pwr_en) t_LO = t_LO + 1; s_LO = c_LO; l_LO = $time; end c_LO = LO; end
  always @(tb_core.dump_activity) begin if (c_HI !== s_HI) t_HI = t_HI + 1; if (c_LO !== s_LO) t_LO = t_LO + 1; $fdisplay(tb_core.act_fd, "%m HI=%0d LO=%0d", t_HI, t_LO); end
endmodule

module sky130_fd_sc_hd__dfxtp_1 (CLK, D, Q);
  input CLK;
  input D;
  output Q;
  reg IQ = 1'b0; wire IQ_N = ~IQ;
  always @(posedge CLK) IQ <= D;
  assign Q = IQ;
  integer t_Q = 0; reg s_Q = 1'b0, c_Q = 1'b0; time l_Q = 0;
  always @(Q) begin if ($time != l_Q) begin if (c_Q !== s_Q && tb_core.pwr_en) t_Q = t_Q + 1; s_Q = c_Q; l_Q = $time; end c_Q = Q; end
  always @(tb_core.dump_activity) begin if (c_Q !== s_Q) t_Q = t_Q + 1; $fdisplay(tb_core.act_fd, "%m Q=%0d", t_Q); end
endmodule

module sky130_fd_sc_hd__edfxtp_1 (CLK, D, DE, Q);
  input CLK;
  input D;
  input DE;
  output Q;
  reg IQ = 1'b0; wire IQ_N = ~IQ;
  always @(posedge CLK) IQ <= (D&DE) | (IQ&~DE);
  assign Q = IQ;
  integer t_Q = 0; reg s_Q = 1'b0, c_Q = 1'b0; time l_Q = 0;
  always @(Q) begin if ($time != l_Q) begin if (c_Q !== s_Q && tb_core.pwr_en) t_Q = t_Q + 1; s_Q = c_Q; l_Q = $time; end c_Q = Q; end
  always @(tb_core.dump_activity) begin if (c_Q !== s_Q) t_Q = t_Q + 1; $fdisplay(tb_core.act_fd, "%m Q=%0d", t_Q); end
endmodule

module sky130_fd_sc_hd__inv_1 (A, Y);
  input A;
  output Y;
  assign Y = (~A);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__maj3_1 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (A&B) | (A&C) | (B&C);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__maj3_2 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (A&B) | (A&C) | (B&C);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__mux2_2 (A0, A1, S, X);
  input A0;
  input A1;
  input S;
  output X;
  assign X = (A0&~S) | (A1&S);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__mux2i_1 (A0, A1, S, Y);
  input A0;
  input A1;
  input S;
  output Y;
  assign Y = (~A0&~S) | (~A1&S);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__mux4_2 (A0, A1, A2, A3, S0, S1, X);
  input A0;
  input A1;
  input A2;
  input A3;
  input S0;
  input S1;
  output X;
  assign X = (A0&~S0&~S1) | (A1&S0&~S1) | (A2&~S0&S1) | (A3&S0&S1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__nand2_1 (A, B, Y);
  input A;
  input B;
  output Y;
  assign Y = (~A) | (~B);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nand2b_1 (A_N, B, Y);
  input A_N;
  input B;
  output Y;
  assign Y = (A_N) | (~B);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nand3_1 (A, B, C, Y);
  input A;
  input B;
  input C;
  output Y;
  assign Y = (~A) | (~B) | (~C);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nand3b_1 (A_N, B, C, Y);
  input A_N;
  input B;
  input C;
  output Y;
  assign Y = (A_N) | (~B) | (~C);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nand4_1 (A, B, C, D, Y);
  input A;
  input B;
  input C;
  input D;
  output Y;
  assign Y = (~A) | (~B) | (~C) | (~D);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nand4b_1 (A_N, B, C, D, Y);
  input A_N;
  input B;
  input C;
  input D;
  output Y;
  assign Y = (A_N) | (~B) | (~C) | (~D);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor2_1 (A, B, Y);
  input A;
  input B;
  output Y;
  assign Y = (~A&~B);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor2b_1 (A, B_N, Y);
  input A;
  input B_N;
  output Y;
  assign Y = (~A&B_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor3_1 (A, B, C, Y);
  input A;
  input B;
  input C;
  output Y;
  assign Y = (~A&~B&~C);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor3b_1 (A, B, C_N, Y);
  input A;
  input B;
  input C_N;
  output Y;
  assign Y = (~A&~B&C_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor4_1 (A, B, C, D, Y);
  input A;
  input B;
  input C;
  input D;
  output Y;
  assign Y = (~A&~B&~C&~D);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor4_2 (A, B, C, D, Y);
  input A;
  input B;
  input C;
  input D;
  output Y;
  assign Y = (~A&~B&~C&~D);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor4b_1 (A, B, C, D_N, Y);
  input A;
  input B;
  input C;
  input D_N;
  output Y;
  assign Y = (~A&~B&~C&D_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__nor4bb_1 (A, B, C_N, D_N, Y);
  input A;
  input B;
  input C_N;
  input D_N;
  output Y;
  assign Y = (~A&~B&C_N&D_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o2111ai_1 (A1, A2, B1, C1, D1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  input D1;
  output Y;
  assign Y = (~A1&~A2) | (~B1) | (~C1) | (~D1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o211a_1 (A1, A2, B1, C1, X);
  input A1;
  input A2;
  input B1;
  input C1;
  output X;
  assign X = (A1&B1&C1) | (A2&B1&C1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o211ai_1 (A1, A2, B1, C1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  output Y;
  assign Y = (~A1&~A2) | (~B1) | (~C1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o21a_1 (A1, A2, B1, X);
  input A1;
  input A2;
  input B1;
  output X;
  assign X = (A1&B1) | (A2&B1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o21ai_0 (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~A2) | (~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o21ai_1 (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~A2) | (~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o21ai_2 (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~A2) | (~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o21bai_1 (A1, A2, B1_N, Y);
  input A1;
  input A2;
  input B1_N;
  output Y;
  assign Y = (~A1&~A2) | (B1_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o221a_2 (A1, A2, B1, B2, C1, X);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output X;
  assign X = (A1&B1&C1) | (A2&B1&C1) | (A1&B2&C1) | (A2&B2&C1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o221ai_1 (A1, A2, B1, B2, C1, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output Y;
  assign Y = (~B1&~B2) | (~A1&~A2) | (~C1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o22a_1 (A1, A2, B1, B2, X);
  input A1;
  input A2;
  input B1;
  input B2;
  output X;
  assign X = (A1&B1) | (A2&B1) | (A1&B2) | (A2&B2);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o22ai_1 (A1, A2, B1, B2, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  output Y;
  assign Y = (~B1&~B2) | (~A1&~A2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o2bb2ai_1 (A1_N, A2_N, B1, B2, Y);
  input A1_N;
  input A2_N;
  input B1;
  input B2;
  output Y;
  assign Y = (~B1&~B2) | (A1_N&A2_N);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o311ai_0 (A1, A2, A3, B1, C1, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  input C1;
  output Y;
  assign Y = (~A1&~A2&~A3) | (~B1) | (~C1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o31a_1 (A1, A2, A3, B1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  output X;
  assign X = (A1&B1) | (A2&B1) | (A3&B1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o31ai_1 (A1, A2, A3, B1, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  output Y;
  assign Y = (~A1&~A2&~A3) | (~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o32a_1 (A1, A2, A3, B1, B2, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output X;
  assign X = (A1&B1) | (A1&B2) | (A2&B1) | (A3&B1) | (A2&B2) | (A3&B2);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o32ai_1 (A1, A2, A3, B1, B2, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output Y;
  assign Y = (~A1&~A2&~A3) | (~B1&~B2);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__o41a_1 (A1, A2, A3, A4, B1, X);
  input A1;
  input A2;
  input A3;
  input A4;
  input B1;
  output X;
  assign X = (A1&B1) | (A2&B1) | (A3&B1) | (A4&B1);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__o41ai_1 (A1, A2, A3, A4, B1, Y);
  input A1;
  input A2;
  input A3;
  input A4;
  input B1;
  output Y;
  assign Y = (~A1&~A2&~A3&~A4) | (~B1);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__or2_1 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A) | (B);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__or2_2 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A) | (B);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__or3_1 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (A) | (B) | (C);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__or3b_1 (A, B, C_N, X);
  input A;
  input B;
  input C_N;
  output X;
  assign X = (A) | (B) | (~C_N);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__or3b_2 (A, B, C_N, X);
  input A;
  input B;
  input C_N;
  output X;
  assign X = (A) | (B) | (~C_N);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__or4_1 (A, B, C, D, X);
  input A;
  input B;
  input C;
  input D;
  output X;
  assign X = (A) | (B) | (C) | (D);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__or4_4 (A, B, C, D, X);
  input A;
  input B;
  input C;
  input D;
  output X;
  assign X = (A) | (B) | (C) | (D);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__xnor2_1 (A, B, Y);
  input A;
  input B;
  output Y;
  assign Y = (~A&~B) | (A&B);
  integer t_Y = 0; reg s_Y = 1'b0, c_Y = 1'b0; time l_Y = 0;
  always @(Y) begin if ($time != l_Y) begin if (c_Y !== s_Y && tb_core.pwr_en) t_Y = t_Y + 1; s_Y = c_Y; l_Y = $time; end c_Y = Y; end
  always @(tb_core.dump_activity) begin if (c_Y !== s_Y) t_Y = t_Y + 1; $fdisplay(tb_core.act_fd, "%m Y=%0d", t_Y); end
endmodule

module sky130_fd_sc_hd__xnor3_1 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (~A&~B&~C) | (A&B&~C) | (A&~B&C) | (~A&B&C);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule

module sky130_fd_sc_hd__xor2_1 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A&~B) | (~A&B);
  integer t_X = 0; reg s_X = 1'b0, c_X = 1'b0; time l_X = 0;
  always @(X) begin if ($time != l_X) begin if (c_X !== s_X && tb_core.pwr_en) t_X = t_X + 1; s_X = c_X; l_X = $time; end c_X = X; end
  always @(tb_core.dump_activity) begin if (c_X !== s_X) t_X = t_X + 1; $fdisplay(tb_core.act_fd, "%m X=%0d", t_X); end
endmodule
