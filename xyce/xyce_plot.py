#!/usr/bin/env python3

import matplotlib.pyplot as plt
import sys

VOL_VARS = 12   #! number of voltages

if len(sys.argv) < 2:
    print("Usage: ", sys.argv[0], "xyce_output [names_of_additional_values_to_print ...]")
    sys.exit(1)

fname = sys.argv[1]

f = open(fname, 'r')
index = f.readline()

# Read index line
labels = index.split()[2:]
num_vals = min(len(labels), VOL_VARS) # draw only voltages

# Additional draw elements
add_draw = []
for i in range(len(labels)):
    for j in range(2, len(sys.argv)):
        if sys.argv[j] in labels[i]:
            add_draw.append(i)

# Read simulation data
dat = [ [] for _ in range(num_vals+1+len(add_draw)) ]
for line in f:
    if line.startswith("End"):
        break
    values = [float(s) for s in line.split()]
    for i,v in enumerate(list(range(num_vals+1)) + add_draw):
        if v <= VOL_VARS:     # ??
            j = 1+v
        else:
            j = 2+v
        dat[i].append(values[j])

# Plot
fig, ax = plt.subplots()
graphs = []
graphsd = {}

for i,v in enumerate(list(range(num_vals)) + add_draw):
    graphs.append(ax.plot(dat[0], dat[i+1], label = labels[v]))

# Make interactive
legend = ax.legend()
llines = legend.get_lines()
for i in range(len(llines)):
    llines[i].set_picker(True)
    llines[i].set_pickradius(8)
    graphsd[llines[i]] = graphs[i]

def on_pick(event):
    legend = event.artist
    isVisible = legend.get_visible()
    
    graphsd[legend][0].set_visible(not isVisible)
    legend.set_visible(not isVisible)

    fig.canvas.draw()

plt.connect('pick_event', on_pick)
plt.show()
