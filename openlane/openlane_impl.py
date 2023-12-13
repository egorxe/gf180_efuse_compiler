#!/usr/bin/env python3

import json
import os
import sys
import glob

TOP = "efuse_ctrl"

PRODUCTS_DIR = "products"
MACRO_DIR = "../../macros"
RUNS_DIR = "runs"

SOURCES = "../../hdl/addr_sel.vhd  ../../hdl/dmuxn.vhd  ../../hdl/efuse_bank.vhd  ../../hdl/efuse_ctrl.vhd  ../../hdl/efuse_rom.vhd"
VERILOG = TOP + "_fromvhdl.v"
CELLS = MACRO_DIR + "/cells.v"
BBOX = MACRO_DIR + "/efuse_array"
OL_CFG = "config.json"
PDN_CFG = "../pdn_cfg.tcl"
PIN_CFG = "../pin.cfg"
MACRO_FILE = "macro_placement.cfg"
STRIPE_EXTENSION_FILE = "extend_stripes.tcl"
LEF_SCRIPT = "make_lef.tcl"
LEF_FILE = TOP + ".lef"

SIZE_X          = 2175
SIZE_Y          = 2370
MACRO_OFF_X     = 40
MACRO_OFF_Y     = 45
MACRO_STEP_X    = 88
MACRO_STEP_Y    = 768
MACRO_X         = 24
MACRO_Y         = 3

PDN_HOR_START   = 42
PDN_HOR_WDT     = 15
PDN_HOR_STEP    = 45
M5_OBS_DELTA    = 0 
M5_OBS_SIDES    = 10

MACRO_FORMAT = "efuse_rom_inst.gen_efuse_banks:{i}.efuse_bank_inst.efuse_array_inst"

EXTEND_STRIPES_FORMAT = r'''extend_stripe $layer ${NET}_net {X0} {Y0} {X1} {Y1}'''
EXTEND_STRIPES_PROTOTYPE = r'''
proc dbu {x} {
    return [ord::microns_to_dbu [expr {$x * 1.0}]]
}

proc extend_stripe {layer swire x0 y0 x1 y1} {
    odb::dbSBox_create $swire $layer [dbu $x0] [dbu $y0] [dbu $x1] [dbu $y1] STRIPE
}

set block [ord::get_db_block]
set VDD_net [odb::dbSWire_create [$block findNet VDD] ROUTED]
set VSS_net [odb::dbSWire_create [$block findNet VSS] ROUTED]
set tech [ord::get_db_tech]
set layer [$tech findLayer Metal4]
'''

def AddPinsToLef(lines, pins, layers, adds):
    out = ""
    pin_line = -1
    for i in range(len(pins)):
        pins[i] = pins[i].upper()
    for i in range(len(layers)):
        layers[i] = layers[i].upper()
    for l in lines:
        out += l
        if pin_line >= 0:
            ls = l.split()
            if len(ls) > 1 and ls[1].upper() == layers[pin_line]:
                out += adds[pin_line] + "\n"
                pin_line = -1
        else:
            for i in range(len(pins)):
                if l.strip().upper() == ("PIN " + pins[i]):
                    pin_line = i
                    break
    return out
    
def ReplaceLefObstruction(lines, obs, layer):
    obs_line = -1
    out = ""
    layer = layer.upper()
    
    for l in lines:
        lstr = l.strip().upper()
        lspl = lstr.split()
        if obs_line == -1:
            out += l
            if lstr == "OBS":
                obs_line = 0
        else:
            
            if obs_line == 0:
                out += l
                if len(lspl) > 1 and lspl[1] == layer:
                    obs_line = 1
            else:
                if (lstr == "END") or ("LAYER" in lstr):
                    obs_line = -1
                    out += obs + l
            
    return out

LEF_RECT_FORMAT = "        RECT {X0} {Y0} {X1} {Y1} ;\n"
OBS_FORMAT = "{LAYER} {X0} {Y0} {X1} {Y1}, "

# Go to directory for implementation files
os.system("mkdir -p " + PRODUCTS_DIR)
os.chdir(PRODUCTS_DIR)

lef_vdd_pins = ""
lef_vss_pins = ""
obs = ""
obs_lef = ""

# Generate macro placement
with open(MACRO_FILE, "w") as f:
    extend_stripes = EXTEND_STRIPES_PROTOTYPE
    for x in range(MACRO_X):
        vss_pin = [0]*4
        vdd_pin = [0]*4
        for y in range(MACRO_Y):
            line = MACRO_FORMAT.format(i=y*MACRO_X + x + 1)
            offx = x*MACRO_STEP_X
            offy = y*MACRO_STEP_Y
            macro_loc = (MACRO_OFF_X + offx, MACRO_OFF_Y + offy)
            line += " " + str(macro_loc[0]) + " " + str(macro_loc[1]) + " R90"
            print(line, file=f)

            vss_ext = (40.0+offx, 762.50+offy, 42.5+offx, 813.20+offy)
            vdd_ext = (97.805+offx, 762.50+offy, 100.305+offx, 813.20+offy)
            extend_stripes += EXTEND_STRIPES_FORMAT.format(NET="VSS", X0=vss_ext[0], Y0=vss_ext[1], X1=vss_ext[2], Y1=vss_ext[3]) + "\n"
            extend_stripes += EXTEND_STRIPES_FORMAT.format(NET="VDD", X0=vdd_ext[0], Y0=vdd_ext[1], X1=vdd_ext[2], Y1=vdd_ext[3]) + "\n"
            
            lef_vss_pins += LEF_RECT_FORMAT.format(X0=vdd_ext[0]-3.97, Y0=macro_loc[1], X1=vdd_ext[2]-3.97, Y1=macro_loc[1]+680)
            
            if y == 0:
                vss_pin[0] = vss_ext[0]
                vss_pin[1] = MACRO_OFF_Y
                vss_pin[2] = vss_ext[2]
                vdd_pin[0] = vdd_ext[0]
                vdd_pin[1] = MACRO_OFF_Y
                vdd_pin[2] = vdd_ext[2]
            elif y == MACRO_Y-1:
                vss_pin[3] = vss_ext[3]
                vdd_pin[3] = vdd_ext[3]
        
        lef_vdd_pins += LEF_RECT_FORMAT.format(X0=vdd_pin[0], Y0=vdd_pin[1], X1=vdd_pin[2], Y1=vdd_pin[3])
        lef_vss_pins += LEF_RECT_FORMAT.format(X0=vss_pin[0], Y0=vss_pin[1], X1=vss_pin[2], Y1=vss_pin[3])

