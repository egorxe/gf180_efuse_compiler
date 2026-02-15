#
# Helper classes to generate GDS for GF180 with KLayout
#

import os
from pathlib import Path
from klayout import db

# Tech parameters, all sizes in nm
CONTACT_POLY_OVERLAP= 70
CONTACT_SIZE        = 220
CONTACT_DIST        = 280
CONTACT_STEP        = CONTACT_SIZE + CONTACT_DIST

METALVIA_OVERLAP    = 60
VIA_SIZE            = 260
VIA_DIST            = 360
VIA_STEP            = VIA_DIST + VIA_SIZE

M1_MIN_WDT          = 230
M1_DIST             = 230

M2_MIN_WDT          = 280
M2_DIST             = 280

DG_POLY_ENC         = 400
COMP_CONT_DIST      = 170

MAX_TAP_DIST        = 20000

class LayoutGf180mcu():
    """
    Small wrapper for KLayout Layout class with definitions for GF180MCU.
    """
    def __init__(self, layout : db.Layout = None):
        # create KLayout layout & set some parameters
        if layout:
            self.layout = layout
        else:
            self.layout = db.Layout()
            self.layout.dbu = 0.001
            layout = self.layout
            
        assert(self.layout.dbu == 0.001)    # intended to use only with DB unit = 1 nm
        self.llo = db.LoadLayoutOptions()
        self.llo.cell_conflict_resolution = db.LoadLayoutOptions.CellConflictResolution.RenameCell
        
        self.contact = layout.layer(33, 0)
        self.metal1 = layout.layer(34, 0)
        self.metal1_label = layout.layer(34, 10)
        self.via1 = layout.layer(35, 0)
        self.metal2 = layout.layer(36, 0)
        self.metal2_label = layout.layer(36, 10)
        self.via2 = layout.layer(38, 0)
        self.metal3 = layout.layer(42, 0)
        self.metal3_label = layout.layer(42, 10)
        self.via3 = layout.layer(40, 0)
        self.metal4 = layout.layer(46, 0)
        self.metal4_label = layout.layer(46, 10)
        self.via4 = layout.layer(41, 0)
        self.metal5 = layout.layer(81, 0)
        self.metal5_label = layout.layer(81, 10)
        self.poly2 = layout.layer(30, 0)
        self.dualgate = layout.layer(55, 0)
        self.nplus = layout.layer(32, 0)
        self.pr_bndry = layout.layer(0, 0)
        self.efuse_mk = layout.layer(80, 5)
        
        self.grid = 5
        
        self.metals = {1: self.metal1, 2: self.metal2, 3: self.metal3, 4: self.metal4, 5: self.metal5}
        self.labels = {1: self.metal1_label, 2: self.metal2_label, 3: self.metal3_label, 4: self.metal4_label, 5: self.metal5_label}
        self.vias = {1: self.via1, 2: self.via2, 3: self.via3, 4: self.via4}
        
    def to_dbu(self, m : float):
        """
        Convert microns to db units
        """
        return int(round(m / self.layout.dbu))
        
    def grid_align(self, x : float):
        """
        Align to grid
        """
        return (int(x)//self.grid) * self.grid
    
class CellGf180mcu():
    """
    Small wrapper for KLayout Layout class with shortcuts for GF180MCU.
    """
    def __init__(self, layout_wrapper : LayoutGf180mcu, parent = None, name : str = "", single_cell : bool = False):
        self.layout = layout_wrapper.layout
        self.l = layout_wrapper
        
        if type(parent) is db.Cell:
            self.cell = parent
        elif (isinstance(parent, str)) or (isinstance(parent, Path)):    
            assert(name)
            if single_cell:
                gds_layout = db.Layout()
                gds_layout.read(str(parent))
                read_cell = gds_layout.cell(name)
                index = self.layout.add_cell(name)
                self.cell = self.layout.cell(index)
                self.name = name
                self.cell.copy_tree(read_cell)
            else:
                self.layout.read(str(parent), layout_wrapper.llo)
                self.cell = self.layout.cell(name)
                self.name = name
        else:
            # create new cell
            assert(name)
            index = self.layout.add_cell(name)
            self.cell = self.layout.cell(index)
            self.name = name
            
    def flatten(self, depth : int = -1, prune : bool = True):
        """
        Flatten cell.
        """
        self.cell.flatten(depth, prune)
        
    def zero_origin(self):
        """
        Move cell origin to zero.
        """
        self.cell = self.cell.transform(db.Trans(-self.cell.bbox().p1))

    def clear_labels(self):
        """
        Remove everything from labels layers.
        """
        for k in self.l.labels:
            self.cell.shapes(self.l.labels[k]).clear()
        
    def trans_llc(self, x : int, y : int, r : int) -> db.Trans:
        """
        Returns a transformation keeping coords of left lower corner.
        """
        if r == 1:
            x += self.bbox().height()
        elif r == 2:
            x += self.bbox().width()
            y += self.bbox().height()
        elif r == 3:
            y += self.bbox().width()
        return db.Trans(r, False, x, y)
        
    def dup_box(self, layer : int, box : db.Box):
        """
        Draw a box on a layer inside this cell. Returns the box.
        """
        self.cell.shapes(layer).insert(box)
        return box
    
    def create_box(self, layer : int, x0 : int, x1 : int, y0 : int, y1 : int):
        """
        Draw a box set by coordinates on a layer inside this cell. Returns the box.
        """
        box = db.Box(x0, x1, y0, y1)
        self.dup_box(layer, box)
        return box
        
    def create_box_p(self, layer : int, p1 : db.Point, p2 : db.Point):
        """
        Draw a box set by points on a layer inside this cell. Returns the box.
        """
        return self.create_box(layer, p1.x, p1.y, p2.x, p2.y)
               
    def create_text(self, layer : int, x : int, y : int, text : str):
        """
        Add a text object to coordinates.
        """
        self.cell.shapes(layer).insert(db.Text(text, x, y))
        
    def create_text_p(self, layer : int, p : db.Point, text : str):
        """
        Add a text object to point.
        """
        self.create_text(layer, p.x, p.y, text)
        
    def bbox(self, layer : int = -1):
        """
        Boundary box of this cell.
        """
        if layer < 0:
            return self.cell.bbox()
        else:
            return self.cell.bbox(layer)
        
    def place_contact(self, x : int, y : int):
        """
        Create a contact.
        """
        self.create_box(self.l.contact, x, y, x + CONTACT_SIZE, y + CONTACT_SIZE)
        
    def place_via_tower(self, point: db.Point, bottom_metal: int, top_metal: int, center : bool = False):
        """
        Generate a via stack & metals connecting a point on bottom_metal to the same point on top_metal. 
        """
        if not center:
            point.x += VIA_SIZE/2
            point.y += VIA_SIZE/2
        via_box = db.Box(point.x-VIA_SIZE/2, point.y-VIA_SIZE/2, point.x+VIA_SIZE/2, point.y+VIA_SIZE/2)
        metal_box = db.Box(point.x-VIA_SIZE/2-METALVIA_OVERLAP, point.y-VIA_SIZE/2-METALVIA_OVERLAP, point.x+VIA_SIZE/2+METALVIA_OVERLAP, point.y+VIA_SIZE/2+METALVIA_OVERLAP)
        self.dup_box(self.l.metals[bottom_metal], metal_box)
        for i in range(bottom_metal, top_metal):
            self.dup_box(self.l.vias[i], via_box)
            self.dup_box(self.l.metals[i+1], metal_box)
        return metal_box
        
    def place_via_area_step(self, box : db.Box, bottom_metal : int, top_metal : int, stepx : int, stepy : int, inhibit_boxes : list = [], fill = True, enlarge = False):
        """
        Fill the box with vias controlling distance between vias. Do not place vias touching any box from inhibit_boxes list.
        """
        if box.empty():
            return
        xvias = ((box.width() - METALVIA_OVERLAP*2 + VIA_DIST) // stepx) 
        yvias = ((box.height() - METALVIA_OVERLAP*2 + VIA_DIST) // stepy)
        x0 = box.p1.x + self.l.grid_align((box.width() - xvias*stepx + VIA_DIST) // 2)
        y0 = box.p1.y + self.l.grid_align((box.height() - yvias*stepy + VIA_DIST) // 2)
        if xvias == 0 and enlarge:
            xvias = 1
            x0 = box.p1.x
        if yvias == 0 and enlarge:
            yvias = 1
            y0 = box.p1.y
        
        boxes = []
        for i in range(xvias):
            for j in range(yvias):
                point = db.Point(x0 + i*stepx, y0 + j*stepy)
                no_via = False
                for ib in inhibit_boxes:
                    if ib.touches(db.Box(point.x-VIA_SIZE-M2_DIST, point.y-VIA_SIZE-M2_DIST, point.x+VIA_SIZE+M2_DIST, point.y+VIA_SIZE+M2_DIST)):
                        no_via = True
                        break
                if not no_via:
                    boxes.append(self.place_via_tower(point, bottom_metal, top_metal))
        # fill metals inbetween vias
        if (len(boxes) > 1) and fill:
            for i in range(bottom_metal, top_metal+1):
                self.create_box_p(self.l.metals[i], boxes[0].p1, boxes[len(boxes)-1].p2)
                
    def place_via_area(self, box: db.Box, bottom_metal: int, top_metal: int):
        """
        Fill the box with vias with minimal distance step.
        """
        self.place_via_area_step(box, bottom_metal, top_metal, VIA_STEP, VIA_STEP)
        
    def cell_inst(self, cell, x : int, y : int, r : int, center : bool = False):
        """
        Instance a cell inside this cell.
        """
        if center:
            x -= cell.bbox().width() // 2
            y -= cell.bbox().height() // 2
        ciarray = db.CellInstArray(cell.cell, cell.trans_llc(x, y, r))
        inst = self.cell.insert(ciarray)
        return inst

    def find_boxes_with_text(self, box_layer : int, label_layer : int, label : str):
        """
        Find all boxes on a layer in this cell intersecting with specific text label.
        """
        boxes = []
        tit = self.cell.begin_shapes_rec(label_layer)
        tit.shape_flags = db.Shapes.STexts
        for t in tit.each():
            if t.shape().text.string == label:
                it = self.cell.begin_shapes_rec_touching(box_layer, t.shape().bbox().transformed(t.trans()))
                for s in it.each():
                    if s.shape().is_box():
                        b = s.shape().box.transformed(s.trans())
                        boxes.append(b)
        return boxes

    def find_boxes_with_text_inst(self, box_layer : int, label_layer : int, label : str, cell, inst : db.Instance):
        boxes = cell.find_boxes_with_text(box_layer, label_layer, label)
        tboxes = []
        for b in boxes:
            tboxes.append(b.transformed(inst.trans))
        return tboxes
        
class StdCellGf180mcu(CellGf180mcu):
    """
    Standard cell helper.
    """
    def __init__(self, l : LayoutGf180mcu, cell_name : str):
        super().__init__(l, parent = Path(os.environ['PDK_ROOT']) / os.environ['PDK'] / 
            "libs.ref/gf180mcu_fd_sc_mcu7t5v0/gds/gf180mcu_fd_sc_mcu7t5v0.gds", name = cell_name, single_cell = True)
        self.zero_origin()
        self.wdt = self.bbox(l.metal1).width()

class Endcap(StdCellGf180mcu):
    """
    Endcap.
    """
    def __init__(self, l : LayoutGf180mcu):
        super().__init__(l, "gf180mcu_fd_sc_mcu7t5v0__endcap")

class FillTie(StdCellGf180mcu):
    """
    Filler with well tap.
    """
    def __init__(self, l : LayoutGf180mcu):
        super().__init__(l, "gf180mcu_fd_sc_mcu7t5v0__filltie")

class FillCap(StdCellGf180mcu):
    """
    Filler with capacitor.
    """
    def __init__(self, l : LayoutGf180mcu):
        super().__init__(l, "gf180mcu_fd_sc_mcu7t5v0__fillcap_4")

class Inv1(StdCellGf180mcu):
    """
    Smallest inverter.
    """
    def __init__(self, l : LayoutGf180mcu):
        super().__init__(l, "gf180mcu_fd_sc_mcu7t5v0__inv_1")
