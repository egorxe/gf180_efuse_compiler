#!/usr/bin/env python3
#
# Generate eFuse array SPICE netlists for LVS & simulation
#

import os
import sys
import json
from pathlib import Path

def write_magic_ports(filename : str, ports : str):
    port_list = ports.split(" ")
    with open(filename, "w") as f:
        for i,p in enumerate(port_list):
            if p.strip():
                print(f"""port {{{p}}} index {1000+i}""", file=f)
            
def subcircuit(name : str, ports : str, body : str, params : str = "") -> str:
    if params:
        params = "PARAMS: " + params
    return f"""
.subckt {name} {ports} {params}
{body}
.ends
    """

def efuse_array_async(word_width : int, n_fuses : int, device_naming : list) -> str:
    assert(n_fuses==1)
    bitline_ports = "VSS VDD "
    for i in range(word_width):
        bitline_ports += f"COL_PROG_N[{i}] OUT[{i}] "
    bitline_ports += "SENSE PRESET_N "
    # write_magic_ports("efuse_array_ports.tcl", bitline_ports)
    body = ""
    for i in range(word_width):
        body += f"X{i} VSS VDD bitline[{i}] efuse_bitcell_async NUM={{LNUM*1000+{i}}}\n"
        
        # add programming PMOS
        body += f"""{device_naming[0]}prog0_{i} bitline[{i}] COL_PROG_N[{i}] VDD VDD p{device_naming[1]} L=0.50u W=62u nf=2\n"""
        body += f"""{device_naming[0]}prog1_{i} bitline[{i}] COL_PROG_N[{i}] VDD VDD p{device_naming[1]} L=0.50u W=62u nf=2\n"""
        # add sensamp
        body += f"Xsense{i} VSS VSS VDD PRESET_N OUT[{i}] SENSE bitline[{i}] efuse_senseamp\n"
    
    return subcircuit("efuse_array_async_1x8", bitline_ports, body, "")
    # return subcircuit("efuse_bitline_async", bitline_ports, body, "LNUM=0")

def efuse_async_mem(cellname : str, word_width : int, n_fuses : int, add_cells : str = "") -> str:
    assert(n_fuses==1)
    common_ports = "VSS VDD "
    array_ports = common_ports
    bitline_ports = common_ports
    body = add_cells

    for i in range(word_width):
        bitline_ports += f"COL_PROG_N[{i}] OUT[{i}] "
        array_ports += f"PROG[{i}] OUT[{i}] "

    array_ports += "RESET_N READY "
    bitline_ports += "SENSE PRESET_N "

    body += f"X0 {bitline_ports} efuse_array_async_1x8 LNUM=0\n"
    # body += f"X0 {bitline_ports} efuse_bitline_async LNUM=0\n"

    # add read-after-reset logic
    body += r"""
Xinv_res RESET_N RESET VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__inv_2
Xdel_resn0 RESET_N RESET_N_DEL0 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__dlyd_4
Xdel_resn1 RESET_N_DEL0 RESET_N_DEL1 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__dlyd_4
Xor_preset RESET RESET_N_DEL1 PRESET_N VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__or2_2

Xinv_resnd RESET_N_DEL1 RESET_DEL0 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__inv_2
Xdel_res0 RESET_DEL0 RESET_DEL1 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__dlyd_4
Xdel_res1 RESET_DEL1 RESET_DEL2 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__dlyd_4
Xand_sense RESET_N_DEL1 RESET_DEL2 SENSE_PREDEL VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__and2_2
Xdel_sense SENSE_PREDEL SENSE VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__dlyd_4
"""

    # add write inhibit logic
    for i in range(word_width):
        body += f"Xnand_wrinhibit{i} RESET_N PROG[{i}] COL_PROG_N[{i}] VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__nand2_2\n"

    write_magic_ports("efuse_array_ports.tcl", array_ports)
    
    return subcircuit(cellname, array_ports, body), array_ports

