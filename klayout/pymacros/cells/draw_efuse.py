# Copyright 2022 GlobalFoundries PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pya
import os
from .draw_mos import *
from .mos import mos_ld, mos_grw

USER = os.environ['USER']
gds_path = f"/home/{USER}/.klayout/pymacros/cells/efuse"

def draw_fill(layout):
    layout.read(f"{gds_path}/fill_1.gds")
    cell_name = "gf180mcu_fd_sc_mcu7t5v0__fill_1"
    cell = layout.cell(cell_name)
    cell.transform(pya.Trans.M0)
    cell.transform(pya.Trans(0, -430))
    metal1_label = layout.layer(34, 10)
    cell.shapes(metal1_label).clear()
    cell.shapes(layout.layer(63,63)).clear()
    return cell 

def draw_filltie(layout):
    layout.read(f"{gds_path}/filltie.gds")
    cell_name = "gf180mcu_fd_sc_mcu7t5v0__filltie"
    cell = layout.cell(cell_name)
    cell.transform(pya.Trans.M0)
    cell.transform(pya.Trans(0, -430))
    metal1_label = layout.layer(34, 10)
    cell.shapes(metal1_label).clear()
    cell.shapes(layout.layer(63,63)).clear()
    return cell 

def draw_fillcap(layout):
    layout.read(f"{gds_path}/fillcap_4.gds")
    cell_name = "gf180mcu_fd_sc_mcu7t5v0__fillcap_4"
    cell = layout.cell(cell_name)
    cell.transform(pya.Trans.M0)
    cell.transform(pya.Trans(0, -430))
    metal1_label = layout.layer(34, 10)
    cell.shapes(metal1_label).clear()
    cell.shapes(layout.layer(63,63)).clear()
    return cell

def draw_endcap(layout):
    layout.read(f"{gds_path}/endcap.gds")
    cell_name = "gf180mcu_fd_sc_mcu7t5v0__endcap"
    cell = layout.cell(cell_name)
    cell.transform(pya.Trans.M0)
    cell.transform(pya.Trans(0, -430))
    metal1_label = layout.layer(34, 10)
    cell.shapes(metal1_label).clear()
    cell.shapes(layout.layer(63,63)).clear()
    return cell

def draw_buf(layout):
    layout.read(f"{gds_path}/buf_1.gds")
    cell_name = "gf180mcu_fd_sc_mcu7t5v0__buf_1"
    cell = layout.cell(cell_name)
    cell.transform(pya.Trans.M0)
    cell.transform(pya.Trans(0, -430))
    metal1_label = layout.layer(34, 10)
    cell.shapes(metal1_label).clear()
    cell.shapes(layout.layer(63,63)).clear()
    return cell

def draw_efuse(layout):
    layout.read(f"{gds_path}/efuse.gds")
    cell_name = "efuse_cell"
    return layout.cell(cell_name)

def draw_efuse_senseamp(layout):

    layout.read(f"{gds_path}/efuse_senseamp_inv2.gds")
    cell_name = "efuse_senseamp_cell"
    layout.cell(cell_name).shapes(layout.layer(63, 63)).clear()
    metal1_label = layout.layer(34, 10)

    layout.cell(cell_name).shapes(metal1_label).clear()

    return layout.cell(cell_name)

