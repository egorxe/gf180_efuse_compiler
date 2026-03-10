""" Helper classes for running tests in Xyce simulation."""

import os
import re
import shutil
import csv
import subprocess as sp
from pathlib import Path

class DigitalPwlDriver:
    """
    Create PWL file to drive "digital" inputs in Xyce.
    """
    def __init__(self, name : str, vdd : float, initial : bool, transition : float = 0.1):
        self.name = name
        self.vdd = vdd
        self.state = int(initial)
        self.transition = transition
        self.last_switch_time = 0
        self.pwl_data = ""
        self.add_pwl(self.state, 0)

    def add_pwl(self, state : int, time : float):
        self.pwl_data += f"{time} {str(state * self.vdd)}\n"

    def set(self, state : bool, time : float):
        assert(time >= self.last_switch_time)
        new_state = int(state)
        if new_state != self.state:
            self.add_pwl(self.state, time)
            ttime = time + self.transition
            self.add_pwl(new_state, ttime)
            self.state = new_state
            self.last_switch_time = ttime

    def write_pwl(self):
        with open(f"{self.name}.pwl", "w") as f:
            f.write(self.pwl_data)


class DigitalPwlBus:
    """
    Create PWL files to drive multibit "digital" buses in Xyce.
    """
    def __init__(self, name : str, wdt : int, vdd : float, initial : int, transition : float = 0.1):
        self.bits = []
        self.wdt = wdt
        assert(initial < 2**wdt)
        for i in range(wdt):
            self.bits.append(DigitalPwlDriver(f"{name}[{i}]", vdd, bool(initial & (1<<i)), transition))

    def set(self, state : int, time : float):
        assert(state < 2**self.wdt)
        for i in range(self.wdt):
            self.bits[i].set(bool(state & (1<<i)), time)

    def write_pwl(self):
        for b in self.bits:
            b.write_pwl()