# Generate stripe extension file
with open(STRIPE_EXTENSION_FILE, "w") as f:
    print(extend_stripes, file=f)

# Generate Met5 obstruction for top PDN
y = PDN_HOR_START
y_prev = 0
while y < SIZE_Y:
    y0 = y-PDN_HOR_WDT/2
    y1 = y+PDN_HOR_WDT/2
    obs += OBS_FORMAT.format(LAYER="Metal5", X0 = 0, Y0 = y0, X1 = SIZE_X, Y1 = y1) 
    obs_lef += LEF_RECT_FORMAT.format(X0 = M5_OBS_SIDES, Y0 = y_prev-M5_OBS_DELTA, X1 = SIZE_X-M5_OBS_SIDES, Y1 = y0+M5_OBS_DELTA) 
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
    "PL_TARGET_DENSITY" : 0.70,
    
    "FP_PDN_CFG" : PDN_CFG,
    "FP_TAP_HORIZONTAL_HALO" : 2,
    "FP_TAP_VERTICAL_HALO" : 1,
    "FP_PDN_HORIZONTAL_HALO" : 1,
    "FP_PDN_VERTICAL_HALO" : 1,
    "FP_PDN_AUTO_ADJUST" : 0,
    "FP_PDN_VOFFSET" : 20,
    "FP_PDN_VPITCH" : 190,
    "FP_PDN_HPITCH" : 25,
    "FP_PDN_VSPACING" : 8,
    "FP_PIN_ORDER_CFG" : PIN_CFG,
    
    "PL_MAX_DISPLACEMENT_X" : 2000,
    "PL_MAX_DISPLACEMENT_Y" : 2000,
    
    "EXTRA_LEFS" : os.path.abspath(BBOX + ".lef"),
    "EXTRA_GDS_FILES" : os.path.abspath(BBOX + ".gds"),
    "VERILOG_FILES_BLACKBOX" : os.path.abspath(BBOX + ".v"),
    "MACRO_PLACEMENT_CFG" : MACRO_FILE,
    
    "ROUTING_CORES" : "24",
    "GRT_ALLOW_CONGESTION" : 1,
    "GRT_ADJUSTMENT" : 0.20,
    "GRT_OBS" : obs[:-2],
    
    "RUN_IRDROP_REPORT" : 0,
    "RUN_KLAYOUT_XOR" : 0,
    "RUN_MAGIC" : 0,
    "RUN_LVS" : 1,
    "PRIMARY_SIGNOFF_TOOL" : "klayout",     # Magic deletes "extended" stripes for some reason
    
    "CLOCK_PORT" : "wb_clk_i",
    "CLOCK_PERIOD" : 30
}

# Dump config JSON
json.dump(config, open(OL_CFG, "w"), indent=4)
   
#Launch Yosys+GHDL VHDL->Verilog conversion
err = os.system(r'''yosys -m ghdl -p "ghdl -fsynopsys --std=08 --work=efuselib {SOURCES} -e {TOP}; hierarchy -check -top {TOP}; write_verilog {VERILOG}"'''\
    .format(SOURCES=SOURCES, TOP=TOP, VERILOG=VERILOG))
if err != 0:
    print("VHDL->Verilog finished with error")
    sys.exit(err)
    
# Launch Openlane implementation
os.environ["PDK"] = "gf180mcuC"
os.environ["STD_CELL_LIBRARY"] = "gf180mcu_fd_sc_mcu7t5v0"
err = os.system("flow.tcl -ignore_mismatches -design .")
if err != 0:
    print("Openlane finished with error")
    sys.exit(err)

# Sorting run dirs based on the creation time
dirs = list(filter(os.path.isdir, glob.glob(RUNS_DIR + "/*"))) 
dirs.sort(key=os.path.getctime)
rundir = dirs[-1]

# Create LEF by OR
odb_file = rundir + "/results/routing/" + TOP + ".odb"
print(odb_file)
lef_file = rundir + "/results/final/lef/" + LEF_FILE
with open(LEF_SCRIPT, "w") as f:
    f.write("read_db {DB}\nwrite_abstract_lef -bloat_occupied_layers {LEF}\n".format(DB=odb_file, LEF=lef_file))
err = os.system("openroad -exit " + LEF_SCRIPT)
if err != 0:
    print("LEF creation finished with error")
    sys.exit(err)

# Patch LEF with obstruction & pins needed for chip-level PDN
lef = AddPinsToLef(open(lef_file).readlines(), ["VSS", "VDD"], ["Metal4", "Metal4"], [lef_vss_pins, lef_vdd_pins])
lef = ReplaceLefObstruction(lef.splitlines(True), obs_lef, "Metal5")
open(lef_file, "w").write(lef)
 
