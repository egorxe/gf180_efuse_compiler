"""Xyce eFuse tests generators reside here."""

import random
import logging
from math import log2
from .xyce_test_runner import XyceTestRunner

TRANSITION_TIME     = 0.5e-9
SETUP_TIME          = 13e-9
PRESET_TIME         = 1e-9
BITSEL_TIME         = 10e-9
SENSE_TIME          = 10e-9
PROG_TO_SEL_TIME    = 10e-9
PROG_TIME           = 100e-9
EFUSE_BLOW_CURRENT  = 12e-3
EFUSE_SAFE_CURRENT  = 1e-3

class EfuseTestRunner(XyceTestRunner):
    """
    Helper class based on XyceTestRunner to run the tests on different eFuse netlists.
    """
    def __init__(self, nwords : int, word_width : int, tb : str, netlist : str, uut_file : str, is_flat : bool, vdd : float, ncpus : int = 1):
        self.nwords = nwords
        self.word_width = word_width
        self.max_word_val = 2**self.word_width - 1
        self.is_flat = is_flat

        self.init_memory()

        super().__init__(tb, netlist, uut_file, vdd, TRANSITION_TIME, ncpus)
        logging.getLogger(__name__)

        # patch flat netlist with parameters
        if is_flat:
            self.regexp_patch(self.netlist, r"^X(\d+)( .* efuse)$", r"X\1\2 PARAMS: NUM=\1")

        # create empty list for references to test funtions
        self.tests = []

    def init_memory(self):
        """ 
        Create test memory array and empty blown map
        """
        self.memory = [0] * self.nwords
        self.blown_map = {0 : 0}

    def fuse_num(self, s : str):
        """
        Get fuse number based on subcircuit hierarchy.
        """
        s = s.split(":")
        if self.is_flat:
            return int(s[1][1:])
        else:
            return int(s[1][1:])*1000 + int(s[2][1:])

    def add_to_blown_map(self, num):
        """
        Add fuse to a map of blown fuses to form a blown.map table.
        """
        logging.debug("Blown " + str(num))
        self.blown_map[num] = 1
        # mark previous and next with 0 if not present already, 0th element is always present
        if num+1 not in self.blown_map:
            self.blown_map[num+1] = 0
        if num-1 not in self.blown_map:
            self.blown_map[num-1] = 0


    def check_fuse_currents(self, blow_allowed : bool = True):
        """
        Check maximum currents flowing via each eFuse to determine which of them will be blown.
        """
        currents = self.get_max_currents()
        logging.debug("Blown fuses:")
        for c in currents:
            sc = self.fuse_num(c[0])
            if blow_allowed and (c[1] > EFUSE_BLOW_CURRENT):
                self.add_to_blown_map(sc)
            elif c[1] > EFUSE_SAFE_CURRENT:
                # assert False, f"Forbidden current level {c[1]} via fuse {sc} at time {c[2]} in test {self.test_name}"
                logging.warning(f"Forbidden current level {c[1]} via fuse {sc} at time {c[2]} in test {self.test_name}")

    def dump_memory(self):
        """
        Test memory array dump for debugging.
        """
        logging.debug("############### Memory dump ###############")
        for i in range(self.nwords):
            logging.debug(f"{i:04d} : {self.memory[i]:016x}")
        logging.debug("###########################################")

    def run_tests(self) -> bool:
        """
        Run the test. Return True if everything have finished without errors.
        """
        for test in self.tests:
            try:
                test()
                self.reset()
            except AssertionError as e:
                logging.error(e)
                return False
            return True

