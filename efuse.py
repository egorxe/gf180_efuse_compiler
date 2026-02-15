#!/usr/bin/env python3
#
# GF180MCU eFuse array creation & verification flow script.
#

import sys
import os
import re
import argparse
import logging
from importlib import util as import_util
from datetime import datetime
from pathlib import Path
from shutil import copy, copytree
import subprocess as sp

from src.efuse_gds_gen.efuse_array import create_efuse_array
from src.efuse_spice_gen.generate_spice import generate_spices
from src.efuse_gds_gen.efuse_array_async import create_efuse_array_async
from src.efuse_spice_gen.generate_spice_async import generate_spices_async
from src.efuse_spice_gen.efuse_tests import EfuseArrayTest, EfuseArrayAsyncTest
from src.magic.magic_wrapper import magic
from src.digital.librelane import EfuseLibrelane, EfuseAsyncLibrelane
from src.digital.verilog import EfuseVerilog

class EfuseFlow:
    """
    eFuse array creation & verification flow.
    """
    def __init__(self, nwords : int, word_width : int, root_dir : Path,
                    xyce_netlist : str, async_efuse : bool, digital_wrapper : tuple,  
                    ncpus : int, skip_drclvs : bool, verbose : bool):
        self.nwords = nwords
        self.word_width = word_width
        self.async_efuse = async_efuse
        async_str = "_async" if async_efuse else ""
        self.name = f"efuse_array{async_str}_{nwords}x{word_width}"
        self.ncpus = ncpus
        self.xyce_netlist = xyce_netlist.lower()
        self.digital_wrapper = digital_wrapper
        self.skip_checks = skip_drclvs

        if async_efuse:
            if nwords != 1 or word_width != 8:
                self.panic("For async eFuse only 1x8 configuration is supported for now.")
            self.async_wrapper_name = f"efuse_async_mem_{nwords}x{word_width}"

        self.root_dir = root_dir
        self.scripts_dir = root_dir / "src"
        self.release_dir = root_dir / "macros" / self.name
        rundir = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.run_dir = root_dir / "runs"
        self.last_link = self.run_dir / "last"
        self.run_dir = self.run_dir / rundir
        os.makedirs(self.run_dir, exist_ok=True)
        try:
            os.unlink(self.last_link)
        except FileNotFoundError:
            pass
        os.symlink(self.run_dir, self.last_link)

        # setup logging
        if verbose:
            logging_level = logging.DEBUG
        else:
            logging_level = logging.INFO
        logging.basicConfig(
            level=logging_level,
            handlers=[
                logging.FileHandler(self.run_dir / "run.log"),
                logging.StreamHandler()
            ],
            format="%(asctime)s | %(module)-12s | %(levelname)-8s | %(message)s",
            datefmt="%d-%b-%Y %H:%M:%S",
        )

    @staticmethod 
    def regexp_patch(file : str, regex : str, sub : str):
        with open(file, "r") as f:
            patched = re.sub(regex, sub, f.read(), flags = re.M | re.I)
        with open(file, "w") as f:
            f.write(patched)

    @staticmethod 
    def panic(msg : str):
        """
        Exit with error message.
        """
        logging.error(msg)
        sys.exit(1)

    @staticmethod 
    def check_in_path(cmd : list):
        """
        Check that binary is in path and is runnable.
        """
        try:
            sp.run(cmd, check = True, capture_output = True)
        except Exception:
            EfuseFlow.panic(f"{cmd[0]} not found in PATH!")

    def run_magic(self, script : str, args : dict = dict(), log = ""):
        """
        Magic call helper.
        """
        if "GDS" not in args:
            args["GDS"] = self.gds_name
        if "CELL" not in args:
            args["CELL"] = self.name
        if not log:
            log = f"{script}.log"
        args["MAGIC_SCRIPT_PATH"] = self.scripts_dir / "magic"
        magic(self.scripts_dir / f"magic/{script}.tcl", args, log)

    def run(self, args : list, log : str, add_msg : str =""):
        """
        Run helper.
        """
        try:
            run = sp.run(args, stdout = sp.PIPE, stderr = sp.STDOUT, check = True)
            with open(log, "a") as f:
                f.write(run.stdout.decode("utf-8"))
        except sp.CalledProcessError as e:
            log = Path(log).absolute()
            with open(log, "a") as err:
                print(e.stdout.decode("utf-8"), file=err)
            self.panic(f"{add_msg} Please see {log} .")

    def check_environment(self):
        """
        Check the environment.
        """
        if ("PDK_ROOT" not in os.environ) or ("PDK" not in os.environ):
            os.environ["PDK_ROOT"] = os.environ["HOME"] + "/.ciel"
            os.environ["PDK"] = "gf180mcuD"
            logging.warning(f"PDK_ROOT and/or PDK environment variables are not set, assuming GF180MCU PDK at: {os.environ['PDK_ROOT']}/{os.environ['PDK']}")
        
        self.pdk_path = Path(os.environ['PDK_ROOT']) / os.environ['PDK']
        if not Path.is_dir(self.pdk_path/"libs.tech/klayout/tech"):
            self.panic(f"PDK not found at {self.pdk_path}")
            sys.exit(1)

        # check for KLayout python module
        ks = import_util.find_spec("klayout")
        if not ks:
            self.panic("klayout python module is not installed!")

        # check for tools in path
        self.check_in_path(["klayout", "-b", "-v"])
        self.check_in_path(["magic", "-d", "null", "--version"])
        if self.xyce_netlist != "none":
            self.check_in_path(["Xyce", "-v"])

    def generate_gds_lef(self):
        """
        Generate eFuse array GDS with KLayout.
        """
        self.gds_name = Path(self.name + ".gds").absolute()
        self.add_cells_json = Path("add_cells.json").absolute()
        logging.info("Generating eFuse array GDS file... ")
        if self.async_efuse:
            create_efuse_array_async(self.gds_name, self.name, self.nwords, self.word_width, flat=False, add_cells = self.add_cells_json)
        else:
            create_efuse_array(self.gds_name, self.name, self.nwords, self.word_width, flat=False, add_cells = self.add_cells_json)
        logging.info(f"eFuse array cell written to {self.gds_name.name}.")

        logging.info("Generating eFuse array LEF file... ")
        self.run_magic("magic_lef")
        self.lef_name = Path(self.name + ".lef").absolute()
        logging.info(f"eFuse array lef written to {self.lef_name.name}")

    def generate_spice(self):
        """
        Generate SPICE netlists & test wrappers.
        """
        logging.info("Generating spice netlists for LVS & simulation... ")
        if self.async_efuse:
            ret = generate_spices_async(self.async_wrapper_name, self.pdk_path, self.nwords, self.word_width, add_cells = self.add_cells_json)
        else:
            ret = generate_spices(self.name, self.pdk_path, self.nwords, self.word_width, add_cells = self.add_cells_json)
        self.spice_name = ret[0]
        self.klvs_name = ret[1]
        self.tb_name = ret[2]

    def magic_extraction(self, digital : bool):
        """
        Run circuit extraction with Magic.
        """
        args = {}
        if digital:
            if self.digital_wrapper[0] == "none":
                return
            args = {"GDS" : self.digital.gds, "CELL" : self.digital.name}
        logging.info(f"Performing {"digital wrapper " if digital else ""}circuit extraction with Magic... ")
        self.ext_netlist = Path(self.name + ".magic_ext.spice").absolute()
        self.run_magic("magic_extract", {"SPICE_NAME" : self.ext_netlist, **args})
        self.pex_netlist = Path(self.name + ".magic_pex.spice").absolute()
        self.run_magic("magic_pex", {"SPICE_NAME" : self.pex_netlist, **args})

        # patch extracted netlists (replace 5V models with 6V)
        self.regexp_patch(self.ext_netlist, "_05v0", "_06v0")
        self.regexp_patch(self.pex_netlist, "_05v0", "_06v0")

    def klayout_checks(self):
        """
        Perform DRC & LVS with KLayout.
        """
        logging.info("Performing KLayout DRC...")
        self.run(
            ["python3", self.pdk_path / "libs.tech/klayout/tech/drc/run_drc.py", f"--path={self.gds_name}", 
                f"--variant={str(self.pdk_path)[-1]}", f"--topcell={self.name}", f"--mp={self.ncpus}"],
            "drc.log", "DRC run failed, or GDS is not DRC clean"
        )
        logging.info("GDS is DRC clean.")
        
        logging.info("Performing KLayout LVS...")
        self.run(
            ["python3", self.pdk_path / "libs.tech/klayout/tech/lvs/run_lvs.py", f"--layout={self.gds_name}", "--lvs_sub=VSS", "--schematic_simplify",
                f"--variant={str(self.pdk_path)[-1]}", f"--topcell={self.name}", f"--netlist={self.klvs_name}", f"--thr={self.ncpus}"],
            "lvs.log", "LVS run failed."
        )
        self.run(["grep", "Congratulations! Netlists match", "lvs.log"], "lvs.err", "GDS does not conform to schematics!")
        logging.info("GDS is LVS clean.")

    def run_xyce_test(self, name : str, netlist : str, is_flat : bool = True):
        """
        Xyce test helper.
        """
        logging.info(f"Running Xyce tests for {name} netlist...")
        if self.async_efuse:
            test = EfuseArrayAsyncTest(self.nwords, self.word_width, self.tb_name, netlist, self.spice_name, is_flat, 5.0, self.ncpus)
        else:
            test = EfuseArrayTest(self.nwords, self.word_width, self.tb_name, netlist, self.spice_name, is_flat, 5.0, self.ncpus)
        if not test.run_tests():
            self.panic("Xyce test failed, stopping.")

    def xyce_tests(self):
        """
        Perform tests in Xyce simulation.
        """
        if self.xyce_netlist == "none":
            return
        if self.async_efuse and self.digital_wrapper[0] == "none":
            self.panic("To perform Xyce simulation of async eFuse netlist, please enable the async digital wrapper.")

        logging.info("Running tests in Xyce simulation...")
        if self.xyce_netlist in ["schematic", "all"]:
            self.run_xyce_test("schematic", self.spice_name, False)
        if self.xyce_netlist in ["extracted", "all"]:
            self.run_xyce_test("extracted", self.ext_netlist)
        if self.xyce_netlist in ["pex", "all"]:
            self.run_xyce_test("PEX", self.pex_netlist)


        logging.info("Xyce tests completed succesfully!")

    def generate_verilog(self):
        """
        Generate Verilog model & blackbox
        """
        logging.info("Generating Verilog models...")
        v = EfuseVerilog(self.name, self.nwords, self.word_width)
        v.gen_verilog()
        self.verilog_bb = v.bb_file
        self.verilog_model = v.model_file

    def gen_digital_wrapper(self):
        """
        Create Librelane digital wrappers around eFuse blocks.
        """
        if self.digital_wrapper[0] != "none":
            logging.info(f"Implementing {self.digital_wrapper[0]} digital wrapper with Librelane...")

            if self.async_efuse:
                self.digital = EfuseAsyncLibrelane(self.digital_wrapper, self.name, self.gds_name, self.lef_name, self.verilog_bb, self.nwords, self.word_width)
            else:
                self.digital = EfuseLibrelane(self.digital_wrapper, self.name, self.gds_name, self.lef_name, self.verilog_bb, self.nwords, self.word_width)
            self.digital.run()
            if not self.digital.final:
                self.panic("Digital wrapper generation failed!")

            self.digital_release_dir = self.release_dir / self.digital.name

            logging.info("Digital wrapper generated successfully!")
        else:
            self.digital_release_dir = None

    def release_files(self):
        """
        Copy resulting files into macro folder.
        """
        logging.info(f"Copying resulting files into {self.release_dir}...")
        os.makedirs(self.release_dir, exist_ok=True)
        copy(self.gds_name, self.release_dir)
        copy(self.lef_name, self.release_dir)
        copy(self.spice_name, self.release_dir)
        copy(self.pex_netlist, self.release_dir)
        copy(self.verilog_bb, self.release_dir)
        copy(self.verilog_model, self.release_dir)

        if self.digital_release_dir:
            os.makedirs(self.digital_release_dir, exist_ok=True)
            copy(self.digital.gds, self.digital_release_dir)
            copy(self.digital.lef, self.digital_release_dir)
            copy(self.digital.nl,  self.digital_release_dir)
            copy(self.digital.pnl, self.digital_release_dir)
            copytree(self.digital.lib, self.digital_release_dir, dirs_exist_ok=True)
            copytree(self.digital.sdf, self.digital_release_dir, dirs_exist_ok=True)

    def run_flow(self):        
        """
        Run all stages of the flow.
        """
        # change to run directory
        logging.info(f"Starting eFuse array generation flow, working directory is {self.run_dir}")
        os.chdir(self.run_dir)

        # run all the stages
        self.check_environment()
    
        self.generate_gds_lef()
        
        self.generate_spice()

        if not self.skip_checks:
            self.klayout_checks()

        self.generate_verilog()

        self.gen_digital_wrapper()

        self.magic_extraction(self.async_efuse) # for async array digital wrapper will be extracted
        
        self.xyce_tests()

        self.release_files()

        logging.info("eFuse array generation completed successfully!")

