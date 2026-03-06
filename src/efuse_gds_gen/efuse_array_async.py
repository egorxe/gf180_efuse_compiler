#!/usr/bin/env python3

from klayout import db
import sys
import json
from pathlib import Path
from os import PathLike

from .gf180_klayout import *
from .cells.draw_mos import draw_pmos
from .cells.mos import mos_ld, mos_grw

# Design constants, sizes are in nm
NFUSES_PER_BLOCK    = 8
EFUSE_XSTEP         = 3000 
EFUSE_YOFF          = 590

PMOS_WDT            = 31000
PMOS_LEN            = 500
PMOS_FINGERS        = 4
PMOS_XOFF           = -400
PMOS_M1_STEP        = 1020
PMOS_VDD_WDT        = 2860
PMOS_YSTEP          = 5720
PMOS_YOFF           = 6340
PMOS_M1_WDT         = 380

BLOCK_XOFF          = -290
BLOCK_DG_PATCH      = 500

SENSAMP_XOFF        = -1160
SENSAMP_YOFF        = 0
SENSE_BIT_OVERLAP   = 1350

BITWIRE_UP_YOFF     = 3785
BITWIRE_DOWN_YOFF   = 1525
BITWIRE_WDT         = 810

BITLINE_YOFF        = -745

BITSEL_XOFF         = -2155
BITSEL_STEP         = -(M2_MIN_WDT + VIA_DIST)

BLOCK_VSS_WDT       = 2860
BLOCK_VSS_OFF       = 24000
CS_WIRE_MAX_OFF     = BLOCK_VSS_OFF - M2_DIST + M2_MIN_WDT - 50
SENSE_POWER_WDT     = 1000

CELL_RAIL_WDT       = 600

GATE_EXTEND         = 320

class ProgPmos(CellGf180mcu):
    """
    eFuse bitline programming PMOS transistor cell.
    """
    def __init__(self, layout):
        pmos_cell = draw_pmos(layout.layout, PMOS_LEN/1000, PMOS_WDT/1000, mos_ld, PMOS_FINGERS, mos_grw, "Bulk Tie", "5V", 0, 0)
        super().__init__(layout, pmos_cell)
        self.zero_origin()
        
        GATE_STEP = 1020
        pmos_m1_bbox = pmos_cell.bbox(self.l.metal1)
        pmos_poly_bbox = pmos_cell.bbox(self.l.poly2)
        
        for i in range(PMOS_FINGERS):
            self.create_box(self.l.poly2, pmos_poly_bbox.p1.x + i*GATE_STEP, pmos_poly_bbox.p1.y - GATE_EXTEND, pmos_poly_bbox.p1.x + PMOS_LEN + i*GATE_STEP, pmos_poly_bbox.p1.y)
        pmos_poly_bbox = pmos_cell.bbox(self.l.poly2)
            
        m1 = self.create_box(self.l.metal1, pmos_poly_bbox.p1.x, pmos_poly_bbox.p1.y, pmos_poly_bbox.p2.x, pmos_m1_bbox.p1.y - M1_DIST) 
        self.create_box(self.l.dualgate, pmos_poly_bbox.p1.x - DG_POLY_ENC - 280, pmos_poly_bbox.p1.y - DG_POLY_ENC, pmos_poly_bbox.p2.x + DG_POLY_ENC, pmos_poly_bbox.p1.y) 
        for i in range(PMOS_FINGERS):
            self.place_contact(m1.p1.x + CONTACT_POLY_OVERLAP + i*GATE_STEP, m1.p1.y + CONTACT_POLY_OVERLAP)
        self.create_text(self.l.metal1_label, m1.p2.x, m1.center().y, "COL_PROG_N")

class Efuse(CellGf180mcu):
    """
    Single eFuse cell.
    """
    def __init__(self, l : LayoutGf180mcu):
        super().__init__(l, parent = str(Path(__file__).parent / "cells/efuse_compact.gds"), name = "efuse_cell")
        self.zero_origin()

class EfuseSenseamp(CellGf180mcu):
    """
    eFuse bitline senseamp cell.
    """
    def __init__(self, l : LayoutGf180mcu):
        super().__init__(l, parent = str(Path(__file__).parent / "cells/efuse_senseamp_2.gds"), name = "efuse_senseamp_2")
        self.flatten()
        self.zero_origin()
        
