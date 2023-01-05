Define('CLR_RTL', value = '1')

AddFile('hw/efuse_array.vhd', libname='work', src_type='vhdl', vhdl='2008')
AddFile('hw/addr_sel.vhd', libname='work', src_type='vhdl', vhdl='2008')
AddFile('hw/efuse_bank.vhd', libname='work', src_type='vhdl', vhdl='2008')
AddFile('hw/dmuxn.vhd', libname='work', src_type='vhdl', vhdl='2008')
AddFile('hw/efuse_rom.vhd', libname='work', src_type='vhdl', vhdl='2008')
AddFile('hw/efuse_ctrl.vhd', libname='work', src_type='vhdl', vhdl='2008')

AddTestBench("hw/efuse_ctrl_tb.py")
SetTop('efuse_ctrl')
