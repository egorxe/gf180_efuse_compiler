#!/usr/bin/env python3

import json
import os
import sys

PRODUCTS_DIR = "products"
SOURCES = "../../hw/addr_sel.vhd  ../../hw/dmuxn.vhd  ../../hw/efuse_bank.vhd  ../../hw/efuse_ctrl.vhd  ../../hw/efuse_rom.vhd"
TOP = "efuse_ctrl"

VERILOG = TOP + "_fromvhdl.v"
MACRO_DIR = "../../macros"
CELLS = MACRO_DIR + "/cells.v"
BBOX = MACRO_DIR + "/efuse_array"
OL_CFG = "config.json"
PDN_CFG = "../pdn_cfg.tcl"
PIN_CFG = "../pin.cfg"
MACRO_FILE = "macro_placement.cfg"

SIZE_X          = 2175
SIZE_Y          = 2370
MACRO_OFF_X     = 40
MACRO_OFF_Y     = 60
MACRO_STEP_X    = 88
MACRO_STEP_Y    = 760
MACRO_X         = 24
MACRO_Y         = 3

PDN_HOR_START   = 42
PDN_HOR_WDT     = 15
PDN_HOR_STEP    = 45
M5_OBS_DELTA    = 0 
M5_OBS_SIDES    = 10 

MACRO_FORMAT = "efuse_rom_inst.gen_efuse_banks:{i}.efuse_bank_inst.efuse_array_inst"

# Go to directory for implementation files
os.system("mkdir -p " + PRODUCTS_DIR)
os.chdir(PRODUCTS_DIR)

# Generate macro placement
f = open(MACRO_FILE, "w")

for y in range(MACRO_Y):
    for x in range(MACRO_X):
        line = MACRO_FORMAT.format(i=y*MACRO_X + x + 1)
        line += " " + str(MACRO_OFF_X + x*MACRO_STEP_X) + " " + str(MACRO_OFF_Y + y*MACRO_STEP_Y) + " N"
        print(line, file=f)

# Generate Met5 obstruction for top PDN
obs = ""
obs_lef = ""
y = PDN_HOR_START
y_prev = 0
while y < SIZE_Y:
    y0 = y-PDN_HOR_WDT/2
    y1 = y+PDN_HOR_WDT/2
    obs += "Metal5 0 {y0} {x1} {y1}, ".format(y0 = y0, x1 = SIZE_X, y1 = y1) 
    obs_lef += "        RECT {x0} {y0} {x1} {y1} ;\n".format(x0 = M5_OBS_SIDES, y0 = y_prev-M5_OBS_DELTA, x1 = SIZE_X-M5_OBS_SIDES, y1 = y0+M5_OBS_DELTA) 
    y_prev = y1
    y += PDN_HOR_STEP

# Create config dict
config = { 
    "DESIGN_NAME" : TOP, 
    "VERILOG_FILES" : VERILOG + " " + CELLS,
    "DESIGN_IS_CORE" : 0,
    "FP_SIZING" : "absolute",
    "DIE_AREA" : "0 0 " + str(SIZE_X) + " " + str(SIZE_Y),
    "SYNTH_STRATEGY" : "AREA 3",
    "PL_TARGET_DENSITY" : 0.55,
    
    "PDN_CFG" : PDN_CFG,
    "FP_TAP_HORIZONTAL_HALO" : 1,
    "FP_PDN_HORIZONTAL_HALO" : 1,
    "FP_PDN_AUTO_ADJUST" : 0,
    "FP_PDN_VOFFSET" : 20,
    "FP_PDN_VPITCH" : 190,
    "FP_PDN_VSPACING" : 8,
    "FP_PIN_ORDER_CFG" : PIN_CFG,
    
    "PL_MAX_DISPLACEMENT_X" : 2000,
    "PL_MAX_DISPLACEMENT_Y" : 2000,
    
    "LVS_CONNECT_BY_LABEL" : 1,
    
    "EXTRA_LEFS" : os.path.abspath(BBOX + ".lef"),
    "EXTRA_GDS_FILES" : os.path.abspath(BBOX + ".gds"),
    # ~ "EXTRA_LIBS" : os.path.abspath(BBOX + ".lib"),
    "VERILOG_FILES_BLACKBOX" : os.path.abspath(BBOX + ".v"),
    "MACRO_PLACEMENT_CFG" : "macro_placement.cfg",
    
    "ROUTING_CORES" : "24",
    "GRT_ALLOW_CONGESTION" : 1,
    "GRT_OBS" : obs[:-2],
    
    "CLOCK_PORT" : "wb_clk_i",
    "CLOCK_PERIOD" : 20
}

# Dump config JSON
json.dump(config, open(OL_CFG, "w"), indent=4)

# LEF obstruction needed for chip-level PDN
# ~ print(obs_lef)

# Launch Yosys+GHDL VHDL->Verilog conversion
err = os.system(r'''yosys -m ghdl -p "ghdl -fsynopsys --std=08 --work=efuselib {SOURCES} -e {TOP}; hierarchy -check -top {TOP}; write_verilog {VERILOG}"'''\
    .format(SOURCES=SOURCES, TOP=TOP, VERILOG=VERILOG))
if err != 0:
    sys.exit(err)
    
# Launch Openlane implementation
os.environ["PDK"] = "gf180mcuC"
os.environ["STD_CELL_LIBRARY"] = "gf180mcu_fd_sc_mcu7t5v0"
err = os.system("flow.tcl -ignore_mismatches -design .")
if err != 0:
    sys.exit(err)