def generate_netlist(cellname : str, filename : str, nwords : int, word_width : int, klayout_lvs : bool = False, add_cells_dict : dict = {}):

    device_naming = ["X", "fet_06v0", "X0 ANODE VSS efuse NUM={NUM}"]

    # generate additional filler, cap & tie cells
    add_cells = ""
    acnt = 0
    for c in add_cells_dict:
        if all(x not in c for x in ["filltie", "endcap"]):
            for i in range(add_cells_dict[c]):
                add_cells += f"Xfill{acnt} VDD VDD VSS VSS {c}\n"
                acnt += 1

    if klayout_lvs:
        device_naming[0] = "M"
        device_naming[1] = "fet_05v0"
        device_naming[2] = "Rfuse ANODE VSS efuse R=200"
        async_mem = ""
    else:
        async_mem = f"{efuse_async_mem(cellname, word_width, nwords, add_cells)[0]}"
                
    netlist = f"""* eFuse array netlist with word_width={word_width}, nwords={nwords}

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__inv_1 I ZN VDD VNW VPW VSS
{device_naming[0]}0 ZN I VSS VPW n{device_naming[1]} W=8.2e-07 L=6e-07  
{device_naming[0]}1 ZN I VDD VNW p{device_naming[1]} W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__inv_2 I ZN VDD VNW VPW VSS
{device_naming[0]}00 ZN I VSS VPW n{device_naming[1]} W=8.2e-07 L=6e-07
{device_naming[0]}01 VSS I ZN VPW n{device_naming[1]} W=8.2e-07 L=6e-07
{device_naming[0]}10 ZN I VDD VNW p{device_naming[1]} W=1.22e-06 L=5e-07
{device_naming[0]}11 VDD I ZN VNW p{device_naming[1]} W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__fillcap_4 VDD VNW VPW VSS
{device_naming[0]}17 net_1 net_0 VSS VPW n{device_naming[1]} W=8.2e-07 L=1e-06
{device_naming[0]}19 VDD net_1 net_0 VNW p{device_naming[1]} W=1.22e-06 L=1e-06
.ENDS

.subckt efuse_bitcell_async VSS VDD ANODE PARAMS: NUM=-1
{device_naming[2]}
.ends

.subckt efuse_senseamp VSS VPW VDD PRESET_N OUT SENSE FUSE
{device_naming[0]}2 net1 PRESET_N VDD VDD p{device_naming[1]} L=0.5u W=2.44u nf=2
X1 net2 OUT VDD VDD VPW VSS  gf180mcu_fd_sc_mcu7t5v0__inv_1
X2 net1 net2 VDD VDD VPW VSS gf180mcu_fd_sc_mcu7t5v0__inv_1
X3 net2 net1 VDD VDD VPW VSS gf180mcu_fd_sc_mcu7t5v0__inv_1
{device_naming[0]}1 net1 SENSE FUSE VPW n{device_naming[1]} L=0.60u W=0.82u
.ends

{efuse_array_async(word_width, nwords, device_naming)}
{async_mem}
.end
    """

    with open(filename, "w") as f:
        f.write(netlist)

def pwl_from_file(name : str, buf : int):
    return f"""V{name} {name}_prebuf 0 PWL FILE "{name}.pwl"
X{name}_buf {name}_prebuf {name} VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__buf_{buf}
"""
    
def constant_driver(name : str, value : float):
    return f"""V{name} {name} 0 {value}\n"""

def gen_pwl_bus(name : str, size : int, buf : int):
    return "".join([pwl_from_file(f'{name}[{i}]', buf) for i in range(0, size)])

