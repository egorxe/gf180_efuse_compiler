#
# Helpers for eFuse digital wrappers generation with Librelane
#

import os
import sys
import re
import json
from math import log2
import logging
import subprocess as sp
from pathlib import Path

def macro_size_from_lef(lef : str):
    """
    Helper func to get macro dimensions from LEF
    """
    with open(lef) as f:
        for l in f.readlines():
            match = re.search("SIZE ((?:[0-9]*[.])?[0-9]+) BY ((?:[0-9]*[.])?[0-9]+)", l)
            if match:
                return float(match.group(1)), float(match.group(2))

class LibrelaneRunner():
    """
    Helper class to run Librelane
    """
    def __init__(self):

        # create basic config for GF180MCU
        self.config = dict()

        self.config["meta"] = {"version" : 2, "flow" : "Classic"}

        self.substitute_step("KLayout.DRC")
        self.substitute_step("Checker.KLayoutDRC")

        self.config["PRIMARY_GDSII_STREAMOUT_TOOL"] = "klayout"
        self.config["PL_KEEP_RESIZE_BELOW_OVERFLOW"] = 0

        # following is to disable ports buffering & wire repair with dly cells as they degrade timing
        self.cd = Path(__file__).parent.absolute()
        self.config["PNR_EXCLUDED_CELL_FILE"] = str(self.cd / "pnr_exclude.cells")

        self.config["VDD_NETS"] = ["VDD"]
        self.config["GND_NETS"] = ["VSS"]

        self.config["MACROS"] = {}

    def substitute_step(self, step : str, sub : str = None):
        if "substituting_steps" not in self.config["meta"]:
            self.config["meta"]["substituting_steps"] = {}
        self.config["meta"]["substituting_steps"][step] = sub

    def add_macro(self, name : str, gds : str, lef : str, nl : str, instances : list):
        
        self.config["MACROS"][name] = macro = dict()
        macro["gds"] = [ str(gds) ]
        macro["lef"] = [ str(lef) ]
        macro["nl"] = [ str(nl) ]

        macro["instances"] = {}

        for i in instances:
            macro["instances"][i] = inst = dict()
            inst["location"] = [ instances[i][0], instances[i][1] ]
            inst["orientation"] = instances[i][2]

    def run(self):
        """
        Create necessary files and run Librelane with config from dict
        """
        orig_wd = os.getcwd()
        os.makedirs("librelane", exist_ok=True)
        os.chdir("librelane")

        with open("config.json", "w") as f:
            json.dump(self.config, f, indent = 4)
        
        log = Path("librelane.log").absolute()
        try:
            run = sp.run(["librelane", "config.json", "--pdk", os.environ["PDK"], "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk"],
                stdout = sp.PIPE, stderr = sp.STDOUT, check = True)
            with open(log, "a") as f:
                f.write(run.stdout.decode("utf-8"))
            self.final = list(Path("runs").glob("*/final"))[0].absolute()

            self.gds = self.final / "gds" / f"{self.name}.gds"
            self.lef = self.final / "lef" / f"{self.name}.lef"
            self.nl  = self.final / "nl"  / f"{self.name}.nl.v"
            self.pnl = self.final / "pnl" / f"{self.name}.pnl.v"
            self.lib = self.final / "lib"
            self.sdf = self.final / "sdf"
            
        except sp.CalledProcessError as e:
            logging.error(f"Librelane run failed! See {log} for log.")
            with open(log, "w") as f:
                f.write(e.stdout.decode("utf-8"))
            self.final = None

        os.chdir(orig_wd)
        return self.final

    @staticmethod 
    def panic(msg : str):
        """
        Exit with error message.
        """
        logging.error(msg)
        sys.exit(1)


