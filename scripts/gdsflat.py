#!/usr/bin/env python3
#
# This script flats the GDS using KLayout and removes all texts aside from ones on top level.
# This is required for proper Magix PEX.

import pya
import sys

labels = [(34, 10), (36, 10), (42, 10), (46, 10), (81, 10)] # List of label layers

Lay = pya.Layout()

if len(sys.argv) < 2:
    print("usage: python3 gdsflat.py file.gds [output.gds]")
Lay.read(sys.argv[1])

outfile = "output.gds" if len(sys.argv) < 3 else sys.argv[2]

assert len(Lay.top_cells()) == 1

top_cell = Lay.top_cells()[0] # Get the top cell instance

label_layers = [Lay.layer(*l) for l in labels]
"""
for cell_idx in top_cell.each_child_cell(): # Iterate over all subcells
    cell = Lay.cell(cell_idx)
    cell.flatten(-1, 1) # Flatten subcell
    continue
    for label_layer in label_layers:
        for s in cell.shapes(label_layer).each(): # Iterate over all shapes and delete texts
            if s.is_text():
                s.delete()
"""
top_cell.flatten(1) # Flatten top cell
top_cell.name = "efuse_array"

Lay.transform(pya.Trans(pya.Vector(-top_cell.bbox().left, -top_cell.bbox().bottom))) # Move cell to (0,0)

Lay.write(outfile)