def generate_xyce_test(cellname : str, filename : str, spice_name : str, xyce_models_path : str, nwords : int, word_width : int, time : float = 100, vdd : float = 5.0):
    array_ports = efuse_async_mem(cellname, word_width, nwords)[1]
    netlist = f"""* Xyce testbench for {cellname}
.option TEMP=25.0
.include "blown.map"

{constant_driver("VSS", 0)}
{constant_driver("VDD", vdd)}

.lib "{xyce_models_path}/design.xyce" typical
.lib "{xyce_models_path}/sm141064.xyce" typical

.SUBCKT efuse ANODE CATHODE PARAMS: PBLOW=0 NUM=-1
.PARAM BLOWN='IF(NUM<0 , PBLOW, BLOWN_MAP(NUM))'
Rfuse ANODE CATHODE R='200*(1-BLOWN) + 20000*BLOWN'
.ENDS efuse

.include {spice_name}

Xefuse_array {array_ports} {cellname}

* buffers to model drive strength
.SUBCKT gf180mcu_fd_sc_mcu7t5v0__buf_1 I Z VDD VNW VPW VSS
X_i_2 VSS I Z_neg VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_0 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_3 VDD I Z_neg VNW pfet_06v0 W=5.65e-07 L=5e-07
X_i_1 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__buf_2 I Z VDD VNW VPW VSS
X_i_2 VSS I Z_neg VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_0 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_1 VSS Z_neg Z VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_3 VDD I Z_neg VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_0 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_1 VDD Z_neg Z VNW pfet_06v0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__buf_8 I Z VDD VNW VPW VSS
X_i_2_0 Z_neg I VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_2_1 VSS I Z_neg VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_2_2 Z_neg I VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_2_3 VSS I Z_neg VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_0 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_1 VSS Z_neg Z VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_2 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_3 VSS Z_neg Z VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_4 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_5 VSS Z_neg Z VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_6 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_7 VSS Z_neg Z VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_3_0 Z_neg I VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_3_1 VDD I Z_neg VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_3_2 Z_neg I VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_3_3 VDD I Z_neg VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_0 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_1 VDD Z_neg Z VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_2 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_3 VDD Z_neg Z VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_4 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_5 VDD Z_neg Z VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_6 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_7 VDD Z_neg Z VNW pfet_06v0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__or2_2 A1 A2 Z VDD VNW VPW VSS
X_i_2 Z_neg A1 VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_3 VSS A2 Z_neg VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_0 Z Z_neg VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_1 VSS Z_neg Z VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_4 net_0 A1 Z_neg VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_5 VDD A2 net_0 VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_0 Z Z_neg VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_1_1 VDD Z_neg Z VNW pfet_06v0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__nand2_2 A1 A2 ZN VDD VNW VPW VSS
X_i_1_1 net_0_0 A2 VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_1 ZN A1 net_0_0 VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_0_0 net_0_1 A1 ZN VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_1_0 VSS A2 net_0_1 VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_3_1 ZN A2 VDD VNW pfet_06v0 W=1.13e-06 L=5e-07
X_i_2_1 VDD A1 ZN VNW pfet_06v0 W=1.13e-06 L=5e-07
X_i_2_0 ZN A1 VDD VNW pfet_06v0 W=1.13e-06 L=5e-07
X_i_3_0 VDD A2 ZN VNW pfet_06v0 W=1.13e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__and2_2 A1 A2 Z VDD VNW VPW VSS
X_i_2 net_0 A1 Z_neg VPW nfet_06v0 W=8.15e-07 L=6e-07
X_i_3 VSS A2 net_0 VPW nfet_06v0 W=8.15e-07 L=6e-07
X_i_0_0 Z Z_neg VSS VPW nfet_06v0 W=8.15e-07 L=6e-07
X_i_0_1 VSS Z_neg Z VPW nfet_06v0 W=8.15e-07 L=6e-07
X_i_4 Z_neg A1 VDD VNW pfet_06v0 W=1.07e-06 L=5e-07
X_i_5 VDD A2 Z_neg VNW pfet_06v0 W=1.07e-06 L=5e-07
X_i_1_0 Z Z_neg VDD VNW pfet_06v0 W=1.215e-06 L=5e-07
X_i_1_1 VDD Z_neg Z VNW pfet_06v0 W=1.215e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__dlyd_4 I Z VDD VNW VPW VSS
X_i_2_0 Z_neg I VSS VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_2 net_7 Z_neg net_1 VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_3 net_1 Z_neg VSS VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_2_26 net_9 net_7 net_13 VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_3_30 net_13 net_7 VSS VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_2_0_1 net_15 net_9 net_11 VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_3_4 net_11 net_9 VSS VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_2_26_13 net_16 net_15 net_18 VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_3_30_34 net_18 net_15 VSS VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_2_0_10 net_14 net_16 net_19 VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_3_4_49 net_19 net_16 VSS VPW nfet_06v0 W=3.6e-07 L=6e-07
X_i_2_21 net_3 net_14 net_6 VPW nfet_06v0 W=3.65e-07 L=6e-07
X_i_3_6 net_6 net_14 VSS VPW nfet_06v0 W=3.65e-07 L=6e-07
X_i_2_0_18 Z net_3 VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_2_0_18_1 Z net_3 VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_2_0_18_2 Z net_3 VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_2_0_18_1_15 Z net_3 VSS VPW nfet_06v0 W=8.2e-07 L=6e-07
X_i_3_0 Z_neg I VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_0 net_0 Z_neg VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_1 net_7 Z_neg net_0 VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_0_35 net_12 net_7 VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_1_47 net_9 net_7 net_12 VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_0_9 net_10 net_9 VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_1_22 net_15 net_9 net_10 VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_0_35_50 net_17 net_15 VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_1_47_46 net_16 net_15 net_17 VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_0_9_2 net_20 net_16 VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_1_22_38 net_14 net_16 net_20 VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_0_29 net_5 net_14 VDD VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_1_39 net_3 net_14 net_5 VNW pfet_06v0 W=3.6e-07 L=5e-07
X_i_3_0_0 Z net_3 VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_3_0_0_14 Z net_3 VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_3_0_0_34 Z net_3 VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
X_i_3_0_0_14_19 Z net_3 VDD VNW pfet_06v0 W=1.22e-06 L=5e-07
.ENDS

{gen_pwl_bus("PROG", word_width, 8)}
{pwl_from_file("RESET_N", 2)}

.tran 10ps {time}
* serial solver is more efficient even for large arrays
.OPTIONS LINSOL TYPE=KLU

.print tran format=csv file={filename}.csv V(RESET_N) V(OUT*) V(PROG*) I(Xefuse_array:X*:RFUSE)
    """
    
    with open(filename, "w") as f:
        f.write(netlist)