def main():
    """
    Main
    """
    # parse arguments
    parser = argparse.ArgumentParser(description = "A script to generate and verify eFuse array targeting GF180MCU technology.")
    parser.add_argument("number_of_words", type = int,      help = "Number of words in eFuse array.")
    parser.add_argument("word_width", type = int,           help = "Width of word in eFuse array.")
    parser.add_argument("--async-efuse", action="store_true", help = "Generate asynchronous eFuse.")
    parser.add_argument("--ncpus", type = int, default = 1, help = "Number of CPU threads to use in KLayout & Xyce, default = 1.")
    parser.add_argument("--skip-drclvs", action="store_true", help = "Skip DRC & LVS checks.")
    parser.add_argument("--verbose", action="store_true",   help = "Debug level output verbosity.")
    parser.add_argument("--xyce-netlist", type = str, default = "pex", choices=["none", "schematic", "extracted", "pex", "all"],
        help = "Run Xyce tests with specified netlist, default = pex."
    )
    parser.add_argument("--digital-wrapper", type = str, default = "none", choices=["none", "wishbone", "spi", "async"],
        help = "Generate digital wrapper with Librelane, default = none."
    )
    parser.add_argument("--digital-depth", type = int, default = None, help = "Depth of digital memory block.")
    parser.add_argument("--digital-width", type = int, default = None, help = "Width of digital memory block.")
    args = parser.parse_args()
    
    root_dir = Path(__file__).parent.absolute() 
    
    if not args.digital_width:
        args.digital_width = args.word_width    

    if not args.digital_depth:
        args.digital_depth = args.number_of_words

    # run the flow
    flow = EfuseFlow(args.number_of_words, args.word_width, root_dir, args.xyce_netlist, args.async_efuse,
        (args.digital_wrapper, args.digital_depth, args.digital_width),
        args.ncpus, args.skip_drclvs, args.verbose
    )
    flow.run_flow()
    
    
if __name__ == '__main__':
    main()
