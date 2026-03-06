//! @title eFuse memory block with Wishbone interface
//!
//!  This is a digital wrapper around efuse_array providing a synchronous interface to the eFuse memory with Wishbone bus. Interface should be compatible with the [classic Wishbone SoC bus standard](https://wishbone-interconnect.readthedocs.io/en/latest/03_classic.html). Wishbone addresses are per eFuse word, not per-byte. The maximum supported Wishbone clock frequency is 33 MHz.
//!
//! It's recommended to connect `write_enable_i` signal to the active-low POR reset to protect fuses during a power-up.

module efuse_wb_mem #(
    parameter EFUSE_NWORDS      = 64,                   //! Number of eFuse memory words, should be 2^WB_ADR_WIDTH
    parameter EFUSE_WORD_WIDTH  = 8,                    //! eFuse word width
    parameter WB_ADR_WIDTH      = 6,                    //! Wishbone address bus width
    parameter WB_DAT_WIDTH      = 8,                    //! Wishbone data buses width, should be equal to EFUSE_WORD_WIDTH
    parameter WB_SEL_WIDTH      = (WB_DAT_WIDTH / 8)    //! Wishbone write mask bus width
) (
    input                       wb_clk_i,       //! Wishbone clock
    input                       wb_rst_i,       //! Active-high Wishbone reset
    input                       wb_stb_i,       //! Wishbone STB signal
    input                       wb_cyc_i,       //! Wishbone CYC signal
    input  [WB_ADR_WIDTH-1:0]   wb_adr_i,       //! Wishbone per-word address
    input  [WB_DAT_WIDTH-1:0]   wb_dat_i,       //! Wishbone data to write to eFuse
    input  [WB_SEL_WIDTH-1:0]   wb_sel_i,       //! Wishbone write mask
    input                       wb_we_i,        //! Wishbone write enable
    output [WB_DAT_WIDTH-1:0]   wb_dat_o,       //! Wishbone data read from eFuse
    output                      wb_ack_o,       //! Wishbone acknowledge signal

    input                       write_enable_i  //! Active-high asynchronous write-enable signal
);

endmodule
