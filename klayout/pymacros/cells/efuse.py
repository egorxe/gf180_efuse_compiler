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

########################################################################################################################
# EFuse Generator for GF180MCU
########################################################################################################################

import pya
from .draw_efuse import *

class efuse(pya.PCellDeclarationHelper):
    """
    eFuse Generator for GF180MCU
    """

    def __init__(self):

        # Important: initialize the super class
        super(efuse, self).__init__()
        self.param("Model", self.TypeString, "Model", default="gf180mcu_fd_pr__efuse",readonly=True)
        self.param("array_x", self.TypeInt, "Elements in x_direction", default=1)
        self.param("array_y", self.TypeInt, "Elements in y_direction", default=1)
        self.param("x_spacing", self.TypeDouble, "Spacing in x_direction", default=1,unit="um")
        self.param("y_spacing", self.TypeDouble, "Spacing in y_direction", default=1,unit="um")


    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "efuse"

    def coerce_parameters_impl(self):
        # We employ coerce_parameters_impl to decide whether the handle or the
        # numeric parameter has changed (by comparing against the effective
        # radius ru) and set ru to the effective radius. We also update the
        # numerical value or the shape, depending on which on has not changed.
        pass


    def can_create_from_shape_impl(self):
        # Implement the "Create PCell from shape" protocol: we can use any shape which
        # has a finite bounding box
        # return self.shape.is_box() or self.shape.is_polygon() or self.shape.is_path()
        pass

    def parameters_from_shape_impl(self):
        # Implement the "Create PCell from shape" protocol: we set r and l from the shape's
        # bounding box width and layer
        # self.r = self.shape.bbox().width() * self.layout.dbu / 2
        # self.l = self.layout.get_info(self.layer)
        pass

    def transformation_from_shape_impl(self):
        # Implement the "Create PCell from shape" protocol: we use the center of the shape's
        # bounding box to determine the transformation
        # return pya.Trans(self.shape.bbox().center())
        pass

    def produce_impl(self):

        # This is the main part of the implementation: create the layout

        self.percision = 1/self.layout.dbu
        efuse_instance = draw_efuse(layout=self.layout)
        write_cells = pya.CellInstArray(efuse_instance.cell_index(), pya.Trans(pya.Point(0, 0)),
                              pya.Vector(self.x_spacing*self.percision, 0), pya.Vector(0, self.y_spacing*self.percision),self.array_x , self.array_y)

        self.cell.flatten(1)
        self.cell.insert(write_cells)
        self.layout.cleanup()

class efuse_senseamp(pya.PCellDeclarationHelper):

    def __init__(self):
        super(efuse_senseamp, self).__init__()

    def display_text_impl(self):
        return "efuse_senseamp"

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape_impl(self):
        pass

    def parameters_from_shape_impl(self):
        pass

    def transformation_from_shape_impl(self):
        pass

    def produce_impl(self):

        self.percision = 1/self.layout.dbu
        efuse_senseamp_instance = draw_efuse_senseamp(layout=self.layout)
        write_cells = pya.CellInstArray(efuse_senseamp_instance.cell_index(), pya.Trans(pya.Point(0, 0)))

        self.cell.flatten(1)
        self.cell.insert(write_cells)
        self.layout.cleanup()

class efuse_bitline(pya.PCellDeclarationHelper):

    def __init__(self):
        super(efuse_bitline, self).__init__()
        self.param("n_bitcells", self.TypeInt, "Number of bitcells", default=4)


    def display_text_impl(self):
        return "efuse_bitline"

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape_impl(self):
        pass

    def parameters_from_shape_impl(self):
        pass

    def transformation_from_shape_impl(self):
        pass

    def produce_impl(self):

        efuse_bitline_instance = draw_efuse_bitline(layout=self.layout, n_bitcells=self.n_bitcells)
        write_cells = pya.CellInstArray(efuse_bitline_instance.cell_index(), pya.Trans(pya.Point(0, 0)))

        self.cell.flatten(1)
        self.cell.insert(write_cells)
        self.layout.cleanup()

class efuse_array(pya.PCellDeclarationHelper):

    def __init__(self):
        super(efuse_array, self).__init__()
        self.param("n_bitlines", self.TypeInt, "Number of bitlines", default=4)
        self.param("n_bitcells", self.TypeInt, "Number of bitcells", default=4)

    def display_text_impl(self):
        return "efuse_array"

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape_impl(self):
        pass

    def parameters_from_shape_impl(self):
        pass

    def transformation_from_shape_impl(self):
        pass

    def produce_impl(self):

        efuse_array_instance = draw_efuse_array(self.layout, self.n_bitlines, self.n_bitcells)
        write_cells = pya.CellInstArray(efuse_array_instance.cell_index(), pya.Trans(pya.Point(0, 0)))

        self.cell.flatten(1)
        self.cell.insert(write_cells)
        self.cell.flatten(1, True)
        self.layout.cleanup()
