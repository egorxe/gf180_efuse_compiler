//! @title Asynchronous eFuse array block with read after reset
//!
//! This is a small digital wrapper around the {ref}`efuse_array_async` which automatically reads eFuse bits into latches once after reset deassertion.
//!
//! It's recommended to connect `reset_n` signal to the active-low POR reset to protect fuses during a power-up. 
//!
//!{head:{text:'Wrapped async eFuse write cycle'},
//!  signal: [
//!    {node:                       '..A...B.', },
//!    {name: 'reset_n'     , wave: '1....|..',},
//!    {name: 'prog'        , wave: '=.=..|=.', data: ['0', 'bits to write    ', '0']},
//!    {name: 'out'         , wave: 'x....|..'},
//!    {name: 'ready'       , wave: '1....|..'},
//!  ],
//!  edge: ['A+B Tprog'],
//!}
//!
//!{head:{text:'Wrapped async eFuse read after reset'},
//!  signal: [
//!    {node:                       '..A...B.', },
//!    {name: 'reset_n'     , wave: '01.....',},
//!    {name: 'prog'        , wave: '=......', data: ['0']},
//!    {name: 'out'         , wave: 'x.=....', data: ['data from efuse']},
//!    {name: 'ready'       , wave: '0.1....'},
//!  ],
//!}

module efuse_async_mem #(
    parameter   WDT = 8     //! Async memory width
) (
    input               reset_n,    //! Active-low reset (POR)
    input  [WDT-1:0]    prog,       //! Data bits to program
    output [WDT-1:0]    out,        //! Data output, latched automatically after reset
    output              ready       //! Ready signal, goes high after data was latched to output
);

endmodule
