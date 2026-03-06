//! @title Basic eFuse array block

//! This is a basic eFuse memory block. Contains 16, 32, or 64 word deep eFuse array of arbitrary width plus a sense amplifier circuit.
//!
//! To write data to the eFuse array, a single word should be selected using one-hot encoding on the `BIT_SEL` bus an inverted data word to write should be provided on the `COL_PROG_N` input. All 0 bits on the `COL_PROG_N` bus will result in blowing of the corresponding fuses in the selected word, and all 1 bits will leave fuses intact. Value on `COL_PROG_N` bus should be kept for at least 1 ms (Tprog).
//!{head:{text:'Sync eFuse write cycle'},
//!  signal: [
//!    {node:                     '..A...B.', },
//!    {name: 'BIT_SEL'   , wave: '==...|.=', data: ['0', '1-hot addr  ', '0']},
//!    {name: 'COL_PROG_N', wave: '=.=..|=.', data: ['all ones', 'inv. bits to write    ', 'all ones']},
//!    {name: 'PRESET_N'  , wave: '1....|..'},
//!    {name: 'SENSE'     , wave: '0....|..'},
//!    {name: 'OUT'       , wave: 'x....|..'},
//!  ],
//!  edge: ['A+B Tprog'],
//!}
//! To read data from the eFuse array, first, a sense amplifier circuit should be precharged by keeping `PRESET_N` input low for at least 1 ns (Tpreset). After that, the sensing circuit should be enabled by setting `SENSE` high (at least 10 ns, Tsense), and bringing `PRESET_N` back high. Finally, a word to read should be selected using one-hot encoding on the `BIT_SEL` bus. Output data will be latched to the `OUT` bus no later than 10 ns (Tout) after the address selection.
//!
//!{head:{text:'Sync eFuse read cycle'},
//!  signal: [
//!    {node:                     '.ABC...D.', },
//!    {name: 'BIT_SEL'   , wave: '=..=...=.', data: ['0', '1-hot addr    ', '0']},
//!    {name: 'COL_PROG_N', wave: '=........', data: ['all ones']},
//!    {name: 'PRESET_N'  , wave: '10.1.....'},
//!    {name: 'SENSE'     , wave: '0.1....0.'},
//!    {name: 'OUT'       , wave: 'x.....=..', data: ['read bits']},
//!    {node:                     '...E..F..', },
//!  ],
//!  edge: ['A+C Tpreset', 'C+D Tsense', 'E+F Tout'],
//!}
//! 


module efuse_array #(
    parameter NWORDS = 16,      //! Number of words in eFuse block (depth)
    parameter WORD_WIDTH = 1    //! Word width
) (
    input  [NWORDS-1:0]     BIT_SEL,        //! Word select, one-hot encoding
    input  [WORD_WIDTH-1:0] COL_PROG_N,     //! Active-low bit write data
    input                   PRESET_N,       //! Active-low senseamp preset signal
    input                   SENSE,          //! Sense enable (read) signal
    output [WORD_WIDTH-1:0] OUT             //! Read data bus
);
endmodule
            