class EfuseLibrelane(LibrelaneRunner):
    """
    eFuse memory digital wrapper implementation in Librelane
    """
    def __init__(self, params : tuple, macro : str, gds : str, lef : str, bb : str, nwords : int, word_width : int):

        super().__init__()

        # check requested parameters
        if params[0] not in ["wishbone", "spi"]:
            self.panic("Only Wishbone and SPI wrappers are supported.")

        supported_params = (
            ("wishbone", 32, 8), ("wishbone", 64, 8), ("wishbone", 64, 32), ("wishbone", 128, 8), 
            ("wishbone", 512, 32), ("wishbone", 1024, 32), ("spi", 128, 8), ("spi", 256, 8), 
        )
        if params not in supported_params:
            logging.warning(f"Digital wrapper configuration {params} was not tested and might fail to generate. " +
                f"Only the following configurations with largest fitting array geometry were confirmed to work: {supported_params}.")

        if word_width != params[2]:
            self.panic("Width of the digital wrapper interface should match array width.")

        if int(2 ** log2(params[1])) != params[1]:
            self.panic("Depth of the digital wrapper should be a power of 2.")

        if params[0] == "spi": 
            if word_width != 8:
                self.panic("SPI wrapper supports only 8-bit width.")
            spi = 1
        else:
            spi = 0

        # determine sizes and paths
        self.macro = macro
        self.nwords = nwords
        self.word_width = word_width

        if (params[1] % nwords) or (params[2] % word_width):
            self.panic("Each digital wrapper dimention should be a multiple of corresponding array size dimention.")
        n_arrays_depth = params[1] // nwords

        # get array dimensions from LEF
        array_x, array_y = macro_size_from_lef(lef)

        # set basic vars
        self.wb_name = f"efuse_wb_mem_{params[1]}x{params[2]}"
        if spi:
            self.name = f"efuse_spi_mem_{params[1]}x{params[2]}"
        else:
            self.name = self.wb_name
        self.config["DESIGN_NAME"] = self.name
        self.config["VERILOG_FILES"] = [ str(self.cd / "efuse_wb_mem.v") ]
        if spi:
            self.config["VERILOG_FILES"] += [str(self.cd / "efuse_spi_mem.v"), str(self.cd / "spi2wb.v")]
        self.config["PNR_SDC_FILE"] = [ str(self.cd / "constraints.sdc") ]
        self.config["CLOCK_PORT"] = "wb_clk_i" if not spi else "clk_i"
        self.config["CLOCK_PERIOD"] = 30

        # set defines & parameters
        mask = (params[2] // 8) if params[2] % 8 == 0 else 1

        self.config["VERILOG_DEFINES"] = [f"EFUSE_WBMEM_NAME={self.wb_name}", f"EFUSE_ARRAY_NAME={macro}"]
        self.config["SYNTH_PARAMETERS"] = [
            f"EFUSE_NWORDS={nwords}", 
            f"EFUSE_WORD_WIDTH={word_width}", 
            f"WB_DAT_WIDTH={params[2]}", 
            f"WB_SEL_WIDTH={mask}",
            f"WB_ADR_WIDTH={int(log2(params[1]))}",
        ]
        if spi:
            self.config["VERILOG_DEFINES"].append(f"EFUSE_SPIMEM_NAME={self.name}")

        # floorplan & PDN
        cm = 10 # core margin
        wb_area = 35000 + spi*10000 # area estimate
        if (n_arrays_depth < 2) and (mask > 1):
            wb_area += 2000
        array_step_x = (int((wb_area / (n_arrays_depth * array_y))*10)/10) + 35

        self.config["FP_SIZING"] = "absolute"
        self.config["DIE_AREA"] = da = [0, 0, array_x*n_arrays_depth + array_step_x*n_arrays_depth, array_y+50]
        self.config["CORE_AREA"] = [da[0] + cm, da[1] + cm, da[2] - cm, da[3] - cm]
        pin_cfg = "spi_pin.cfg" if spi else "pin.cfg"
        self.config["IO_PIN_ORDER_CFG"] = str(self.cd / pin_cfg)

        self.config["FP_PDN_CORE_RING"] = True
        self.config["PDN_CORE_RING_VWIDTH"] = 2
        self.config["PDN_CORE_RING_HWIDTH"] = 2
        self.config["PDN_CORE_RING_VSPACING"] = 0.5
        self.config["PDN_CORE_RING_HSPACING"] = 0.5
        self.config["PDN_CORE_RING_VOFFSET"] = 4
        self.config["PDN_CORE_RING_HOFFSET"] = 7

        self.config["PDN_HPITCH"] = 50
        self.config["PDN_HOFFSET"] = 5
        self.config["PDN_VPITCH"] = 50
        self.config["PDN_VOFFSET"] = 5
        self.config["FP_MACRO_HORIZONTAL_HALO"] = 5
        self.config["FP_MACRO_VERTICAL_HALO"] = 3
        self.config["PDN_CFG"] = str(self.cd / "pdn_cfg.tcl")

        # PnR
        self.config["PL_MAX_DISPLACEMENT_X"] = (array_x+array_step_x)*3
        self.config["PL_MAX_DISPLACEMENT_Y"] = array_y
        self.config["RT_MAX_LAYER"] = "Metal4"
        self.config["GRT_ALLOW_CONGESTION"] = True
        self.config["RSZ_DONT_TOUCH_RX"] = ".*_keep_cell"
        self.config["DIODE_ON_PORTS"] = "both"
        self.config["DESIGN_REPAIR_MAX_WIRE_LENGTH"] = 1000
        self.config["GRT_ANTENNA_MARGIN"] = 30
        self.config["GRT_ANTENNA_ITERS"] = 10
        self.config["DRT_ANTENNA_REPAIR_ITERS"] = 10

        # efuse macro
        array_inst = {}
        prefix = "efuse_wb_mem." if spi else ""
        for x in range(n_arrays_depth):
            array_inst.update({f"{prefix}efuse_gen_depth[{x}].efuse_array" : [cm + (array_x+array_step_x)*x , cm + 5, "N" if (x%2) else "FN"]})
        self.add_macro(macro, gds, lef, bb, array_inst)


class EfuseAsyncLibrelane(LibrelaneRunner):
    """
    eFuse memory async wrapper implementation in Librelane
    """
    def __init__(self, params, macro : str, gds : str, lef : str, bb : str, nwords : int, word_width : int):

        super().__init__()
        assert(nwords==1 and word_width==8) # the only size supported for now

        if params[0] != "async":
            self.panic("Please use async wrapper for the async eFuse array.")

        # determine sizes and paths
        self.macro = macro
        self.nwords = nwords
        self.word_width = word_width

        # get array dimensions from LEF
        array_x, array_y = macro_size_from_lef(lef)

        # set basic vars
        self.substitute_step("OpenROAD.CTS")
        self.substitute_step("Checker.SetupViolations")
        self.name = f"efuse_async_mem_{nwords}x{word_width}"
        self.config["DESIGN_NAME"] = self.name
        self.config["VERILOG_FILES"] = [ str(self.cd / "efuse_async_mem.v") ]

        # floorplan & PDN
        cm = 10 # core margin

        self.config["FP_SIZING"] = "absolute"
        self.config["DIE_AREA"] = da = [0, 0, array_x+cm*2+35, array_y+cm*3]
        self.config["CORE_AREA"] = [da[0] + cm, da[1] + cm, da[2] - cm, da[3] - cm]
        self.config["IO_PIN_ORDER_CFG"] = str(self.cd / "async_pin.cfg")

        self.config["FP_PDN_CORE_RING"] = True
        self.config["PDN_CORE_RING_VWIDTH"] = 1.2
        self.config["PDN_CORE_RING_HWIDTH"] = 1.2
        self.config["PDN_CORE_RING_VSPACING"] = 0.5
        self.config["PDN_CORE_RING_HSPACING"] = 0.5
        self.config["PDN_CORE_RING_VOFFSET"] = 4
        self.config["PDN_CORE_RING_HOFFSET"] = 7

        self.config["PDN_HPITCH"] = 20
        self.config["PDN_HOFFSET"] = 5
        self.config["PDN_VPITCH"] = 20
        self.config["PDN_VOFFSET"] = 5
        self.config["FP_MACRO_HORIZONTAL_HALO"] = 5
        self.config["FP_MACRO_VERTICAL_HALO"] = 3
        self.config["PDN_CFG"] = str(self.cd / "pdn_cfg.tcl")

        # PnR
        self.config["PL_MAX_DISPLACEMENT_X"] = array_x
        self.config["PL_MAX_DISPLACEMENT_Y"] = array_y
        self.config["RT_MAX_LAYER"] = "Metal4"
        self.config["GRT_ALLOW_CONGESTION"] = True
        self.config["RSZ_DONT_TOUCH_RX"] = ".*_cell"
        self.config["DIODE_ON_PORTS"] = "in"
        self.config["DESIGN_REPAIR_MAX_WIRE_LENGTH"] = 800

        # efuse macro
        array_inst = {}
        array_inst.update({"efuse_array" : [cm , cm+7, "FN"]})
        self.add_macro(macro, gds, lef, bb, array_inst)
