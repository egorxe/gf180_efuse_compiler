import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from cocotbext.wishbone.driver import WishboneMaster
from cocotbext.wishbone.driver import WBOp

USER_WB_BASEADDR    = 0x00000000

BLOCK_CFG_ADDR      = 0x30010000
VRNODE_CFG_ADDR     = 0x30011000
HRNODE_CFG_ADDR     = 0x30012000
RST_CFG_ADDR        = 0x3001A000
CLK_CFG_ADDR        = 0x3001E000

LOGIC_CLK_ENA        = 0x40000000
SRAM_CLK_ENA         = 0x80000000

CONFIG_DELAY_TICKS  = 1
FREQ_KHZ            = 3000

block_fw = []
vrnode_fw = []
hrnode_fw = []

def listToString(s): 
    # initialize an empty string
    str1 = "" 
    # traverse in the string  
    for ele in s: 
        str1 += ele  
    # return string  
    return str1 

class WishboneRegs:
    def __init__(self, dut, base):
        self.dut = dut
        self.base = base
        self.clk = self.dut.wb_clk_i
        self.wbs = WishboneMaster(self.dut, "wb", self.clk, width=8, timeout=10,
            signals_dict={"cyc":  "cyc_i",
                          "stb":  "stb_i",
                          "we":   "we_i",
                          "adr":  "adr_i",
                          "datwr":"dat_i",
                          "datrd":"dat_o",
                          "ack":  "ack_o" })
        
    async def read(self, addr):
        wbres = await self.wbs.send_cycle([WBOp(adr=addr)]) 
        return wbres[0].datrd
        
    async def write(self, addr, dat):
        wbres = await self.wbs.send_cycle([WBOp(adr=addr, dat=dat)]) 
        
class WishboneCfgLoader:
    def __init__(self, wb):
        self.wb = wb
        self.clk = self.wb.dut.wb_clk_i
        self.rst = self.wb.dut.wb_rst_i
        cocotb.fork(Clock(self.clk, round(10**6 / FREQ_KHZ), units="ns").start())
        
    # Reset process
    async def reset(self):
        self.rst.value = 1
        await cocotb.triggers.ClockCycles(self.clk, 10)
        self.rst.value = 0
        await RisingEdge(self.clk)
        await RisingEdge(self.clk)
        
        
