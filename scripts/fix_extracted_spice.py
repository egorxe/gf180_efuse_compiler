#!/usr/bin/env python3
#
# This script inserts resistors emulating eFuses after Magic PEX.

import re
import sys

LINE_SEL_NMOS = "nmos_6p0 w=50u l=0.7u"
VSS_NET = "VSS"
EFUSE_RES = 200

SUBC_PATTERN = r'X[^\s\\]+'
NET_PATTERN = r'[^\s\\]+'
DIODE_PATTERN = r'^D[\d]+ .*'

fin = open(sys.argv[1], "r")
fout = open(sys.argv[2], "w")

nmos_pattern = re.compile("^\s*(" + SUBC_PATTERN + ") (" + NET_PATTERN + ") (" 
    + NET_PATTERN + ") (" + NET_PATTERN + ") (" + NET_PATTERN + ") " + LINE_SEL_NMOS, flags=re.IGNORECASE)
diode_pattern = re.compile(DIODE_PATTERN)

efuse_cnt = 0

for line in fin:
    # search for line select NMOS transistors
    res = re.search(nmos_pattern, line)
    copy_line = True
    if res:
        # patch nmos line inserting net to EFUSE
        efuse_net = "efuse_net_" + str(efuse_cnt)
        if res.group(2) == VSS_NET:
            line = res.group(1) + " " + res.group(2) + " " + res.group(3) + " " + efuse_net + " " + res.group(5) + " " + LINE_SEL_NMOS + "\n"
            nmos_net = res.group(4)
        else:
            assert(res.group(4) == VSS_NET)
            line = res.group(1) + " " + efuse_net + " " + res.group(3) + " " + res.group(4) + " " + res.group(5) + " " + LINE_SEL_NMOS + "\n"
            nmos_net = res.group(2)
        fout.write("RFUSE" + str(efuse_cnt) + " " + nmos_net + " " + efuse_net + " " + str(EFUSE_RES) + "\n")
        efuse_cnt += 1
    res = re.search(diode_pattern, line)
    if res:
        copy_line = False
    
    if copy_line:
        fout.write(line)

print("Patched", efuse_cnt, "eFuses")
