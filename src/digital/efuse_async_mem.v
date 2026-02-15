/*
 * 1-byte async eFuse memory block, wraps efuse_array_async & performs read-after-reset
 * 
 */

 `timescale 1ns/1ps
 `default_nettype none


module efuse_async_mem_1x8 #(
    parameter   WDT = 8
) (
    input               reset_n,
    input  [WDT-1:0]    prog, 
    output [WDT-1:0]    out, 
    output              ready 
);

    wire            reset;
    wire [1:0]      reset_n_del;
    wire [2:0]      reset_del;
    wire            sense_predel;
    wire            sense;
    wire            preset_n;
    wire [WDT-1:0]  col_prog_n;
    wire [WDT-1:0]  out_prebuf;

    // Reset inverter
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__inv_2 inv_res_cell (
        .I(reset_n),
        .ZN(reset)
    );

    // Preset form chain
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__dlyd_4 del_resn0_cell (
        .I(reset_n),
        .Z(reset_n_del[0])
    );    
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__dlyd_4 del_resn1_cell (
        .I(reset_n_del[0]),
        .Z(reset_n_del[1])
    );    
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__or2_2 or_preset_cell (
        .A1(reset),
        .A2(reset_n_del[1]),
        .Z(preset_n)
    );

    // Sense form chain
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__inv_2 inv_resnd_cell (
        .I(reset_n_del[1]),
        .ZN(reset_del[0])
    );    
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__dlyd_4 del_res0_cell (
        .I(reset_del[0]),
        .Z(reset_del[1])
    );     
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__dlyd_4 del_res1_cell (
        .I(reset_del[1]),
        .Z(reset_del[2])
    );    
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__and2_2 and_sense_cell (
        .A1(reset_n_del[1]),
        .A2(reset_del[2]),
        .Z(sense_predel)
    );
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__dlyd_4 del_sense_cell (
        .I(sense_predel),
        .Z(sense)
    );

    assign ready = ~reset_del[2] & ~sense;

    // Program inhibit & buffer output
    genvar i;
    generate 
        for (i = 0; i < WDT; i = i + 1) begin
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__nand2_2 nand_wrinhibit_cell (
                .A1(reset_n),
                .A2(prog[i]),
                .ZN(col_prog_n[i])
            );
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__buf_4 out_buf_cell (
                .I(out_prebuf[i]),
                .Z(out[i])
            );
        end
    endgenerate

    // Async eFuse array
    efuse_array_async_1x8 efuse_array (
        .COL_PROG_N(col_prog_n),
        .OUT(out_prebuf),
        .SENSE(sense),
        .PRESET_N(preset_n)
    );
  
endmodule
