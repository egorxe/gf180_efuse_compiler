/*
 * eFuse array digital wrapper with SPI slave interface in Verilog-2005.
 * Wraps eFuse array with Wishbone interface and WB->SPI converter.
 * 
 */

`timescale 1ns/1ps
`default_nettype none

`ifndef EFUSE_SPIMEM_NAME
`define EFUSE_SPIMEM_NAME efuse_spi_mem_256x8
`define EFUSE_ARRAY_NAME efuse_array_64x8
`endif

`ifndef EFUSE_WBMEM_NAME
`define EFUSE_WBMEM_NAME efuse_wb_mem
`endif

module `EFUSE_SPIMEM_NAME #(
    parameter EFUSE_NWORDS      = 256,
    parameter EFUSE_WORD_WIDTH  = 8,
    parameter WB_ADR_WIDTH      = 8,
    parameter WB_DAT_WIDTH      = 8,
    parameter WB_SEL_WIDTH      = 1,
    parameter SPI_ADR_WIDTH     = 24
) (
    input                       spi_csn,
    input                       spi_clk,
    input                       spi_mosi,
    output                      spi_miso,

    input                       clk_i,
    input                       npor
);

wire rst;
wire write_ena;

wire                      wb_stb;
wire                      wb_cyc;
wire [WB_ADR_WIDTH-1:0]   wb_adr;
wire [WB_DAT_WIDTH-1:0]   wb_dat_wr;
wire                      wb_we;
wire [WB_DAT_WIDTH-1:0]   wb_dat_rd;
wire                      wb_ack;

assign rst = ~npor;

spi2wb #(
    .WB_ADR_WIDTH (WB_ADR_WIDTH),
    .WB_DAT_WIDTH (WB_DAT_WIDTH),
    .SPI_ADR_WIDTH(SPI_ADR_WIDTH)
) spi2wb (
    .clk_i   (clk_i),      
    .rst_i   (rst),      
    .wb_stb_o(wb_stb), 
    .wb_cyc_o(wb_cyc), 
    .wb_adr_o(wb_adr),      
    .wb_dat_o(wb_dat_wr), 
    .wb_we_o (wb_we),
    .wb_dat_i(wb_dat_rd),
    .wb_ack_i(wb_ack),

    .write_ena_o(write_ena),

    .spi_csn (spi_csn),
    .spi_clk (spi_clk),
    .spi_mosi(spi_mosi),
    .spi_miso(spi_miso)
);

`EFUSE_WBMEM_NAME #(
    .EFUSE_NWORDS    (EFUSE_NWORDS),
    .EFUSE_WORD_WIDTH(EFUSE_WORD_WIDTH),
    .WB_ADR_WIDTH    (WB_ADR_WIDTH),
    .WB_DAT_WIDTH    (WB_DAT_WIDTH),
    .WB_SEL_WIDTH    (1)
) efuse_wb_mem (
    .wb_clk_i(clk_i),
    .wb_rst_i(rst), 
    .wb_stb_i(wb_stb), 
    .wb_cyc_i(wb_cyc), 
    .wb_adr_i(wb_adr),
    .wb_dat_i(wb_dat_wr), 
    .wb_sel_i(1'b1), 
    .wb_we_i (wb_we),
    .wb_dat_o(wb_dat_rd),
    .wb_ack_o(wb_ack),
    .write_enable_i(npor & write_ena)
);

endmodule