class EfuseArrayTest(EfuseTestRunner):
    """
    Class based on EfuseTestRunner to run the tests on eFuse array netlists.
    """
    def __init__(self, nwords : int, word_width : int, tb : str, netlist : str, uut_file : str, is_flat : bool, vdd : float, ncpus : int = 1):
        super().__init__(nwords, word_width, tb, netlist, uut_file, is_flat, vdd, ncpus)
        self.tests.append(self.full_range_test)

    def new_test_run(self, test_name : str):
        """
        Prepare new test run keeping memory contents.
        """
        # start from the begining
        super().new_test_run(test_name)

        # create tb drivers
        self.preset_n = self.create_driver("PRESET_N", True)
        self.sense = self.create_driver("SENSE", False)
        self.col_prog_n = self.create_bus_driver("COL_PROG_N", self.word_width, self.max_word_val)
        self.bit_sel = self.create_bus_driver("BIT_SEL", self.nwords, 0)

        self.write_table_include("blown.map", self.blown_map)

    def perform_efuse_read(self, word_addr : int, sleep : float = 0.0):
        """
        Generate PWL sequence for eFuse read.
        """
        # create pwl data
        self.set(self.preset_n, False)
        self.wait_for(PRESET_TIME)
        self.set(self.sense, True)
        self.wait_for(SENSE_TIME)
        self.set(self.preset_n, True)
        self.set(self.bit_sel, 1<<word_addr)
        self.wait_for(BITSEL_TIME)
        self.set(self.sense, False)
        self.set(self.bit_sel, 0)

        # check read val after simulation
        self.add_check("OUT", self.word_width, self.memory[word_addr])

        self.wait_for(sleep)

    def perform_efuse_write(self, word_addr : int, data : int, sleep : float = 0.0):
        """
        Generate PWL sequence for eFuse write.
        """
        # create pwl data
        self.set(self.bit_sel, 1<<word_addr)
        self.wait_for(PROG_TO_SEL_TIME)
        self.set(self.col_prog_n, self.max_word_val - data)  # binary negated data
        self.wait_for(PROG_TIME)
        self.set(self.bit_sel, 0)
        self.set(self.col_prog_n, self.max_word_val)
        
        self.wait_for(sleep)

        self.memory[word_addr] = data

    def full_range_test(self):
        """
        Simple eFuse test which first fills whole array with random data and reads ant verifies it afterwards.
        To simulate blown fuses we patch the netlist inbetween tests based on maximum current level through fuse.
        """
        # write all memory
        self.new_test_run("xyce_full_write")
        self.wait_for(10e-9)
        for i in range(self.nwords):
            self.perform_efuse_write(i, random.randrange(self.max_word_val+1), random.randrange(10,100)*0.1e-9)
        self.simulate_and_check()
        self.check_fuse_currents()
        self.dump_memory()

        # read all memory
        self.new_test_run("xyce_full_read")
        self.wait_for(10e-9)
        for i in range(self.nwords):
            self.perform_efuse_read(i, random.randrange(10,100)*0.1e-9)
        self.simulate_and_check()
        self.check_fuse_currents(False)


class EfuseArrayAsyncTest(EfuseTestRunner):
    """
    Class based on EfuseTestRunner to run the tests on async eFuse array netlists.
    """
    def __init__(self, nwords : int, word_width : int, tb : str, netlist : str, uut_file : str, is_flat : bool, vdd : float, ncpus : int = 1):
        super().__init__(nwords, word_width, tb, netlist, uut_file, is_flat, vdd, ncpus)
        self.tests.append(self.async_wrapper_tests)

        # remove antenna diodes
        self.regexp_patch(self.netlist, r"^D", r"*D")

    def new_test_run(self, test_name : str):
        """
        Prepare new test run keeping memory contents.
        """
        # start from the begining
        super().new_test_run(test_name)

        # create tb drivers
        self.reset_n = self.create_driver("RESET_N", False)
        self.prog = self.create_bus_driver("PROG", self.word_width, 0)

        self.write_table_include("blown.map", self.blown_map)

    def perform_efuse_read(self, sleep : float = 0.0):
        """
        Generate PWL sequence for async eFuse read.
        """
        # read is automatic after reset

        # check read val after simulation
        self.add_check("OUT", self.word_width, self.memory[0])

        self.wait_for(sleep)

    def perform_efuse_write(self, data : int, sleep : float = 0.0):
        """
        Generate PWL sequence for async eFuse write.
        """
        # create pwl data
        self.set(self.prog, data)  # binary negated data
        self.wait_for(PROG_TIME)
        self.set(self.prog, 0)
        
        self.wait_for(sleep)

        self.memory[0] = data

    def do_reset(self):
        self.wait_for(100e-9)
        self.set(self.reset_n, True)
        self.wait_for(10e-9)

    def async_wrapper_test(self, num : int = 0):
        """
        Simple async eFuse test which writes eFuse cell, resets and reads the result. 
        """
        # write eFuse
        self.new_test_run(f"xyce_async_write_{num}")
        self.do_reset()
        self.wait_for(100e-9)
        self.perform_efuse_write(random.randrange(self.max_word_val+1), random.randrange(10,100)*0.1e-9)
        self.simulate_and_check()
        self.check_fuse_currents()
        self.dump_memory()

        # read eFuse
        self.new_test_run(f"xyce_async_read_{num}")
        self.do_reset()
        self.wait_for(10e-9)
        self.perform_efuse_read(random.randrange(10,100)*0.1e-9)
        self.simulate_and_check()
        self.check_fuse_currents(False)

    def async_wrapper_tests(self):
        """
        Perform several tests with random values
        """
        for i in range(4):
            self.init_memory()
            self.async_wrapper_test(i)


