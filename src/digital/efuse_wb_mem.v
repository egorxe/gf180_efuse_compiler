/*
 * eFuse array digital wrapper with Wishbone slave interface in Verilog-2005.
 * Write mask is ignored unless (WB_SEL_WIDTH * 8) == WB_DAT_WIDTH.
 *
 * Wishbone address is per efuse word.
 * 
 */

`timescale 1ns/1ps
`default_nettype none

`ifndef EFUSE_WBMEM_NAME
`define EFUSE_WBMEM_NAME efuse_wb_mem
`endif

`ifndef EFUSE_ARRAY_NAME
`define EFUSE_ARRAY_NAME efuse_array
`endif

module `EFUSE_WBMEM_NAME #(
    parameter EFUSE_NWORDS      = 64,
    parameter EFUSE_WORD_WIDTH  = 8,
    parameter WB_ADR_WIDTH      = 6,
    parameter WB_DAT_WIDTH      = 8,
    parameter WB_SEL_WIDTH      = (WB_DAT_WIDTH / 8)
) (
    input                       wb_clk_i,
    input                       wb_rst_i, 
    input                       wb_stb_i, 
    input                       wb_cyc_i, 
    input  [WB_ADR_WIDTH-1:0]   wb_adr_i,       // Address is per efuse word
    input  [WB_DAT_WIDTH-1:0]   wb_dat_i, 
    input  [WB_SEL_WIDTH-1:0]   wb_sel_i, 
    input                       wb_we_i,
    output [WB_DAT_WIDTH-1:0]   wb_dat_o,
    output                      wb_ack_o,

    input                       write_enable_i  // Active-high write-enable signal. Recommended to be connected to active-low POR reset
);

    // number of eFuse array macros connected in "parallel" to form Wishbone word (!should be 1 for now!)
    localparam EFUSE_ARRAYS_WDT = WB_DAT_WIDTH / EFUSE_WORD_WIDTH; 
    // number of eFuse array macros connected with mux to get requested memory depth 
    localparam EFUSE_ARRAYS_DPT = (2**WB_ADR_WIDTH) / EFUSE_NWORDS;

    localparam EFUSE_DAT_BITS   = EFUSE_WORD_WIDTH*EFUSE_ARRAYS_DPT;

    localparam EFUSE_ADR_WDT    = $clog2(EFUSE_NWORDS);
    localparam EFUSE_SEL_WDT    = (WB_ADR_WIDTH-EFUSE_ADR_WDT)!=0 ? WB_ADR_WIDTH-EFUSE_ADR_WDT : 1;

    localparam USE_MASK         = (WB_SEL_WIDTH * 8) == WB_DAT_WIDTH;

    localparam COUNTER_WIDTH    = 10; // width of write time counter

    reg [WB_DAT_WIDTH-1:0] dat_o;
    reg ack_o;
    reg [1:0] state;
    reg [COUNTER_WIDTH-1:0] counter;

    wire [EFUSE_NWORDS-1:0] bit_sel;
    wire [EFUSE_DAT_BITS-1:0] col_prog_n;
    wire [EFUSE_ARRAYS_DPT-1:0] preset_n;
    wire [EFUSE_ARRAYS_DPT-1:0] sense;
    wire [EFUSE_ARRAYS_DPT-1:0] sense_del;
    wire [EFUSE_DAT_BITS-1:0] efuse_out;
    wire [EFUSE_SEL_WDT-1:0] sel;   // efuse array selector

    reg [EFUSE_NWORDS-1:0] bit_sel_reg;
    reg [EFUSE_DAT_BITS-1:0] col_prog_n_reg;
    reg [EFUSE_ARRAYS_DPT-1:0] preset_n_reg;
    reg [EFUSE_ARRAYS_DPT-1:0] sense_reg;

    wire one;

    assign wb_ack_o = ack_o;
    assign wb_dat_o = dat_o;

    // Generate efuse arrays
    genvar i;
    generate
        for (i = 0; i < EFUSE_ARRAYS_DPT; i = i + 1) begin : efuse_gen_depth
            `EFUSE_ARRAY_NAME 
            `ifdef SIM
            #(
                .NWORDS(EFUSE_NWORDS),
                .WORD_WIDTH(EFUSE_WORD_WIDTH)
            )
            `endif
            efuse_array (
                .BIT_SEL    (bit_sel),
                .COL_PROG_N (col_prog_n[EFUSE_WORD_WIDTH*(i+1)-1:EFUSE_WORD_WIDTH*i]),
                .PRESET_N   (preset_n[i]),
                .SENSE      (sense[i]),
                .OUT        (efuse_out[EFUSE_WORD_WIDTH*(i+1)-1:EFUSE_WORD_WIDTH*i])
            );
        end
    endgenerate

    localparam WRITE_CNT        = 1000;

    localparam STATE_IDLE       = 0;
    localparam STATE_PRESET     = 1;
    localparam STATE_READ       = 2;
    localparam STATE_WRITE      = 3;

    // Manually instantiate buffers
    (* keep, dont_touch  *)
    gf180mcu_fd_sc_mcu7t5v0__tieh tie_keep_cell (
        .Z(one)
    );

    generate
        for (i = 0; i < EFUSE_DAT_BITS; i = i + 1) begin
            // ensure write signals are held in 1 state during write disable, for example on power up
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__mux2_4 prog_disable_keep_cell (
                .I0(one),
                .I1(col_prog_n_reg[i]),
                .S(write_enable_i),
                .Z(col_prog_n[i])
            );
        end

        for (i = 0; i < EFUSE_NWORDS; i = i + 1) begin
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__buf_2 bitsel_buf_keep_cell (
                .I(bit_sel_reg[i]),
                .Z(bit_sel[i])
            );
        end

        for (i = 0; i < EFUSE_ARRAYS_DPT; i = i + 1) begin
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__dlyc_2 sense_dly_keep_cell (
                .I(sense_reg[i]),
                .Z(sense_del[i])
            );
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__buf_8 sense_buf_keep_cell (
                .I(sense_del[i]),
                .Z(sense[i])
            );
            (* keep, dont_touch  *)
            gf180mcu_fd_sc_mcu7t5v0__buf_8 preset_buf_keep_cell (
                .I(preset_n_reg[i]),
                .Z(preset_n[i])
            );
        end
    endgenerate

    assign sel = (WB_ADR_WIDTH-EFUSE_ADR_WDT)!=0 ? wb_adr_i[EFUSE_SEL_WDT+EFUSE_ADR_WDT-1:EFUSE_ADR_WDT] : 1'b0;

    always @(posedge wb_clk_i or posedge wb_rst_i) begin
        if (wb_rst_i) begin
            ack_o   <= 1'b0;
            dat_o   <= {WB_DAT_WIDTH{1'b0}};
            counter <= {COUNTER_WIDTH{1'b0}};
            state   <= STATE_IDLE;

            preset_n_reg    <= {EFUSE_ARRAYS_DPT{1'b1}};
            sense_reg       <= {EFUSE_ARRAYS_DPT{1'b0}};
            col_prog_n_reg  <= {EFUSE_DAT_BITS{1'b1}};
            bit_sel_reg     <= {EFUSE_NWORDS{1'b0}};
        end else begin
            case(state)
                STATE_IDLE: begin
                    ack_o       <= 1'b0;
                    bit_sel_reg <= {EFUSE_NWORDS{1'b0}};

                    if (wb_stb_i & wb_cyc_i & ~ack_o) begin
                        if (wb_we_i) begin
                            state           <= STATE_WRITE;
                            bit_sel_reg     <= 2**(wb_adr_i[EFUSE_ADR_WDT-1:0]);
                            counter         <= WRITE_CNT;
                        end else begin
                            state           <= STATE_PRESET;
                            preset_n_reg[sel]<= 1'b0;
                            sense_reg[sel]  <= 1'b1;
                        end
                    end
                end

                STATE_PRESET : begin
                    preset_n_reg    <= {EFUSE_ARRAYS_DPT{1'b1}};
                    bit_sel_reg     <= 2**(wb_adr_i[EFUSE_ADR_WDT-1:0]);
                    state           <= STATE_READ;
                end

                STATE_READ : begin
                    sense_reg   <= {EFUSE_ARRAYS_DPT{1'b0}};
                    state       <= STATE_IDLE;
                    ack_o       <= 1'b1;
                    dat_o       <= efuse_out[WB_DAT_WIDTH*sel +: WB_DAT_WIDTH];
                end

                STATE_WRITE : begin
                    if (counter === 0) begin
                        state           <= STATE_IDLE;
                        col_prog_n_reg  <= {EFUSE_DAT_BITS{1'b1}};
                        ack_o           <= 1'b1;
                    end else begin
                        if (!USE_MASK) begin
                            col_prog_n_reg[WB_DAT_WIDTH*sel +: WB_DAT_WIDTH]  <= ~wb_dat_i;
                        end else begin
                            integer m;
                            for (m = 0; m < WB_SEL_WIDTH; m = m + 1)
                                col_prog_n_reg[WB_DAT_WIDTH*sel + m*8 +: 8]  <= ~(wb_dat_i[m*8 +: 8] & {8{wb_sel_i[m]}});
                        end
                        counter <= counter - 1;
                    end
                end

            endcase
        end 
    end
  
endmodule
