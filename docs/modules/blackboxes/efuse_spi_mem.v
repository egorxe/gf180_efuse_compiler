//! @title eFuse memory block with SPI interface
//!
//! This is a digital wrapper around efuse_array providing an EEPROM-like SPI interface to the eFuse memory.
//!
//! SPI protocol is a subset of the 25-series SPI EEPROMs protocol with an active-low chip-select and data latching on the rising clock edge. The protocol consists of sending an 8-bit command opcode to the device first and receiving or sending more data after it, depending on the command. The 24-bit address is used in read and write sequences, but bits exceeding the eFuse depth are ignored. Maximum SPI clock frequency is 10 MHz.
//!
//!Supported SPI commands are:
//!
//! | Cmd name | Opcode Hex  | Description                                       |
//! |----------|-------------|---------------------------------------------------|
//! | WRITE    | 0x02        | Write to memory. Only single writes are supported.|
//! | READ     | 0x03        | Read from memory. Continuos reading is supported. |
//! | WRDI     | 0x04        | Disable writing to eFuse array (default).         |
//! | RDSR     | 0x05        | Read status register.                             |
//! | WREN     | 0x06        | Enable writing to eFuse array.                    |
//!
//! In order to program the eFuse memory, first, the device must be write-enabled using the WREN instruction (once after reset or `WRDI`). Then the `WRITE` instruction should be transmitted, followed by the 24-bit address and a single byte to be written.
//!
//!{head:{text:'Example of a write cycle (without WREN) '},
//!  signal: [
//!    {name: 'spi_csn'   , wave: '10..........|..........1'},
//!    {name: 'spi_clk'   , wave: '0.p.........|.........l.', phase: -0.5},
//!    {name: 'spi_mosi'  , wave: 'x.==========|============.', data : ['0', '0', '0', '0', '0', '0', '1', '0','A23', '...', 'A0', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'D1', 'D0', ] },
//!    {node:                     '..A.......B...C.......D.'},
//!    {name: 'spi_miso'  , wave: 'x.......................'},
//!  ],
//!  edge: ['A+B WRITE opcode', 'B+C address', 'C+D data to write'],
//!}
//!
//! Reading the eFuse memory requires the following sequence. After the `spi_csn` is pulled low, the `READ` instruction should be transmitted, followed by the 24-bit address to be read. Data byte at the specified eFuse address is then shifted out via the `spi_miso` line. If only one byte is to be read, the `spi_csn` should be driven high after the last data bit. If `spi_csn` stays low, the read sequence will continue, automatically incrementing the byte address, and data will continue to be shifted out.
//!
//!{head:{text:'Example of a read cycle '},
//!  signal: [
//!    {name: 'spi_csn'   , wave: '10..........|..........1'},
//!    {name: 'spi_clk'   , wave: '0.p.........|.........l.'},
//!    {name: 'spi_mosi'  , wave: 'x.==========|=x.........', data : ['0', '0', '0', '0', '0', '0', '1', '1', 'A23', '...', 'A0'] },
//!    {node:                     '..A.......B...C........D'},
//!    {name: 'spi_miso'  , wave: 'x.............========x.', data : ['D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'D1', 'D0', ], phase: 0.5},
//!    {node:                     '..............D.......E.', phase: 0.5},
//!  ],
//!  edge: ['A+B READ opcode', 'B+C address', 'D+E read data'],
//!}
//!
//! Readiness of the device to accept the next read/write and write-enable status could be verified by reading the status register with the `RDSR` command.
//!
//! {reg: [
//!     { "name": "BUSY",   "bits": 1 },
//!     { "name": "WE", "bits": 1 },
//!     { "bits": 6 }
//!]}

module efuse_spi_mem #(
    parameter EFUSE_NWORDS      = 256,      //! Number of eFuse words
    parameter EFUSE_WORD_WIDTH  = 8         //! Word width (only 8 is supported)
) (
    input                       spi_csn,    //! Active-low SPI chip-select
    input                       spi_clk,    //! SPI clock
    input                       spi_mosi,   //! SPI controller-to-device line
    output                      spi_miso,   //! SPI device-to-controller line

    input                       clk_i,      //! Internal eFuse clock, should be at least 4x faster than the `spi_clk`
    input                       npor        //! Active-low reset, connection to POR is recommended
);

endmodule