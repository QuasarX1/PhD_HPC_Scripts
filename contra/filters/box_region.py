"""
File: box_region.py

Author: Christopher Rowe
Vesion: 1.5.3
Date:   27/03/2023

Convinence functions for handeling spatial regions within a cosmological box.

Public API:

    BoxRegion (class)
    BoxRegion.get_command_params(bool)

Dependancies:

    QuasarCode
    numpy
    swiftsimio (optional)
    typing
    unyt (optional)
"""

import numpy as np
from typing import Union, List

SWIFTSIMIO_AVALIBLE = False
try:
    import swiftsimio as sw
    import unyt
    SWIFTSIMIO_AVALIBLE = True
except ImportError: pass


class BoxRegion(object):
    def __init__(self, centre_x_position = None, centre_y_position = None, centre_z_position = None, side_length = None, x_min = None, x_max = None, y_min = None, y_max = None, z_min = None, z_max = None, x_side_length = None, y_side_length = None, z_side_length = None, **kwargs):
        if x_side_length is None:
            x_side_length = side_length
        if y_side_length is None:
            y_side_length = side_length
        if z_side_length is None:
            z_side_length = side_length
            
        x_half_side_length = x_side_length / 2 if x_side_length is not None else None
        y_half_side_length = y_side_length / 2 if y_side_length is not None else None
        z_half_side_length = z_side_length / 2 if z_side_length is not None else None
        
        if x_min is not None: self.__x_min = x_min
        elif centre_x_position is not None and x_side_length is not None: self.__x_min = centre_x_position - x_half_side_length
        elif x_max is not None and x_side_length is not None: self.__x_min = x_min - x_side_length
        elif x_side_length == np.inf: self.__x_min = -np.inf
        else: self.__x_min = None
        if x_max is not None: self.__x_max = x_max
        elif centre_x_position is not None and x_side_length is not None: self.__x_max = centre_x_position + x_half_side_length
        elif x_min is not None and x_side_length is not None: self.__x_max = x_min + x_side_length
        elif x_side_length == np.inf: self.__x_max = np.inf
        else: self.__x_max = None

        if y_min is not None: self.__y_min = y_min
        elif centre_y_position is not None and y_side_length is not None: self.__y_min = centre_y_position - y_half_side_length
        elif y_max is not None and y_side_length is not None: self.__y_min = y_min - y_side_length
        elif y_side_length == np.inf: self.__y_min = -np.inf
        else: self.__y_min = None
        if y_max is not None: self.__y_max = y_max
        elif centre_y_position is not None and y_side_length is not None: self.__y_max = centre_y_position + y_half_side_length
        elif y_min is not None and y_side_length is not None: self.__y_max = y_min + y_side_length
        elif y_side_length == np.inf: self.__y_max = np.inf
        else: self.__y_max = None

        if z_min is not None: self.__z_min = z_min
        elif centre_z_position is not None and z_side_length is not None: self.__z_min = centre_z_position - z_half_side_length
        elif z_max is not None and z_side_length is not None: self.__z_min = z_min - z_side_length
        elif z_side_length == np.inf: self.__z_min = -np.inf
        else: self.__z_min = None
        if z_max is not None: self.__z_max = z_max
        elif centre_z_position is not None and z_side_length is not None: self.__z_max = centre_z_position + z_half_side_length
        elif z_min is not None and z_side_length is not None: self.__z_max = z_min + z_side_length
        elif z_side_length == np.inf: self.__z_max = np.inf
        else: self.__z_max = None
        
        self.__centre = None
        self.__side_length = None
        self.__set_calculated_attributes()

    def __set_calculated_attributes(self):
        self.__centre = [((self.__x_min + self.__x_max) / 2) if (self.__x_min is not None and self.__x_max is not None) else None,
                         ((self.__y_min + self.__y_max) / 2) if (self.__y_min is not None and self.__y_max is not None) else None,
                         ((self.__z_min + self.__z_max) / 2) if (self.__z_min is not None and self.__z_max is not None) else None]
        self.__side_length = [self.__x_max - self.__x_min if (self.__x_min is not None and self.__x_max is not None) else None,
                              self.__y_max - self.__y_min if (self.__y_min is not None and self.__y_max is not None) else None,
                              self.__z_max - self.__z_min if (self.__z_min is not None and self.__z_max is not None) else None]
        if self.__side_length[0] == self.__side_length[1] and self.__side_length[1] == self.__side_length[2]:
            self.__side_length = self.__side_length[0]

    def make_array_filter(self, coord_2d_arr: np.array):
        arr_filter = np.full(coord_2d_arr.shape[:-1], True, bool)
        if self.__x_min is not None:
            arr_filter = arr_filter & (coord_2d_arr[:, 0] >= self.__x_min)
        if self.__x_max is not None:
            arr_filter = arr_filter & (coord_2d_arr[:, 0] <= self.__x_max)
        if self.__y_min is not None:
            arr_filter = arr_filter & (coord_2d_arr[:, 1] >= self.__y_min)
        if self.__y_max is not None:
            arr_filter = arr_filter & (coord_2d_arr[:, 1] <= self.__y_max)
        if self.__z_min is not None:
            arr_filter = arr_filter & (coord_2d_arr[:, 2] >= self.__z_min)
        if self.__z_max is not None:
            arr_filter = arr_filter & (coord_2d_arr[:, 2] <= self.__z_max)
        return arr_filter

    def constrain_mask(self, mask):
        if not SWIFTSIMIO_AVALIBLE:
            raise NotImplementedError("The swiftsimio and unyt package is required to use this method.")

        box_size = mask.metadata.boxsize
        box_size_units = box_size[0].units.__repr__()
        
        return mask.constrain_spatial([[unyt.unyt_quantity(self.__x_min if (self.__x_min is not None and self.__x_min != -np.inf) else 0, box_size[0].units.__repr__()), unyt.unyt_quantity(self.__x_max if (self.__x_max is not None and self.__x_max != np.inf) else box_size[0], box_size_units)],
                                       [unyt.unyt_quantity(self.__y_min if (self.__y_min is not None and self.__y_min != -np.inf) else 0, box_size[1].units.__repr__()), unyt.unyt_quantity(self.__y_max if (self.__y_max is not None and self.__y_max != np.inf) else box_size[1], box_size_units)],
                                       [unyt.unyt_quantity(self.__z_min if (self.__z_min is not None and self.__z_min != -np.inf) else 0, box_size[2].units.__repr__()), unyt.unyt_quantity(self.__z_max if (self.__z_max is not None and self.__z_max != np.inf) else box_size[2], box_size_units)]])

    def complete_bounds_from_coords(self, coord_2d_arr: np.ndarray):
        if self.__x_min is None: self.x_min = np.min(coord_2d_arr[:, 0])
        if self.__x_max is None: self.x_max = np.max(coord_2d_arr[:, 0])
        if self.__y_min is None: self.y_min = np.min(coord_2d_arr[:, 1])
        if self.__y_max is None: self.y_max = np.max(coord_2d_arr[:, 1])
        if self.__z_min is None: self.z_min = np.min(coord_2d_arr[:, 2])
        if self.__z_max is None: self.z_max = np.max(coord_2d_arr[:, 2])
        self.__set_calculated_attributes()

    @property
    def x_min(self) -> float:
        return self.__x_min
    @x_min.setter
    def x_min(self, value):
        if self.__x_min is not None:
            raise RuntimeError("You may not change the value of x_min when it has a value other than None.")
        self.__x_min = value
        self.__set_calculated_attributes()

    @property
    def x_max(self) -> float:
        return self.__x_max
    @x_max.setter
    def x_max(self, value):
        if self.__x_max is not None:
            raise RuntimeError("You may not change the value of x_max when it has a value other than None.")
        self.__x_max = value
        self.__set_calculated_attributes()

    @property
    def y_min(self) -> float:
        return self.__y_min
    @y_min.setter
    def y_min(self, value):
        if self.__y_min is not None:
            raise RuntimeError("You may not change the value of y_min when it has a value other than None.")
        self.__y_min = value
        self.__set_calculated_attributes()

    @property
    def y_max(self) -> float:
        return self.__y_max
    @y_max.setter
    def y_max(self, value):
        if self.__y_max is not None:
            raise RuntimeError("You may not change the value of y_max when it has a value other than None.")
        self.__y_max = value
        self.__set_calculated_attributes()

    @property
    def z_min(self) -> float:
        return self.__z_min
    @z_min.setter
    def z_min(self, value):
        if self.__z_min is not None:
            raise RuntimeError("You may not change the value of z_min when it has a value other than None.")
        self.__z_min = value
        self.__set_calculated_attributes()

    @property
    def z_max(self) -> float:
        return self.__z_max
    @z_max.setter
    def z_max(self, value):
        if self.__z_max is not None:
            raise RuntimeError("You may not change the value of z_max when it has a value other than None.")
        self.__z_max = value
        self.__set_calculated_attributes()

    @property
    def side_length(self) -> Union[float, List[float]]:
        return self.__side_length

    @property
    def centre(self):
        return self.__centre

    @staticmethod
    def get_command_params(use_abbriviation = True):
        return [
            ["centre-x-position", "x" if use_abbriviation else None,  "Position of the bounding box centre on\nthe x-axis (in Mpc).",               False, False, float, None],
            ["centre-y-position", "y" if use_abbriviation else None,  "Position of the bounding box centre on\nthe y-axis (in Mpc).",               False, False, float, None],
            ["centre-z-position", "z" if use_abbriviation else None,  "Position of the bounding box centre on\nthe z-axis (in Mpc).",               False, False, float, None],
            ["side-length",       "w" if use_abbriviation else None,  "Side length of the bounding box (in Mpc).",                                  False, False, float, None],
            ["x-min",             None,                               "X-axis minimum bound (in Mpc).",                                             False, False, float, None],
            ["x-max",             None,                               "X-axis maximum bound (in Mpc).",                                             False, False, float, None],
            ["y-min",             None,                               "Y-axis minimum bound (in Mpc).",                                             False, False, float, None],
            ["y-max",             None,                               "Y-axis maximum bound (in Mpc).",                                             False, False, float, None],
            ["z-min",             None,                               "Z-axis minimum bound (in Mpc).",                                             False, False, float, None],
            ["x-side-length",     None,                               "Overrides the side-length paramiters for the X-axis minimum only (in Mpc).", False, False, float, None],
            ["y-side-length",     None,                               "Overrides the side-length paramiters for the Y-axis minimum only (in Mpc).", False, False, float, None],
            ["z-side-length",     None,                               "Overrides the side-length paramiters for the Z-axis minimum only (in Mpc).", False, False, float, None]]

    @staticmethod
    def get_command_param_names():
        return [param[0].replace("-", "_") for param in BoxRegion.get_command_params()]

    @staticmethod
    def filter_command_params(**kwargs):
        valid_param_names = BoxRegion.get_command_param_names()
        return {param_name : kwargs[param_name] for param_name in kwargs if param_name in valid_param_names}
