//! @title Basic asynchronous eFuse array block

//! This is a basic asynchronous eFuse memory block which stores whole eFuse array content in latches after a single read. Contains one 8-bit wide word of eFuse plus a sense amplifier circuit per each bit.
//!
//! To write data to the asynchronous eFuse array, `COL_PROG_N` input bus should be driven with an inverted data word to write. All 0 bits on `COL_PROG_N` bus will result in blowing of the corresponding fuses in the array, and all 1 bits will leave fuses intact. Value on `COL_PROG_N` bus should be kept for at least 50 us (Tprog).
//!{head:{text:'Async eFuse write cycle'},
//!  signal: [
//!    {node:                     '..A...B.', },
//!    {name: 'COL_PROG_N', wave: '=.=..|=.', data: ['all ones', 'inv. bits to write    ', 'all ones']},
//!    {name: 'PRESET_N'  , wave: '1....|..'},
//!    {name: 'SENSE'     , wave: '0....|..'},
//!    {name: 'OUT'       , wave: 'x....|..'},
//!  ],
//!  edge: ['A+B Tprog'],
//!}
//! To read data from the eFuse array, first, a sense amplifier circuit should be precharged by keeping `PRESET_N` input low for at least 1 ns (Tpreset) and bringing it back to high after it. After `PRESET_N` is high, the sensing circuit should be enabled by setting `SENSE` high for at least 4 ns (Tsense). Output data will be latched to the `OUT` bus no later than 3 ns (Tout) after the `SENSE` assertion.
//!
//!{head:{text:'Async eFuse read cycle'},
//!  signal: [
//!    {node:                     '.A.BC..D.', },
//!    {name: 'COL_PROG_N', wave: '=........', data: ['all ones']},
//!    {name: 'PRESET_N'  , wave: '10.1.....'},
//!    {name: 'SENSE'     , wave: '0...1..0.'},
//!    {name: 'OUT'       , wave: 'x.....=..', data: ['read bits']},
//!    {node:                     '....E.F..', },
//!  ],
//!  edge: ['A+B Tpreset', 'C+D Tsense', 'E+F Tout'],
//!}
//! 
module efuse_array_async #(
    parameter NWORDS = 1,       //! Number of words in eFuse block (depth)
    parameter WORD_WIDTH = 8    //! Word width
) (
    input  [WORD_WIDTH-1:0] COL_PROG_N,     //! Active-low bit write data
    input                   PRESET_N,       //! Active-low senseamp preset signal
    input                   SENSE,          //! Sense enable (read) signal
    output [WORD_WIDTH-1:0] OUT             //! Read data bus
);
endmodule
            