class EfuseWbTest(EfuseTestRunner):
    """
    Class based on EfuseTestRunner to run the tests on eFuse with Wishbone interface netlists.
    """
    def __init__(self, nwords : int, word_width : int, clock_period : float, tb : str, netlist : str, uut_file : str, is_flat : bool, vdd : float, ncpus : int = 1):
        super().__init__(nwords, word_width, tb, netlist, uut_file, is_flat, vdd, ncpus)

        self.addr_width = int(log2(self.nwords))
        self.clock_period = clock_period

        self.tests.append(self.wb_single_test)

        # remove antenna diodes
        self.regexp_patch(self.netlist, r"^D", r"*D")

    def new_test_run(self, test_name : str):
        """
        Prepare new test run keeping memory contents.
        """
        # start from the begining
        super().new_test_run(test_name)

        # patch flat netlist with parameters
        if self.is_flat:
            self.regexp_patch(self.uut_file, r"^X(\d+)( .* efuse)", r"X\1\2 PARAMS: NUM=\1")

        # create tb drivers
        self.preset_n = self.create_driver("write_enable_i", True)
        self.wb_clk_i = self.create_driver("wb_clk_i", False)
        self.wb_rst_i = self.create_driver("wb_rst_i", True)
        self.wb_cyc_i = self.create_driver("wb_cyc_i", False)
        self.wb_stb_i = self.create_driver("wb_stb_i", False)
        self.wb_we_i  = self.create_driver("wb_we_i", False)
        self.wb_adr_i = self.create_bus_driver("wb_adr_i", self.addr_width, 0)
        self.wb_sel_i = self.create_driver("wb_sel_i", 0)
        self.wb_dat_i = self.create_bus_driver("wb_dat_i", self.word_width, 0)

        self.write_table_include("blown.map", self.blown_map)

    def clock_ticks(self, nclocks : int = 1):
        hp = self.clock_period/2-2*TRANSITION_TIME
        for i in range(nclocks):
            self.wait_for(SETUP_TIME)
            self.set(self.wb_clk_i, True)
            self.wait_for(hp)
            self.set(self.wb_clk_i, False)
            self.wait_for(hp-SETUP_TIME)

    def wb_reset(self):
        self.clock_ticks(4)
        self.set(self.wb_rst_i, False)
        self.clock_ticks(1)

    def perform_wb_read(self, addr : int, sleep : int = 1):
        """
        Generate PWL sequence for Wishbone read.
        """
        # create pwl data
        self.set(self.wb_adr_i, addr)
        self.set(self.wb_cyc_i, True)
        self.set(self.wb_stb_i, True)
        self.set(self.wb_we_i, False)
        self.clock_ticks(3)

        # check read val after simulation
        self.checks.append((self.time, "wb_ack_o", 1, 1))
        self.checks.append((self.time, "wb_dat_o", self.word_width, self.memory[addr]))

        self.set(self.wb_cyc_i, False)
        self.set(self.wb_stb_i, False)

        self.clock_ticks(sleep)

    def perform_efuse_write(self, addr : int, data : int, sleep : int = 1):
        """
        Generate PWL sequence for Wishbone read.
        """
        # create pwl data
        self.set(self.wb_adr_i, addr)
        self.set(self.wb_dat_i, data)
        self.set(self.wb_sel_i, (1<<(self.word_width//8))-1)
        self.set(self.wb_cyc_i, True)
        self.set(self.wb_stb_i, True)
        self.set(self.wb_we_i, True)
        self.clock_ticks(1002)

        # check read val after simulation
        self.checks.append((self.time, "wb_ack_o", 1, 1))

        self.set(self.wb_cyc_i, False)
        self.set(self.wb_stb_i, False)
        self.set(self.wb_we_i, False)

        self.clock_ticks(sleep)
        
        self.memory[addr] = data

    def wb_single_test(self):
        """
        Wishbone digital wrapper for eFuse array test. Takes very long time, so only single write & read is simulated.
        To simulate blown fuses we patch the netlist inbetween tests based on maximum current level through fuse.
        """
        # write wb memory
        self.new_test_run("xyce_wb_write")
        self.wb_reset()
        self.perform_efuse_write(29, random.randrange(self.max_word_val+1))
        self.simulate_and_check()
        self.check_fuse_currents()
        self.dump_memory()

        # read wb  memory
        self.new_test_run("xyce_wb_read")
        self.wb_reset()
        self.perform_wb_read(29)
        self.simulate_and_check()
        self.check_fuse_currents(False)

