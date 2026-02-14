/*
 * SPI slave to Wishbone master with EEPROM-like protocol.
 * Intended to be used as WB->SPI adapter for eFuse wrapper.
 */

`timescale 1ns/1ps
`default_nettype none

module spi2wb #(
    parameter WB_ADR_WIDTH      = 4,
    parameter WB_DAT_WIDTH      = 8,    // only 8 is supported
    parameter SPI_ADR_WIDTH     = 24
) (
    input                       clk_i,          // Will be treated as Wishbone clock
    input                       rst_i,          // Active-high reset
    output                      wb_stb_o, 
    output                      wb_cyc_o, 
    output [WB_ADR_WIDTH-1:0]   wb_adr_o,       // Address is per efuse word
    output [WB_DAT_WIDTH-1:0]   wb_dat_o, 
    output                      wb_we_o,
    input  [WB_DAT_WIDTH-1:0]   wb_dat_i,
    input                       wb_ack_i,

    output                      write_ena_o,

    input                       spi_csn,
    input                       spi_clk,
    input                       spi_mosi,
    output                      spi_miso
);

    localparam SPI_CMD_WIDTH    = 8;    
    localparam SPI_DAT_WIDTH    = 8;    // should be equal to WB_DAT_WIDTH
    localparam SPI_STAT_WIDTH   = 8;    

    reg wb_stb_reg;
    reg wb_we_reg;
    reg [WB_ADR_WIDTH-1:0] wb_adr_reg;
    reg [WB_DAT_WIDTH-1:0] wb_datwr_reg;
    reg [WB_DAT_WIDTH-1:0] wb_datrd_reg;
    
    reg [SPI_ADR_WIDTH-1:0] spi_adr_reg;
    reg [SPI_CMD_WIDTH-1:0] spi_cmd_reg;
    reg [SPI_DAT_WIDTH-1:0] spi_dat_reg;
    reg spi_miso_reg;
    reg spi_clk_reg;
    reg spi_csn_reg;
    reg wr_req;
    reg rd_req;

    reg [2:0] spi_state;
    reg [4:0] spi_counter;
    reg wren_reg;
    wire [SPI_STAT_WIDTH-1:0] spi_status;

    wire spi_clk_fall;
    wire spi_clk_rise;

    assign wb_stb_o = wb_stb_reg;
    assign wb_cyc_o = wb_stb_reg;
    assign wb_we_o  = wb_we_reg;
    assign wb_adr_o = wb_adr_reg;
    assign wb_dat_o = wb_datwr_reg;
    assign spi_miso = spi_miso_reg;
    assign write_ena_o = wren_reg;

    assign spi_clk_fall = ~spi_clk & spi_clk_reg;
    assign spi_clk_rise = ~spi_clk_reg & spi_clk;
    assign spi_status = {6'b0, wren_reg, wb_stb_reg};

    localparam [SPI_CMD_WIDTH-1:0]  SPI_CMD_WRITE  = 8'h02;
    localparam [SPI_CMD_WIDTH-1:0]  SPI_CMD_READ   = 8'h03;
    localparam [SPI_CMD_WIDTH-1:0]  SPI_CMD_WRDI   = 8'h04;
    localparam [SPI_CMD_WIDTH-1:0]  SPI_CMD_RSTAT  = 8'h05;
    localparam [SPI_CMD_WIDTH-1:0]  SPI_CMD_WREN   = 8'h06;

    localparam STATE_SPI_IDLE   = 0;
    localparam STATE_SPI_CMD    = 1;
    localparam STATE_SPI_ADDR   = 2;
    localparam STATE_SPI_WRITE  = 3;
    localparam STATE_SPI_READ   = 4;
    localparam STATE_SPI_READST = 5;

    always @(posedge clk_i or posedge rst_i) begin
        if (rst_i) begin
            wb_stb_reg      <= 1'b0;
            wb_we_reg       <= 1'b0;
            wb_datwr_reg    <= {WB_DAT_WIDTH{1'b0}};
            wb_adr_reg      <= {WB_ADR_WIDTH{1'b0}};

            spi_miso_reg    <= 1'b0;
            wr_req          <= 1'b0;
            rd_req          <= 1'b0;

            wren_reg        <= 1'b0;
            spi_state       <= STATE_SPI_IDLE;
        end else begin

            spi_csn_reg <= spi_csn;
            spi_clk_reg <= spi_clk;

            wr_req <= 1'b0;
            rd_req <= 1'b0;

            if (spi_csn == 1'b1)
                spi_state <= STATE_SPI_IDLE;

            // SPI FSM
            case (spi_state)
                STATE_SPI_IDLE: begin
                    spi_miso_reg    <= 1'b0;
                    spi_counter     <= SPI_CMD_WIDTH-1;

                    if (spi_csn == 1'b0)
                        spi_state <= STATE_SPI_CMD;
                end

                STATE_SPI_CMD: begin
                    if (spi_clk_rise) begin
                        spi_cmd_reg[spi_counter] <= spi_mosi;
                        if (spi_counter == 0) begin
                            case ({spi_cmd_reg[SPI_CMD_WIDTH-1:1], spi_mosi})
                                // read or write data command
                                SPI_CMD_READ, SPI_CMD_WRITE: begin
                                    spi_state   <= STATE_SPI_ADDR;
                                    spi_counter <= SPI_ADR_WIDTH-1;
                                end 

                                // read status command
                                SPI_CMD_RSTAT: begin
                                    spi_state <= STATE_SPI_READST;
                                    spi_counter <= SPI_STAT_WIDTH-1;
                                end

                                // write enable command
                                SPI_CMD_WREN: begin
                                    spi_state <= STATE_SPI_IDLE;
                                    wren_reg <= 1'b1;
                                end

                                // write disable command
                                SPI_CMD_WRDI: begin
                                    spi_state <= STATE_SPI_IDLE;
                                    wren_reg <= 1'b0;
                                end

                                // ignore everything else
                                default:
                                    spi_state <= STATE_SPI_IDLE;
                            endcase
                        end else
                            spi_counter <= spi_counter - 1;
                    end
                end

                STATE_SPI_ADDR: begin
                    if (spi_clk_rise) begin
                        spi_adr_reg[spi_counter] <= spi_mosi;
                        if (spi_counter == 0) begin
                            spi_counter <= SPI_DAT_WIDTH-1;
                            if (spi_cmd_reg == SPI_CMD_WRITE) begin
                                spi_state <= STATE_SPI_WRITE;
                            end else begin
                                spi_state <= STATE_SPI_READ;
                                rd_req <= ~wb_stb_reg; // request only if wb is free
                            end
                        end else
                            spi_counter <= spi_counter - 1;
                    end
                end
                
                STATE_SPI_WRITE: begin
                    if (spi_clk_rise) begin
                        spi_dat_reg[spi_counter] <= spi_mosi;
                        if (spi_counter == 0) begin
                            // only single byte writes are supported
                            spi_state <= STATE_SPI_IDLE;
                            wr_req <= ~wb_stb_reg; // request only if wb is free
                        end else
                            spi_counter <= spi_counter - 1;
                    end
                end 

                STATE_SPI_READ: begin
                    if (spi_clk_fall) begin
                        spi_miso_reg <= wb_datrd_reg[spi_counter];
                        if (spi_counter == 0) begin
                            // start reading the next address
                            spi_counter <= SPI_DAT_WIDTH-1;
                            spi_adr_reg <= spi_adr_reg + 1;
                            rd_req <= 1'b1;
                        end else
                            spi_counter <= spi_counter - 1;
                    end
                end

                STATE_SPI_READST: begin
                    if (spi_clk_fall) begin
                        spi_miso_reg <= spi_status[spi_counter];
                        if (spi_counter == 0) begin
                            // start reading again
                            spi_counter <= SPI_DAT_WIDTH-1;
                        end else
                            spi_counter <= spi_counter - 1;
                    end
                end
            endcase

            // Wishbone requests
            if (wb_stb_reg == 0) begin
                if (wr_req | rd_req) begin
                    wb_datwr_reg    <= spi_dat_reg; // needed only on write, but does not hurt
                    wb_adr_reg      <= spi_adr_reg[WB_ADR_WIDTH-1:0];
                    wb_we_reg       <= wr_req;
                    wb_stb_reg      <= 1'b1;
                end
            end else begin
                if (wb_ack_i) begin
                    wb_datrd_reg    <= wb_dat_i;    // needed only on read, but does not hurt
                    wb_stb_reg      <= 1'b0;
                    wb_we_reg       <= 1'b0;
                end
            end

        end
    end

endmodule