class BitlineBlock(CellGf180mcu):
    """
    8 fuse basic async eFuse building block cell.
    """
    def __init__(self, l : LayoutGf180mcu, num_offset : int = 0):
        # create cell
        super().__init__(l, name = "efuse_bitline_block_"+str(num_offset))

        M1_M2_OVERLAP = 1100
        
        # create fuses with programming PMOSes
        efuse_cell = Efuse(l)
        pmos_cell = ProgPmos(l)
        for i in range(NFUSES_PER_BLOCK):
            # create fuse with vias on anode
            fuse = self.cell_inst(efuse_cell, i*EFUSE_XSTEP, 0, 3)
            fuse_bbox = fuse.bbox()
            fuse_m1_bbox = fuse.bbox(l.metal1)
            y = PMOS_YOFF+PMOS_YSTEP*(i)
            pmos = self.cell_inst(pmos_cell, PMOS_XOFF, y, 3)
            pmos_m1_bbox = pmos.bbox(l.metal1)
            pmos_bbox = pmos.bbox()
            for f in range(PMOS_FINGERS//2):
                self.create_text(l.metal1_label, pmos_bbox.center().x, pmos_m1_bbox.p1.y + 1150 + PMOS_M1_STEP*f*2, "VDD")
            for f in range(PMOS_FINGERS//2+1):
                self.create_text(l.metal1_label, pmos_bbox.center().x, pmos_m1_bbox.p1.y + 10 + PMOS_M1_STEP*f*2, f"pmos{i}")
            self.create_text(l.metal1_label, pmos_bbox.center().x, pmos_m1_bbox.p1.y + 1000 + PMOS_M1_STEP*PMOS_FINGERS//2*2, "VDD")
            prog = self.find_boxes_with_text_inst(l.metal1, l.metal1_label, "COL_PROG_N", pmos_cell, pmos)
            assert(len(prog)==1)
            self.create_text_p(l.metal1_label, prog[0].center(), f"COL_PROG_N[{i}]")

            y = fuse_m1_bbox.p2.y
            y2 = fuse_bbox.p2.y + M1_M2_OVERLAP//2
            m2y = fuse_bbox.p2.y - M1_M2_OVERLAP//2
            m2y2 = pmos_m1_bbox.p2.y
            m1_box = self.create_box(l.metal1, fuse_m1_bbox.p1.x, y, fuse_m1_bbox.p2.x, y2)
            m2_box = self.create_box(l.metal2, fuse_m1_bbox.p1.x, m2y, fuse_m1_bbox.p2.x, m2y2)
            self.create_text_p(l.metal2_label, m2_box.center(), f"ANODE[{i}]")
            self.place_via_area(m1_box & m2_box, 1, 2)

            # create M2 - pmos_drain_M1 vias
            pmos_con = self.find_boxes_with_text(l.metal1, l.metal1_label, f"pmos{i}")
            for c in pmos_con:
                self.place_via_area_step(m2_box & c, 1, 2, VIA_STEP, VIA_STEP, enlarge=True)
        
        # connect cathodes with VSS 
        cathodes = self.find_boxes_with_text(l.metal1, l.metal1_label, "CATHODE")
        assert(len(cathodes) == NFUSES_PER_BLOCK)
        vss = self.create_box(l.metal1, cathodes[0].p1.x, cathodes[0].p1.y - 1000, self.bbox(l.metal1).p2.x, cathodes[NFUSES_PER_BLOCK-1].p2.y)
        self.create_text(l.metal1_label, vss.center().x, vss.center().y, "VSS")
        # create M2 metal strip to discourage metal fill
        vss2 = self.create_box(l.metal2, cathodes[0].p1.x, cathodes[0].p1.y - 1000, cathodes[NFUSES_PER_BLOCK-1].p2.x, cathodes[NFUSES_PER_BLOCK-1].p2.y)
        self.dup_box(l.metal2, vss)
        self.place_via_area(vss & vss2, 1, 2)

        # cover fuses with M3-M5
        emk_bbox = self.bbox(l.efuse_mk)
        self.dup_box(l.metal3, emk_bbox)
        self.dup_box(l.metal4, emk_bbox)
        self.dup_box(l.metal5, emk_bbox)

# Efuse asyc bitline (actually word_width bitlines)
class EfuseBitline(CellGf180mcu):
    """
    eFuse bitline cell.
    """
    def __init__(self, l : LayoutGf180mcu, word_width : int = 8):
        # create cell
        super().__init__(l, name = "efuse_bitline")
        
        assert(word_width==8)
        
        # create basic 16 fuse blocks (up to 4)
        blocks = word_width // NFUSES_PER_BLOCK
        block_cells = []
        for b in range(blocks):
            block_cell = BitlineBlock(l, b * NFUSES_PER_BLOCK)
            block = self.cell_inst(block_cell, b * (block_cell.bbox(l.dualgate).width() + BLOCK_XOFF), 0, 0)
            block_cells.append(block)
  
        # create sensamps aligned in 2 stdcell lines
        bitwire_m3 = []
        sensamps = []
        presets = []
        senses = []
        sensamp_cell = EfuseSenseamp(l)
        senseamp_wdt = sensamp_cell.bbox(l.metal1).width()
        senseamp_height = sensamp_cell.bbox(l.metal1).height() - CELL_RAIL_WDT
        senseamp_x = self.bbox(l.metal1).p1.x + SENSAMP_XOFF - sensamp_cell.bbox().height()
        for i in range(word_width):
            odd = i%2
            if not odd:
                senseamp = self.cell_inst(sensamp_cell, senseamp_x-senseamp_height, SENSAMP_YOFF + senseamp_wdt*(i//2), 1)
            else:
                senseamp = self.cell_inst(sensamp_cell, senseamp_x, SENSAMP_YOFF + senseamp_wdt*(i//2), 3)
            sensamps.append(senseamp)
            # patch OUT labels
            out = self.find_boxes_with_text_inst(l.metal1, l.metal1_label, "OUT", sensamp_cell, senseamp)
            assert(len(out)==1)
            self.create_text_p(l.metal1_label, out[0].center(), f"OUT[{i}]")
            
            # create metal bit wires connecting each fuse with it's senseamp
            sense_bitwire = self.find_boxes_with_text_inst(l.metal1, l.metal1_label, "BITWIRE", sensamp_cell, senseamp)
            anode = self.find_boxes_with_text(l.metal2, l.metal2_label, f"ANODE[{i}]")
            assert(len(sense_bitwire)==1 and len(anode) == 1)
            anode = anode[0]
            sense_bitwire = sense_bitwire[0]
            y0 = anode.p2.y if odd else anode.p2.y - 2000
            wdt = 800
            m3h = self.create_box(l.metal3, anode.p2.x, y0, sense_bitwire.p1.x, y0 - wdt)
            m3v = self.create_box(l.metal3, m3h.p1.x, m3h.p1.y, m3h.p1.x + wdt, sense_bitwire.p2.y - wdt)
            self.place_via_area(anode & m3h, 2, 3)
            self.place_via_area(sense_bitwire & m3v, 1, 3)
            bitwire_m3 += [m3h, m3v]

            presets += self.find_boxes_with_text_inst(l.metal2, l.metal2_label, "PRESET_N", sensamp_cell, senseamp)
            senses += self.find_boxes_with_text_inst(l.metal2, l.metal2_label, "SENSE", sensamp_cell, senseamp)

        # draw PRESET & SENSE connection wires
        bbox = self.bbox()
        assert(len(presets) == word_width)
        self.create_box(l.metal2, presets[1].p1.x, bbox.p1.y, presets[1].p1.x + M2_MIN_WDT, bbox.p2.y)
        self.create_box(l.metal2, presets[0].p2.x - M2_MIN_WDT, bbox.p1.y, presets[0].p2.x, bbox.p2.y)
        self.create_box(l.metal2, presets[0].p2.x - M2_MIN_WDT, bbox.p2.y - M2_MIN_WDT, presets[1].p1.x + M2_MIN_WDT, bbox.p2.y)
        assert(len(senses) == word_width)
        self.create_box(l.metal2, senses[1].p1.x, bbox.p1.y, senses[1].p1.x + M2_MIN_WDT, bbox.p2.y + M2_MIN_WDT + M2_DIST)
        self.create_box(l.metal2, senses[0].p2.x - M2_MIN_WDT, bbox.p1.y, senses[0].p2.x, bbox.p2.y + M2_MIN_WDT + M2_DIST)
        self.create_box(l.metal2, senses[0].p2.x - M2_MIN_WDT, bbox.p2.y + M2_DIST, senses[1].p1.x + M2_MIN_WDT, bbox.p2.y + M2_MIN_WDT + M2_DIST)
        
        # draw power rails for standard cells 
        x = sensamps[1].bbox(l.metal1).p2.x - CELL_RAIL_WDT
        self.create_box(l.metal1, x, bbox.p1.y, x + CELL_RAIL_WDT, bbox.p2.y)
        x = sensamps[1].bbox(l.metal1).p1.x
        self.create_box(l.metal1, x, bbox.p1.y, x + CELL_RAIL_WDT, bbox.p2.y)
        x = sensamps[0].bbox(l.metal1).p1.x
        self.create_box(l.metal1, x, bbox.p1.y, x + CELL_RAIL_WDT, bbox.p2.y)
            
        # draw VSS stripes on M4
        self.vss_m1 = self.find_boxes_with_text(l.metal1, l.metal1_label, "VSS")
        self.vss_m4 = []
        for block in block_cells:
            x = block.bbox(l.nplus).p1.x + BLOCK_VSS_OFF
            vss = self.create_box(l.metal4, x, bbox.p1.y, x + BLOCK_VSS_WDT, bbox.p2.y)
            self.vss_m4.append(vss)
            
        for m4 in self.vss_m4:
            for m1 in self.vss_m1:
                self.place_via_area(m1 & m4, 1, 4)
                
        self.vss_sense = []
        xs = (sensamps[1].bbox(l.metal1).p2.x + METALVIA_OVERLAP, sensamps[0].bbox(l.metal1).p1.x + CELL_RAIL_WDT)
        for x in xs:
            vss = self.create_box(l.metal4, x - SENSE_POWER_WDT, bbox.p1.y, x, bbox.p2.y)
            self.vss_sense.append(vss)

        self.pvia_inhibit = bitwire_m3

        # draw VDD stripes on M4
        self.vdd_m4 = []
        self.vdd_m1 = self.find_boxes_with_text(l.metal1, l.metal1_label, "VDD")
        vdd_create_list = (
            (sensamps[1].bbox(l.metal1).p1.x - METALVIA_OVERLAP, SENSE_POWER_WDT),
            (self.bbox(l.metal1).p2.x - PMOS_VDD_WDT, PMOS_VDD_WDT)
        )
        for x,w in vdd_create_list:
            vdd = self.create_box(l.metal4, x, bbox.p1.y, x + w, bbox.p2.y)
            self.vdd_m4.append(vdd)
        

class EfuseArrayAsync(CellGf180mcu):
    """
    Parametrizable eFuse array cell.
    """
    def __init__(self, l : LayoutGf180mcu, name : str = "efuse_array_async", nwords : int = 1, word_width : int = 8, nfuses : int = 1):
        super().__init__(l, name = name)
        layout = l.layout
        assert(nfuses == nwords) # the only supported mode for now  
        
        # generate bitlines
        self.add_cells = {}

        bitline_cell = EfuseBitline(l, word_width)

        for i in range(1):
            bitline = self.cell_inst(bitline_cell, 0, i * (bitline_cell.bbox().height() + BITLINE_YOFF), 0)
            inhibit = []

            # create power vias
            for p in bitline_cell.pvia_inhibit:
                inhibit.append(p.transformed(bitline.trans))
            for m4 in bitline_cell.vdd_m4:
                self.create_text_p(l.metal4_label, m4.center(), "VDD")
                for m1 in bitline_cell.vdd_m1:
                    m1t = m1.transformed(bitline.trans)
                    m4t = m4.transformed(bitline.trans)
                    self.place_via_area_step(m1t & m4t, 1, 4, l.grid_align(VIA_STEP*1.2), 3000, inhibit, False, True)
            
            for m4 in bitline_cell.vss_m4:
                vss = m4.transformed(bitline.trans)
                self.create_text_p(l.metal4_label, vss.center(), "VSS")         

            for m4 in bitline_cell.vss_sense:
                vss_sense = m4.transformed(bitline.trans)
                self.create_text_p(l.metal4_label, vss_sense.center(), "VSS")
                for m1 in bitline_cell.vss_m1:
                    m1 = m1.transformed(bitline.trans)
                    self.place_via_area_step(m1 & vss_sense, 1, 4, VIA_STEP, 3000, inhibit, False)
            
            # create output access vias
            for o in range(word_width):
                out = bitline_cell.find_boxes_with_text(l.metal1, l.metal1_label, f"OUT[{o}]")
                assert(len(out) == 1)
                if o%2:
                    out = self.place_via_tower(out[0].transformed(bitline.trans).center() + db.Point(100, -100), 1, 3, True)
                    self.create_box_p(l.metal3, out.p1, out.p2 + db.Point(100, 100))
                else:
                    out = self.place_via_tower(out[0].transformed(bitline.trans).center() + db.Point(-100, 100), 1, 3, True)
                    self.create_box_p(l.metal3, out.p1, out.p2 - db.Point(100, 100))
                self.create_text_p(l.metal3_label, out.center(), f"OUT[{o}]")


            # move labels to upper level adding postfixes
            label_layers = [l.metal1_label, l.metal2_label, l.metal3_label, l.metal4_label]
            it = db.RecursiveShapeIterator(layout, self.cell, label_layers, bitline.bbox(l.metal1_label))
            it.shape_flags = db.Shapes.STexts
            for t in it.each():
                shape = t.shape()
                s = shape.text.string
                box = t.shape().bbox().transformed(t.trans())
                labels_to_replace = []
                labels_to_keep = ["BIT_SEL", "PRESET_N", "SENSE", "COL_PROG_N[", "OUT["]
                labels_to_keep_m4 = ["VSS", "VDD"]
                if s in labels_to_replace:
                    self.create_text(it.layer(), box.p1.x, box.p1.y, s+"["+str(i)+"]")
                for lab in labels_to_keep:
                    if lab == s[:len(lab)]:
                        self.create_text(it.layer(), box.p1.x, box.p1.y, s)
                if (it.layer() == l.metal4_label) and (s in labels_to_keep_m4):
                    self.create_text(it.layer(), box.p1.x, box.p1.y, s)
        
        # remove all labels not on top
        it = db.RecursiveShapeIterator(layout, self.cell, label_layers)
        it.shape_flags = db.Shapes.STexts
        it.min_depth = 1
        for t in it.each():
            shape = t.shape()
            shape.delete()  

        # mark whole array with PR_BNDRY
        self.dup_box(l.pr_bndry, self.bbox())

        self.zero_origin()
        

def create_efuse_array_async(layout : PathLike | str = "efuse_array.gds", cellname : str = "efuse_array", 
    nwords : int = 32, word_width : int = 2, flat : bool = False, add_cells : PathLike | str = ""):
    """
    Create eFuse array cell with defined parameters and write it to GDS or add it to an existing layout.
    
        layout      : could be either a string/PathLike object (a name of GDS file to write) or a klayout.db.Layout object
        cellname    : name for the array cell
        nwords      : total number of words in array
        word_width  : number of bits per word
        flat        : if True the cell will be flattened
    """
    
    gdsname = ""
    if isinstance(layout, PathLike) or (type(layout) is str):
        gdsname = str(layout)
        layout = db.Layout()
    elif type(layout) is not db.Layout:
        raise TypeError("layout argument should be either a pathlike or a klayout.db.Layout object!")
    l = LayoutGf180mcu(layout)
        
    assert(nwords==1)
    nfuses = nwords # the only supported mode for now  
    array = EfuseArrayAsync(l, cellname, nwords, word_width, nfuses)
    
    if flat:
        array.flatten()
    
    if gdsname:
        l.layout.write(gdsname)

    if add_cells:
        with open(add_cells, "w") as f:
            json.dump(array.add_cells, f)
    
# Main
if __name__ == '__main__':
    # Parse arguments
    if len(sys.argv) < 2:
        word_width = 1
        nwords = 16
    elif len(sys.argv) == 3:
        nwords = int(sys.argv[1])
        word_width = int(sys.argv[2])
    else:
        print("Usage:", sys.argv[0], "number_of_words word_width")
        sys.exit(1)
    
    name = f"efuse_array_{nwords}x{word_width}"
    create_efuse_array(name + ".gds", name, nwords, word_width)
    