def draw_efuse_bitline(layout, n_bitcells=4):
    n_full_lines = n_bitcells // 4
    n_extra_cells = n_bitcells % 4
    efuse_bitline_index = layout.add_cell("efuse_bitline_cell")
    efuse_bitline_cell = layout.cell(efuse_bitline_index)
    metal1_label = layout.layer(34, 10)
    metal2 = layout.layer(36, 0)
    metal2_label = layout.layer(36, 10)
    metal4_label = layout.layer(46, 10)
    line_sel_pin = pya.Point(1820, 51385)

    cur_pos = 0
    if n_full_lines > 0:
        layout.read(f"{gds_path}/efuse_bitline4.gds")
        efuse_bitline_instance = layout.cell("efuse_bitline4_cell")
        efuse_bitline_bbox = efuse_bitline_instance.bbox()
        efuse_bitline_width = efuse_bitline_bbox.right - efuse_bitline_bbox.left
        efuse_bitline_spacing = -920
        efuse_bitline_step = efuse_bitline_width + efuse_bitline_spacing
        full_bitlines = pya.CellInstArray(efuse_bitline_instance.cell_index(), pya.Trans(pya.Point(0, 0)),
                                        pya.Vector(efuse_bitline_step, 0), pya.Vector(0, 0),
                                        n_full_lines, 1)
        efuse_bitline_cell.insert(full_bitlines)

        line_sel_wire = pya.Box(line_sel_pin-pya.Vector(210, 230), line_sel_pin+pya.Vector(efuse_bitline_step*(n_full_lines-1), 185))
        efuse_bitline_cell.shapes(metal2).insert(line_sel_wire)
        cur_pos = efuse_bitline_step*(n_full_lines)

    if n_extra_cells > 0:
        layout.read(f"{gds_path}/efuse_bitline{n_extra_cells}.gds")
        extra_cells_instance = layout.cell(f"efuse_bitline{n_extra_cells}_cell")
        extra_cells = pya.CellInstArray(extra_cells_instance.cell_index(), pya.Trans(pya.Point(cur_pos, 0)))
        efuse_bitline_cell.insert(extra_cells)

    if n_full_lines > 0 and n_extra_cells > 0:
        line_sel_wire = pya.Box(line_sel_pin-pya.Vector(210, 230), line_sel_pin+pya.Vector(cur_pos, 185))
        efuse_bitline_cell.shapes(metal2).insert(line_sel_wire)

    efuse_bitline_cell.flatten(1)
    efuse_bitline_cell.shapes(metal1_label).clear()
    efuse_bitline_cell.shapes(metal2_label).clear()
    efuse_bitline_cell.shapes(metal4_label).clear()


    return efuse_bitline_cell 

