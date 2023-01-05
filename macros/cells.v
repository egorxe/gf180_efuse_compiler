module gf180mcu_fd_sc_mcu7t5v0__clkinv_4( I, ZN);
input I;
output ZN;
endmodule


module gf180mcu_fd_sc_mcu7t5v0__clkbuf_4( I, Z );
input I;
output Z;
endmodule

module tech_inv( I, ZN);
input I;
output ZN;

gf180mcu_fd_sc_mcu7t5v0__clkinv_4 inv(I, ZN);

endmodule

module tech_buf( I, Z);
input I;
output Z;

gf180mcu_fd_sc_mcu7t5v0__clkbuf_4 inv(I, Z);

endmodule
