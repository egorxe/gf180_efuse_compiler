#!/usr/bin/env python3

import sys

EFUSE_CUR_LIMIT = 1e-4
VOL_VARS = 12

fname = sys.argv[1]

f = open(fname, 'r')
index = f.readline()

# Read index line
labels = index.split()[2:]

num_vals = len(labels)
dat = [ [] for _ in range(num_vals+1) ]
efuse_cur_vals = range(VOL_VARS+2, num_vals+2)
over_cur = []

# Read simulation data
for line in f:
    if line.startswith("End"):
        break
    values = [float(s) for s in line.split()]
    for i in range(num_vals+2):
        val = i
        if i in efuse_cur_vals and abs(values[val]) > EFUSE_CUR_LIMIT:
            
            if not (val in over_cur):
                print(values[val], "A ", labels[i-2], "(", i, ") at", values[1])
                over_cur.append(val)