def draw_efuse_array(layout, n_bitlines=4, n_bitcells=4):

    # define layers 
    contact = layout.layer(33, 0)
    metal1 = layout.layer(34, 0)
    metal1_label = layout.layer(34, 10)
    via1 = layout.layer(35, 0)
    metal2 = layout.layer(36, 0)
    metal2_label = layout.layer(36, 10)
    via2 = layout.layer(38, 0)
    metal3 = layout.layer(42, 0)
    metal3_label = layout.layer(42, 10)
    via3 = layout.layer(40, 0)
    metal4 = layout.layer(46, 0)
    metal4_label = layout.layer(46, 10)
    via4 = layout.layer(41, 0)
    metal5 = layout.layer(81, 0)
    poly2 = layout.layer(30, 0)
    dualgate = layout.layer(55, 0)

    # global parameters
    wire_width = 330
    anode_wire_width = 1700
    anode_wire_sep = 1000
    metalvia_overlap = 60
    via_size = 260
    rail_width = 2500
    vss_rail_y = 51500 - 1180
    vdd_rail_y = -10000 + 1750 + 765
    extra_vss_rail_y = vdd_rail_y + 3970
    via_step = metalvia_overlap*2+via_size+280

    def place_via_tower(cell: pya.Cell, point: pya.Point, bottom_metal: int, top_metal: int):
        """
        Place necessary vias metals connecting a point on bottom_metal to the same point on top_metal. 
        """
        metals = {1: metal1, 2: metal2, 3: metal3, 4: metal4, 5: metal5}
        vias = {1: via1, 2: via2, 3: via3, 4: via4}
        via_box = pya.Box(point.x-via_size/2, point.y-via_size/2, point.x+via_size/2, point.y+via_size/2)
        metal_box = pya.Box(point.x-via_size/2-metalvia_overlap, point.y-via_size/2-metalvia_overlap, point.x+via_size/2+metalvia_overlap, point.y+via_size/2+metalvia_overlap)
        cell.shapes(metals[bottom_metal]).insert(metal_box)
        for i in range(bottom_metal, top_metal):
            cell.shapes(vias[i]).insert(via_box)
            cell.shapes(metals[i+1]).insert(metal_box)

    # create cell
    efuse_array_index = layout.add_cell("efuse_array")
    efuse_array_cell = layout.cell(efuse_array_index)
    
    bitline_instance = draw_efuse_bitline(layout, n_bitcells=n_bitcells)
    bitline_bbox = bitline_instance.bbox()
    bitline_width = bitline_bbox.right - bitline_bbox.left
    bitline_spacing = 500 #-160-320# they need to overlap a bit
    bitline_step = bitline_width + bitline_spacing
    full_line_width = 21495
    anode0_pin = pya.Point( 5600, 39800) 
    anode1_pin = pya.Point( 5600, 11800)
    anode2_pin = pya.Point(15900, 11800)
    anode3_pin = pya.Point(15900, 39800)
    anode_pins = [pin + pya.Vector((full_line_width-920)*i, 0) for i in range(n_bitcells//4 + 1) 
                                for pin in [anode0_pin, anode1_pin, anode2_pin, anode3_pin]][:n_bitcells]
    line_sel_pin = pya.Point(10750, 200) # take the leftmost point
    vss_0_pin = pya.Point(455, 50200)
    vss_1_pin = pya.Point(10745, 50200)
    vss_2_pin = pya.Point(21030, 50200)
    n_bitline_vss_pins = (n_bitcells//4)*3 + {0: 0, 1: 1, 2: 2, 3: 2}[n_bitcells%4]
    vss_pins = [pin + pya.Vector((full_line_width-920)*i, 0) for i in range(n_bitcells//4 + 1) 
                                for pin in [vss_0_pin, vss_1_pin, vss_2_pin]][:n_bitline_vss_pins]

    bitlines = pya.CellInstArray(bitline_instance.cell_index(), pya.Trans(pya.Point(0, 0)),
                                    pya.Vector(bitline_step, 0), pya.Vector(0, 0),
                                    n_bitlines, 1)
    efuse_array_cell.insert(bitlines)

    PMOS = draw_pmos(layout, 0.5, 50, mos_ld, 1, mos_grw, "Bulk Tie", "5V", 0, 0)
    PMOS_width = 2660
    PMOS_spacing = 1980
    PMOS_step = PMOS_width+PMOS_spacing
    PMOS_bulk_pin_x = -580
    PMOS_source_pin_x = 180
    PMOS_drain_pin_x = 1205
    PMOS_bulk_drain_pin_y = 500
    PMOS_gate_pin = pya.Point(690, PMOS.bbox().height()-220)
    PMOS_gate_extension = pya.Box(440, 50220, 940, 50620)
    PMOS_dualgate_extension = pya.Box(-1040, 50620, 1620, 51120)
    bitline_PMOS_sep = 960 + 500
    PMOS_start_x = bitline_step*(n_bitlines)+bitline_PMOS_sep
    PMOS_y = 450
    PMOSs = pya.CellInstArray(PMOS.cell_index(), pya.Trans(pya.Point(PMOS_start_x, PMOS_y)),
                                pya.Vector(PMOS_step, 0), pya.Vector(0, 0),
                                n_bitcells, 1)
    efuse_array_cell.insert(PMOSs)

    senseamp_instance = draw_efuse_senseamp(layout)
    senseamp_bbox = senseamp_instance.bbox()
    senseamp_width = senseamp_bbox.right - senseamp_bbox.left
    senseamp_height = senseamp_bbox.top - senseamp_bbox.bottom
    senseamp_spacing = -430 
    senseamp_step = senseamp_width + senseamp_spacing
    senseamp_vss_pin = pya.Point(6000, -400)
    senseamp_vdd_pin = pya.Point(5400, -4350)
    senseamp_out_pin = pya.Point(9400, -3590)
    fuse_pin = pya.Point(1920, -1020)
    npreset_pin = pya.Point(1890, -2360)
    sense_pin = pya.Point(1480, -1700)

    senseamp_y = vdd_rail_y + 4060 

    stripe_right = efuse_array_cell.bbox().right 
    stripe_left  = -500 #efuse_array_cell.bbox().left

    # add metal4 vss rail
    vss_rail = pya.Box(stripe_left, vss_rail_y-rail_width/2, stripe_right, vss_rail_y+rail_width/2)
    efuse_array_cell.shapes(metal4).insert(vss_rail)
    efuse_array_cell.shapes(metal4_label).insert(pya.Text("VSS", pya.Trans(vss_rail.center())))

    # add metal4 vdd rail
    vdd_rail = pya.Box(stripe_left, vdd_rail_y-rail_width/2, stripe_right, vdd_rail_y+rail_width/2)
    efuse_array_cell.shapes(metal4).insert(vdd_rail)
    efuse_array_cell.shapes(metal4_label).insert(pya.Text("VDD", pya.Trans(vdd_rail.center())))

    # create metal stripes connecting corresponding anodes
    anode_wires_y = []
    anode_wires = []
    top_wires = 0
    bottom_wires = 0
    for i in range(n_bitcells):
        if i%4 in [0, 3]:
            anode_wires_y.append(38600 - (anode_wire_width + anode_wire_sep)*top_wires)
            top_wires += 1
        else:
            anode_wires_y.append(13000 + (anode_wire_width + anode_wire_sep)*bottom_wires)
            bottom_wires += 1
        anode_wires.append(pya.Box(0, anode_wires_y[i]-anode_wire_width/2, stripe_right, anode_wires_y[i]+anode_wire_width/2))
        efuse_array_cell.shapes(metal3).insert(anode_wires[i])
    
    current_capcell_x = 0
    endcap_instance = draw_endcap(layout)
    endcap_VSS_pin = pya.Point(540, -430)
    endcap_VDD_pin = pya.Point(540, -4350)
    place_via_tower(endcap_instance, endcap_VSS_pin, 1, 4)
    place_via_tower(endcap_instance, endcap_VDD_pin, 1, 4)
    fill_instance = draw_fill(layout)
    fillcap_instance = draw_fillcap(layout)
    fillcap_VSS_pin = pya.Point(1100, -430)
    fillcap_VDD_pin = pya.Point(1100, -4350)
    for j in [-1, 0, 1]:
        place_via_tower(fillcap_instance, pya.Point(fillcap_VSS_pin.x+j*via_step, fillcap_VSS_pin.y), 1, 4)
        place_via_tower(fillcap_instance, pya.Point(fillcap_VDD_pin.x+j*via_step, fillcap_VDD_pin.y), 1, 4)
    filltie_instance = draw_filltie(layout)
    filltie_VSS_pin = pya.Point(560, -430)
    filltie_VDD_pin = pya.Point(560, -4350)
    place_via_tower(filltie_instance, filltie_VSS_pin, 1, 4)
    place_via_tower(filltie_instance, filltie_VDD_pin, 1, 4)
    buf_instance = draw_buf(layout)
    buf_VSS_pin = pya.Point(1200, -430)
    buf_VDD_pin = pya.Point(1600, -4350)
    buf_I_pin = pya.Point(925, 900-3250)
    buf_I_pin2 = pya.Point(925, 900-2250)
    buf_Z_pin = pya.Point(2650, 900-2250)
    buf_Z_pin2 = pya.Point(2700, 900-4250)
    for j in [-1, 0, 1]:
        place_via_tower(buf_instance, pya.Point(buf_VSS_pin.x+j*via_step, buf_VSS_pin.y), 1, 4)
    for j in [-2, 0]:
        place_via_tower(buf_instance, pya.Point(buf_VDD_pin.x+j*via_step, buf_VDD_pin.y), 1, 4)
    cell_overlap = 860

    # place PMOS
    for i in range(n_bitcells):
        # connect PMOS drain and bulk to VDD
        current_PMOS_displ = pya.Vector(PMOS_start_x+PMOS_step*i, -170)
        current_bulk_pin = pya.Point(PMOS_bulk_pin_x, PMOS_bulk_drain_pin_y) + current_PMOS_displ
        current_drain_pin = pya.Point(PMOS_drain_pin_x, PMOS_bulk_drain_pin_y) + current_PMOS_displ
        vdd_wire = pya.Box(current_bulk_pin.x-wire_width/2, vdd_rail.bottom, current_drain_pin.x+wire_width/2, vss_rail.bottom-2000)
        efuse_array_cell.shapes(metal4).insert(vdd_wire)
        for k in range((min(anode_wires_y)-current_bulk_pin.y-anode_wire_width-500)//via_step):
            place_via_tower(efuse_array_cell, pya.Point(current_bulk_pin.x, current_bulk_pin.y+via_step*k), 1, 4)
            place_via_tower(efuse_array_cell, pya.Point(current_drain_pin.x, current_drain_pin.y+via_step*k), 1, 4)
        for k in range((vss_rail.bottom-2500-max(anode_wires_y)-anode_wire_width-500)//via_step):
            place_via_tower(efuse_array_cell, pya.Point(current_bulk_pin.x, vss_rail.bottom-2500-via_step*k), 1, 4)
            place_via_tower(efuse_array_cell, pya.Point(current_drain_pin.x, vss_rail.bottom-2500-via_step*k), 1, 4)
        # extend gate and label PMOS gate pin
        efuse_array_cell.shapes(poly2).insert(PMOS_gate_extension.moved(pya.Vector(bitline_step*(n_bitlines)+bitline_PMOS_sep+PMOS_step*i, PMOS_y)))
        efuse_array_cell.shapes(dualgate).insert(PMOS_dualgate_extension.moved(pya.Vector(bitline_step*(n_bitlines)+bitline_PMOS_sep+PMOS_step*i, PMOS_y)))
        current_gate_pin = PMOS_gate_pin + current_PMOS_displ 
        efuse_array_cell.shapes(contact).insert(pya.Box(current_gate_pin-pya.Vector(110, 110), current_gate_pin+pya.Vector(110,110)))
        efuse_array_cell.shapes(metal1).insert(pya.Box(current_gate_pin-pya.Vector(170, 170), current_gate_pin+pya.Vector(170,720)))
        efuse_array_cell.shapes(metal1_label).insert(pya.Text(f"COL_PROG[{i}]", pya.Trans(current_gate_pin)))
        # connect source pin to anode_wire
        for j in [-1, 0, 1]:
            place_via_tower(efuse_array_cell, pya.Point(PMOS_source_pin_x+current_PMOS_displ.x, anode_wires_y[i]+via_step*j), 1, 3)
        
    # connect bitlines 
    for i in range(n_bitlines):
        # connect anodes to routing metal3 (anode_wires)
        current_bitline_displ = pya.Vector(bitline_step*i, 0)
        for j in range(n_bitcells):
            current_anode_pin = anode_pins[j] + current_bitline_displ 
            if anode_pins[j].y > anode_wires_y[j]:
                anode_extension = pya.Box(current_anode_pin.x-anode_wire_width/2, anode_wires_y[j]-anode_wire_width/2,
                                            current_anode_pin.x+anode_wire_width/2, anode_pins[j].y+anode_wire_width/2)
                efuse_array_cell.shapes(metal1).insert(anode_extension)
            else:
                anode_extension = pya.Box(current_anode_pin.x-anode_wire_width/2, anode_pins[j].y-anode_wire_width/2,
                                            current_anode_pin.x+anode_wire_width/2, anode_wires_y[j]+anode_wire_width/2)
                efuse_array_cell.shapes(metal1).insert(anode_extension)

            for j1 in [-1, 0, 1]:
                for j2 in [-1, 0, 1]:
                    place_via_tower(efuse_array_cell, pya.Point(current_anode_pin.x+j1*via_step, anode_wires_y[j]+j2*via_step), 1, 3)

        # place line_i pin
        # current_line_sel_pin = line_sel_pin + pya.Vector(bitline_step*i, 0)
        # efuse_array_cell.shapes(metal2_label).insert(pya.Text(f"LINE[{i}]", pya.Trans(current_line_sel_pin)))

        # connect to VSS
        for j in range(n_bitline_vss_pins):
            current_vss_pin = vss_pins[j] + current_bitline_displ
            # vss_connect = pya.Box(current_vss_pin.x-rail_width/2, 0, current_vss_pin.x+rail_width/2, vss_rail.top)
            vss_connect = pya.Box(current_vss_pin.x-rail_width/4-wire_width, max(anode_wires_y)+anode_wire_width, 
                                    current_vss_pin.x+rail_width/4+wire_width, vss_rail.top)
            efuse_array_cell.shapes(metal4).insert(vss_connect)
            via_step = metalvia_overlap*2+via_size+280
            for k in range((current_vss_pin.y-max(anode_wires_y)-anode_wire_width-500)//via_step):
                place_via_tower(efuse_array_cell, current_vss_pin+pya.Vector(0, -k*via_step), 1, 4)

    endcap = pya.CellInstArray(endcap_instance.cell_index(), pya.Trans(pya.Point(current_capcell_x, senseamp_y)))
    efuse_array_cell.insert(endcap)
    current_capcell_x += endcap_instance.bbox().width() - cell_overlap 

    last_filltie_x = current_capcell_x
    filltie = pya.CellInstArray(filltie_instance.cell_index(), pya.Trans(pya.Point(current_capcell_x, senseamp_y)))
    efuse_array_cell.insert(filltie)
    current_capcell_x += filltie_instance.bbox().width() - cell_overlap 
    
    next_line_sel = line_sel_pin.x
    senseamps_placed = 0
    lines_routed = 0
    leftmost_sense_pin = None
    rightmost_sense_pin = None
    leftmost_npreset_pin = None
    rightmost_npreset_pin = None
    senseamp_fuse_pin_y_extension = 3280 - 610

    filltie_num = 0
    fillcap_num = 0

    # place cap cells, senseamps and bufs
    while True:
        if current_capcell_x > PMOS_start_x-5000:
            break
        if current_capcell_x > next_line_sel:
            buf_displ = pya.Vector(current_capcell_x, senseamp_y) 
            buf = pya.CellInstArray(buf_instance.cell_index(), buf_displ)
            efuse_array_cell.insert(buf)
            m2_connect_h = pya.Box(next_line_sel-wire_width/2, line_sel_pin.y-wire_width/2,
                                   current_capcell_x+buf_Z_pin.x+wire_width/2, line_sel_pin.y+wire_width/2)
            m2_connect_v = pya.Box(current_capcell_x+buf_Z_pin.x-wire_width/2, senseamp_y+buf_Z_pin.y-wire_width/2,
                                   current_capcell_x+buf_Z_pin.x+wire_width/2, line_sel_pin.y+wire_width/2)
            efuse_array_cell.shapes(metal2).insert(m2_connect_h)
            efuse_array_cell.shapes(metal2).insert(m2_connect_v)
            place_via_tower(efuse_array_cell, buf_displ+buf_Z_pin, 1, 2)
            
            efuse_array_cell.shapes(metal2_label).insert(pya.Text(f"LINE[{lines_routed}]", pya.Trans(buf_displ+buf_I_pin)))
            place_via_tower(efuse_array_cell, buf_displ+buf_I_pin, 1, 2)
            m2_router_helper = pya.Box(current_capcell_x+buf_I_pin.x-wire_width/2, vdd_rail.bottom,
                                   current_capcell_x+buf_I_pin.x+wire_width/2, senseamp_y+buf_I_pin.y+wire_width/2)
            efuse_array_cell.shapes(metal2).insert(m2_router_helper)

            lines_routed += 1
                
            current_capcell_x += buf_instance.bbox().width() - cell_overlap
            next_line_sel += bitline_step
            continue
        if current_capcell_x - last_filltie_x > 20000:
            last_filltie_x = current_capcell_x 
            filltie = pya.CellInstArray(filltie_instance.cell_index(), pya.Trans(pya.Point(current_capcell_x, senseamp_y)))
            efuse_array_cell.insert(filltie)
            current_capcell_x += filltie_instance.bbox().width() - cell_overlap
            filltie_num += 1
            continue
        if senseamps_placed < n_bitcells:
            current_capcell_x += 140 # NP.2 violation fix
            # connect senseamp pins
            current_senseamp_displ = pya.Vector(current_capcell_x, senseamp_y)
            if senseamps_placed == 0:        
                leftmost_sense_pin = sense_pin + current_senseamp_displ 
                leftmost_npreset_pin = npreset_pin + current_senseamp_displ
            if senseamps_placed == n_bitcells-1:        
                rightmost_sense_pin = sense_pin + current_senseamp_displ
                rightmost_npreset_pin = npreset_pin + current_senseamp_displ
            senseamp = pya.CellInstArray(senseamp_instance.cell_index(), pya.Trans(current_senseamp_displ))
            efuse_array_cell.insert(senseamp)
            current_capcell_x += senseamp_step

            current_vss_pin = senseamp_vss_pin + current_senseamp_displ 
            for j1 in [-1, 0, 1]:
                place_via_tower(efuse_array_cell, pya.Point(current_vss_pin.x+j1*via_step, current_vss_pin.y), 1, 4)

            current_vdd_pin = senseamp_vdd_pin + current_senseamp_displ 
            for j1 in [-1, 0, 1]:
                place_via_tower(efuse_array_cell, pya.Point(current_vdd_pin.x+j1*via_step, current_vdd_pin.y), 1, 4)
            
            current_out_pin = senseamp_out_pin + current_senseamp_displ 

            current_fuse_pin = fuse_pin + current_senseamp_displ 
            fuse_wire = pya.Box(current_fuse_pin.x-wire_width/2, current_fuse_pin.y+senseamp_fuse_pin_y_extension-wire_width/2, 
                                    current_fuse_pin.x+wire_width/2, anode_wires_y[senseamps_placed]+anode_wire_width/2)
            efuse_array_cell.shapes(metal4).insert(fuse_wire)
            m1_fuse_extension = pya.Box(current_fuse_pin.x-via_size/2-metalvia_overlap, current_fuse_pin.y-wire_width/2,
                                    current_fuse_pin.x+via_size/2+metalvia_overlap, current_fuse_pin.y+senseamp_fuse_pin_y_extension+via_step*2+wire_width/2)
            efuse_array_cell.shapes(metal1).insert(m1_fuse_extension)
            for j1 in [0, 1, 2]:
                place_via_tower(efuse_array_cell, pya.Point(current_fuse_pin.x, current_fuse_pin.y+senseamp_fuse_pin_y_extension+j1*via_step), 1, 4)
            for j1 in [-1, 0, 1]:
                place_via_tower(efuse_array_cell, pya.Point(current_fuse_pin.x, anode_wires_y[senseamps_placed]+j1*via_step), 3, 4)

            current_sense_pin = sense_pin + current_senseamp_displ
            place_via_tower(efuse_array_cell, current_sense_pin, 1, 3)
            
            current_npreset_pin = npreset_pin + current_senseamp_displ
            place_via_tower(efuse_array_cell, current_npreset_pin, 1, 3)
            
            buf_displ = pya.Vector(current_capcell_x, senseamp_y) 
            senseamp_buf = pya.CellInstArray(buf_instance.cell_index(), pya.Trans(buf_displ))
            efuse_array_cell.insert(senseamp_buf)
            
            #connect senseamp to buf
            senseamp_buf_v_x = 1750
            place_via_tower(efuse_array_cell, current_out_pin, 1, 2)
            senseamp_buf_conn_h1 = pya.Box(current_out_pin.x-wire_width/2, current_out_pin.y-wire_width/2,
                                           current_out_pin.x+senseamp_buf_v_x+wire_width/2, current_out_pin.y+wire_width/2)
            senseamp_buf_conn_v = pya.Box(current_out_pin.x+senseamp_buf_v_x-wire_width/2, current_out_pin.y-wire_width/2,
                                           current_out_pin.x+senseamp_buf_v_x+wire_width/2, senseamp_y+buf_I_pin.y+wire_width/2)
            senseamp_buf_conn_h2 = pya.Box(current_out_pin.x+senseamp_buf_v_x-wire_width/2, senseamp_y+buf_I_pin.y-wire_width/2,
                                           buf_displ.x+buf_I_pin.x+wire_width/2, senseamp_y+buf_I_pin.y+wire_width/2)
            place_via_tower(efuse_array_cell, buf_displ+buf_I_pin, 1, 2)
            efuse_array_cell.shapes(metal2).insert(senseamp_buf_conn_h1)
            efuse_array_cell.shapes(metal2).insert(senseamp_buf_conn_v)
            efuse_array_cell.shapes(metal2).insert(senseamp_buf_conn_h2)
            efuse_array_cell.shapes(metal2_label).insert(pya.Text(f"DO[{senseamps_placed}]", pya.Trans(buf_displ+buf_Z_pin2)))
            place_via_tower(efuse_array_cell, buf_displ+buf_Z_pin2, 1, 2)
            m2_router_helper = pya.Box(current_capcell_x+buf_Z_pin2.x-wire_width/2, vdd_rail.bottom,
                                   current_capcell_x+buf_Z_pin2.x+wire_width/2, senseamp_y+buf_Z_pin2.y+wire_width/2)
            efuse_array_cell.shapes(metal2).insert(m2_router_helper)
            current_capcell_x += buf_instance.bbox().width() - cell_overlap
            
            

            senseamps_placed += 1
            continue
        else: 
            fillcap = pya.CellInstArray(fillcap_instance.cell_index(), pya.Trans(pya.Point(current_capcell_x, senseamp_y)))
            efuse_array_cell.insert(fillcap)
            current_capcell_x += fillcap_instance.bbox().width() - cell_overlap
            fillcap_num += 1

    endcap = pya.CellInstArray(endcap_instance.cell_index(), pya.Trans(pya.Point(current_capcell_x, senseamp_y)))
    efuse_array_cell.insert(endcap)
    current_capcell_x += endcap_instance.bbox().width()

    # add metal4 extra vss rail
    extra_vss_rail = pya.Box(stripe_left, extra_vss_rail_y-rail_width/2, current_capcell_x, extra_vss_rail_y+rail_width/2)
    efuse_array_cell.shapes(metal4).insert(extra_vss_rail)
    vss_connector = pya.Box(extra_vss_rail.right-rail_width, extra_vss_rail.bottom, extra_vss_rail.right, vss_rail.top)
    efuse_array_cell.shapes(metal4).insert(vss_connector)

    sense_wire = pya.Box(leftmost_sense_pin - pya.Vector(wire_width/2, wire_width/2), rightmost_sense_pin + pya.Vector(wire_width/2, wire_width/2))
    npreset_wire = pya.Box(leftmost_npreset_pin - pya.Vector(wire_width/2, wire_width/2), rightmost_npreset_pin + pya.Vector(wire_width/2, wire_width/2))
    efuse_array_cell.shapes(metal3).insert(sense_wire)
    efuse_array_cell.shapes(metal3).insert(npreset_wire)
    efuse_array_cell.shapes(metal3_label).insert(pya.Text("SENSE", pya.Trans(sense_wire.center())))
    efuse_array_cell.shapes(metal3_label).insert(pya.Text("nPRESET", pya.Trans(npreset_wire.center())))


    print(f"Number of filltie cells: {filltie_num}")
    print(f"Number of fillcap cells: {fillcap_num}")

    return efuse_array_cell
