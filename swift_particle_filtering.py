"""
File: swift_particle_filtering.py

Author: Christopher Rowe
Vesion: 1.0.0
Date:   29/03/2023

Computes filters for SWIFT particle datasets.

Public API:

    class ParticleFilter

Dependancies:

    numpy
    QuasarCode
    sph_map.py (local file)
    swift_data_expression.py (local file)
    swiftsimio
    typing
"""

import numpy as np
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from typing import List, Union

source_file_relitive_add_to_path(__file__)
from swift_data_expression import parse_string
from swift_parttype_enum import PartType

class ParticleFilter(object):
    @staticmethod
    def _calculate_filter(data_root_node: sw.SWIFTDataset, limit_fields: Union[str, List[str]], limit_units: Union[str, List[str]], limits_min: Union[None, float, List[float]] = None, limits_max: Union[None, float, List[float]] = None, **kwargs):
        # Handle formatting for there only being one item
        if isinstance(limit_fields, str):
            limit_fields = [limit_fields]
            limit_units = [limit_units]
            if limits_min is not None:
                limits_min = [limits_min]
            if limits_max is not None:
                limits_max = [limits_max]

        manual_filter = np.full(parse_string(limit_fields[0], data_root_node).shape[0], True)

        for i, field in enumerate(limit_fields):
            field_value = parse_string(field, data_root_node).to(limit_units[i])
            if limits_min is not None and limits_min[i] is not None:
                manual_filter = manual_filter & (field_value >= limits_min[i])
            if limits_max is not None and limits_max[i] is not None:
                manual_filter = manual_filter & (field_value <= limits_max[i])

        return manual_filter

    def __init__(self, data_root_node: sw.SWIFTDataset, limit_fields: Union[str, List[str]], limit_units: Union[str, List[str]], limits_min: Union[None, float, List[float]] = None, limits_max: Union[None, float, List[float]] = None):
        self.__filter = ParticleFilter._calculate_filter(data_root_node, limit_fields, limit_units, limits_min, limits_max)
        self.__n_items = self.__filter.sum()

    def __call__(self, dataset):
        return dataset[self.__filter]
    
    def __len__(self):
        return self.__n_items

    @property
    def numpy_filter(self):
        return self.__filter
    
    def update(self, additional_filter: np.ndarray):
        len_new_items = additional_filter.shape[0]
        len_self_items = self.__filter.shape[0]

        if len_new_items > len_self_items:
            # New filter is a larger array than the current filter! This is not compattible.
            raise ValueError("The new filter has a length of {}. This is larger than (and therfore, incompatible with) the current filter size of {}.".format(len_new_items, len_self_items))
        elif len_new_items == len_self_items:
            # Same lengths, just do a simple logical and.
            #print(self.__filter)
            #print(type(self.__filter))
            #print(self.__filter[0])
            #print(additional_filter)
            #print(type(additional_filter))
            #print(additional_filter[0])
            self.__filter = self.__filter & additional_filter
            self.__n_items = self.__filter.sum()
        elif len_new_items != len(self):
            # New filter has a size that isn't consistent with the currently filtered subset.
            raise ValueError("The new filter has a length of {}. This is smaller than the current filter size of {}, but also not the same as (and therfore, incompatible with) the current filtered subset size of {}.".format(len_new_items, len_self_items, len(self)))
        elif additional_filter.sum() > 0:
            # Apply to the filtered subset.
            self.__filter[np.where(self.__filter)[0][additional_filter == False]] = False
            self.__n_items = self.__filter.sum()
        else:
            # New filter was valid, but would remove all items. Just overwrite internal filter.
            self.self.__filter = np.full_like(self.__filter, False)
            self.__n_items = 0

    @staticmethod
    def passthrough_filter(data_file: sw.SWIFTDataset, part_type: PartType):
        return ParticleFilter(part_type.get_dataset(data_file), "masses", "Msun", None, None)

    @staticmethod
    def get_command_params():
        return [["limit-fields", None, "Names (or expressions with no spaces) as a semicolon seperated list of the data set to be used for filtering the list of particles.", False, False, ScriptWrapper.make_list_converter(";"), None],
                ["limit-units", None, "Unit expression for the limits specified. Uses a semicolon seperated list.", False, False, ScriptWrapper.make_list_converter(";"), None],
                ["limits-min", None, "", False, False, ScriptWrapper.make_list_converter(";", float), None],
                ["limits-max", None, "", False, False, ScriptWrapper.make_list_converter(";", float), None]]
    
    @staticmethod
    def check_limits_present(limit_fields: Union[None, str, List[str]] = None, **kwargs):
        return limit_fields is not None