def generate_spices_async(base_name : str, pdk_path : str, nwords : int, word_width : int, time : float = 100e-9, add_cells : Path | str = ""):
    """
    Generate a basic set of SPICE files - simulation & LVS netlists and Xyce test wrapper.
    """
    xyce_models_path = f"{pdk_path}/libs.tech/xyce/"

    spice_name = base_name + ".spice"
    lvs_name = base_name + ".klvs.spice"
    tb_name = base_name + "_test.xyce"

    if add_cells:
        with open(add_cells, "r") as f:
            add_cells_dict = json.load(f)
    else:
        add_cells_dict = {}

    generate_netlist(base_name, spice_name, nwords, word_width, False)
    generate_netlist(base_name, lvs_name, nwords, word_width, True, add_cells_dict)
    generate_xyce_test(base_name, tb_name, spice_name, xyce_models_path, nwords, word_width, time)

    return spice_name, lvs_name, tb_name

########## MAIN ########## 

def usage():
    print("Usage:", sys.argv[0], "bitlines bits_per_bitline")
    print("PDK_ROOT environmental variable must point to the directory containing gf180mcu PDK")
    sys.exit(1)

def main():
    try:
        nwords = int(sys.argv[1])
        word_width = int(sys.argv[2])
    except Exception:
        usage()

    base_name = f"efuse_array_{nwords}x{word_width}"

    if "PDK_ROOT" not in os.environ or "PDK" not in os.environ:
        usage()
    pdk_path = os.environ["PDK_ROOT"] + "/" + os.environ["PDK"]

    generate_spices_async(base_name, pdk_path, nwords, word_width, 1000)


if __name__ == '__main__':
    main()



