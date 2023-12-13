import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from cocotbext.wishbone.driver import WishboneMaster
from cocotbext.wishbone.driver import WBOp

import random

USER_WB_BASEADDR    = 0x00000000

BLOCK_CFG_ADDR      = 0x30100000
VRNODE_CFG_ADDR     = 0x30200000
HRNODE_CFG_ADDR     = 0x30300000
CLK_CFG_ADDR        = 0x30E00000
RST_CFG_ADDR        = 0x30A00000

CNT_ADDR            = 0x00000000

MEM_WIDTH           = 8
MEM_DEPTH           = 2**10

class WishboneMemTest:
    def __init__(self, wb):
        self.wb = wb
        self.clk = self.wb.dut.wb_clk_i
        self.rst = self.wb.dut.wb_rst_i
                
    async def write_mem_data(self, addr, data):
        await self.wb.write(USER_WB_BASEADDR + addr, data)

    async def read_mem_data(self, addr):
        val = await self.wb.read(USER_WB_BASEADDR + addr)
        return val

@cocotb.test()
async def run_test(dut):
    # Create wishbone access helpers
    wb = WishboneRegs(dut, USER_WB_BASEADDR)
    test = WishboneMemTest(wb)
    rst = dut.wb_rst_i
    rst.value = 1
    await cocotb.triggers.ClockCycles(test.clk, 10)
    rst.value = 0
    dut.log.info("Design ready for test!")
    
    model_ram = []
    
    dut.log.info("Init mem with random data...")
    for i in range(MEM_DEPTH):
        buf = random.randint(0, (2**MEM_WIDTH)-1)
        await test.write_mem_data(i, buf)
        model_ram.append(buf)
        
    dut.log.info("Done!")
    
    dut.log.info("Test data readback...")
    for i in range(MEM_DEPTH):
        assert model_ram[i] == await test.read_mem_data(i)
        
    dut.log.info("Done!")
        