class XyceTestRunner:
    """
    Base class to create test sequences in PWL files, run Xyce simulation 
    and analize simulation waveforms afterwards.
    """
    def __init__(self, tb : str, netlist : str, uut_file : str, vdd : float, transition : float, ncpus : int = 1):
        self.vdd = vdd
        self.tb = tb
        self.netlist = netlist
        self.uut_file = uut_file
        self.transition = transition
        self.ncpus = ncpus
        self.orig_wd = os.getcwd()
        self.reset()

    @staticmethod 
    def regexp_patch(file : str, regex : str, sub : str):
        with open(file, "r") as f:
            patched = re.sub(regex, sub, f.read(), flags = re.M | re.I)
        with open(file, "w") as f:
            f.write(patched)

    def reset(self):
        """
        Reset sim state.
        """
        # start from the begining
        self.time = 0
        self.checks = []
        self.simlog = []
        self.simlog_ptr = 0
        self.simlog_dict = {}
        self.drivers = []

        os.chdir(self.orig_wd)

    def new_test_run(self, test_name : str):
        """
        Prepare new test run.
        """
        self.reset()
        self.test_name = test_name
        os.makedirs(self.test_name, exist_ok=True)
        shutil.copy(self.tb, self.test_name)
        shutil.copy(self.netlist, Path(self.test_name) / self.uut_file)
        self.run_tb = (Path(self.test_name) / Path(self.tb).name).absolute()
        os.chdir(self.test_name)

    def create_driver(self, name : str, initial : bool):
        """
        Create digital signal driver.
        """
        d = DigitalPwlDriver(name, self.vdd, initial, self.transition)
        self.drivers.append(d)
        return d

    def create_bus_driver(self, name : str, wdt : int, initial : int):
        """
        Create digital bus driver.
        """
        d = DigitalPwlBus(name, wdt, self.vdd, initial, self.transition)
        self.drivers.append(d)
        return d

    def wait_for(self, time : float):
        """
        Wait for some simulation time.
        """
        self.time += time

    def set(self, drv, val):
        """
        Signal setting helper.
        """
        drv.set(val, self.time)

    def prepare_sim(self):
        """
        Get ready to run the simulator.
        """
        # write all PWL files
        for d in self.drivers:
            d.write_pwl()

        # patch simulation time in testbench
        self.regexp_patch(self.run_tb, r"^\.tran (\d+)ps (?:\d+([.]\d*)?(?:e[+-]?\d+)?|[.]\d+(?:e[+-]?\d+)?)(.*)", f".tran \\1ps {self.time} \\2")

    def run_xyce_sim(self):
        """
        Run current test in Xyce simulator.
        """
        with open("xyce.log", "w") as log:
            try:
                run_list = ["Xyce", self.run_tb]
                if self.ncpus != 1:
                    run_list = ["mpirun", "-np", str(self.ncpus)] + run_list
                sp.run(run_list, stdout = log, stderr = sp.STDOUT, check = True)
            except Exception:
                raise AssertionError("Xyce run failed!")

    def read_simlog(self):
        """
        Read the simulation log in the csv format.
        """
        with open(Path(f"{self.run_tb}.csv")) as tb_csv:
            reader = csv.reader(tb_csv)
            header = next(reader)
            # construct simlog dict (TIME is always 0)
            for i,e in enumerate(header):
                self.simlog_dict[e] = i

            # read whole simlog
            for row in reader:
                self.simlog.append(row)

    def cur_simlog(self, i : int):
        """
        Get "current" value from simulation log by column number.
        """
        return float(self.simlog[self.simlog_ptr][i])

    def cur_simlog_voltage(self, n : str):
        """
        Get "current" voltage value from simulation log by name.
        """
        return self.cur_simlog(self.simlog_dict[f"V({n})"])

    def goto_simlog_time(self, time : float):
        """
        Find the specific time in simulation log (goes only forward!).
        """
        assert (time >= self.cur_simlog(0)), "Error during simulation log parsing."
        for i in range(self.simlog_ptr, len(self.simlog)):
            if float(self.simlog[i][0]) >= time:
                break
        self.simlog_ptr = i-1

    def volt_to_digital(self, n : str):
        """
        Voltage to digital value conversion.
        """
        volt = self.cur_simlog_voltage(n)
        if volt > 0.8 * self.vdd:
            return 1
        elif (volt < 0.1*self.vdd) and (volt > -0.01*self.vdd):
            return 0
        else:
            assert False, f"Digital signal {n} is in indeterminate state during test at time {self.cur_simlog(0)}!"

    def verify_signal_state(self, time : float, name : str, wdt : int, expected : int, is_bus : bool):
        """
        Check the simulation log to verify that the bus has an expected value at specific time.
        """
        self.goto_simlog_time(time)
        word = 0
        if is_bus:
            for i in range(wdt):
                word += self.volt_to_digital(f"{name.upper()}[{i}]") << i
        else:
            word += self.volt_to_digital(f"{name.upper()}")
        assert (word == expected), f"Word read from eFuse in simulation differs from expected in test {self.test_name}!"

    def write_table_include(self, fname : str, table : dict):
        """
        Write Xyce-format include containing a table for single parameter dependedn on other parameter.
        Quiet ugly, but tablefile supports only time parameter for some reason.
        """
        with open(fname, "w") as f:
            f.write(".FUNC BLOWN_MAP(X) {table(X\n")
            for i in sorted(table.items()):
                f.write(f"+, {i[0]}, {i[1]}\n")
            f.write("+)}")

    def get_max_currents(self):
        """
        Get maximum current value for each registered current probe.
        """
        currents = []
        for k in self.simlog_dict:
            if "I(" in k:
                currents.append([k, 0.0, 0.0])
        for row in self.simlog:
            for c in currents:
                cur_val = abs(float(row[self.simlog_dict[c[0]]]))
                if cur_val > c[1]:
                    c[1] = cur_val
                    c[2] = row[0]
        return currents

    def run_checks(self):
        """
        Perform all registered bus state checks.
        """
        for c in self.checks:
            self.verify_signal_state(c[0], c[1], c[2], c[3], c[4])

    def add_check(self, signal, wdt, val, is_bus : bool = True):
        """
        Add a check to verify signal state at current time.
        """
        self.checks.append((self.time, signal, wdt, val, is_bus))

    def simulate_and_check(self):
        """
        Run simulation and checks after it.
        """
        self.prepare_sim()
        self.run_xyce_sim()
        self.read_simlog()
        self.run_checks()
