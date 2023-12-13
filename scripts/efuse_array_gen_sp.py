N_BITLINES = 16
N_ANODES = 8
N_FILLCAP = 210

#N_BITLINES = 8
#N_ANODES = 4
#N_FILLCAP = 35

def efuse_byte(n_anodes: int):
    res = ".subckt efuse_byte "
    for i in range(n_anodes):
        res += f"ANODE_{i} "
    res += "VSS LINE_SEL\n"
    for i in range(n_anodes):
        res += f"x{i} LINE_SEL ANODE_{i} VSS efuse_bitcell\n"
    res += ".ends\n" 
    return res

def efuse_array(n_bitlines: int, n_anodes: int, n_fillcap: int):
    res = ".subckt efuse_array "
    for i in range(n_bitlines):
        res += f"LINE_{i} "
    res += "VDD VSS "
    for i in range(n_anodes):
        res += f"COL_{i}_PROG "
    res += "SENSE nPRESET "
    for i in range(n_anodes):
        res += f"DO_{i} "
    res += "\n"

    for i in range(n_bitlines):
        res += f"x0_{i} " + " ".join([f'net{j}' for j in range(n_anodes)]) + f" VSS LINE_{i}_buf efuse_byte\n"
        res += f"x4_{i} LINE_{i} LINE_{i}_buf VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__buf_1\n"

    for i in range(n_anodes):
        res += f"""
M{i} net{i} COL_{i}_PROG VDD VDD pmos_5p0 L=0.50u W=50u
"""
    res += "\n"
    for i in range(n_anodes):
        res += f"x1_{i} VDD nPRESET DO_{i}_buf SENSE VSS net{i} efuse_sense_amp\n"
        res += f"x3_{i} DO_{i}_buf DO_{i} VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__buf_1\n"

    for i in range(n_fillcap):
        res += f"x2_{i} VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__fillcap_4\n"

    res += ".ends\n"

    return res



netlist = f"""
* N_BITLINES={N_BITLINES}, N_ANODES={N_ANODES}
.SUBCKT gf180mcu_fd_sc_mcu7t5v0__inv_1 I ZN VDD VNW VPW VSS
M0 ZN I VSS VPW nmos_5p0 W=8.2e-07 L=6e-07  
M1 ZN I VDD VNW pmos_5p0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__inv_2 I ZN VDD VNW VPW VSS
M00 ZN I VSS VPW nmos_5p0 W=8.2e-07 L=6e-07
M01 VSS I ZN VPW nmos_5p0 W=8.2e-07 L=6e-07
M10 ZN I VDD VNW pmos_5p0 W=1.22e-06 L=5e-07
M11 VDD I ZN VNW pmos_5p0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__buf_1 I Z VDD VNW VPW VSS
M_i_2 VSS I Z_neg VPW nmos_5p0 W=3.6e-07 L=6e-07
M_i_0 Z Z_neg VSS VPW nmos_5p0 W=8.2e-07 L=6e-07
M_i_3 VDD I Z_neg VNW pmos_5p0 W=5.65e-07 L=5e-07
M_i_1 Z Z_neg VDD VNW pmos_5p0 W=1.22e-06 L=5e-07
.ENDS

.SUBCKT gf180mcu_fd_sc_mcu7t5v0__fillcap_4 VDD VNW VPW VSS
M17 net_1 net_0 VSS VPW nmos_5p0 W=8.2e-07 L=1e-06
M19 VDD net_1 net_0 VNW pmos_5p0 W=1.22e-06 L=1e-06
.ENDS

.subckt efuse_bitcell  select anode VSS
R0 anode net1 efuse R=200
M1 net1 select VSS VSS nmos_6p0 L=0.70u W=50u
.ends

.subckt efuse_sense_amp  VDD nPRESET OUT SENSE VSS FUSE
M2 net1 nPRESET VDD VDD pmos_5p0 L=0.50u W=1.9u
x1 net2 OUT VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__inv_2
x2 net1 net2 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__inv_1
x3 net2 net1 VDD VDD VSS VSS gf180mcu_fd_sc_mcu7t5v0__inv_1
M1 net1 SENSE FUSE VSS nmos_5p0 L=0.60u W=0.5u
.ends

{efuse_byte(N_ANODES)}
{efuse_array(N_BITLINES, N_ANODES, N_FILLCAP)}
.end"""
with open(f"efuse_array{N_BITLINES}x{N_ANODES}.sp", "w") as f:
    f.write(netlist)


