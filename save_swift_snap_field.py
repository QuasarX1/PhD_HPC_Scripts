"""
File: save_swift_snap_field.py

Author: Christopher Rowe
Vesion: 1.0.0
Date:   21/03/2023

Save new fields to disk.

Public API:

    save_particle_fields(str, str, int, swiftsimio.SWIFTDataset, Union[str, None])

Dependancies:

    h5py
    numpy
    sph_map.py (local file)
    swift_data_expression.py (local file)
    os
    swiftsimio
    sys
    typing
"""

import h5py
import numpy as np
import os
import swiftsimio as sw
import sys
from typing import Union, List

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from sph_map import PartType
from swift_data_expression import parse_string

def save_particle_fields(field_name: Union[str, List[str]], description: Union[str, List[str]], part_type: Union[PartType, List[PartType]], current_file: sw.SWIFTDataset, new_file: Union[str, None]):
    """
    function save_particle_field

    Adds a new on-disk field to the dataset of the specified particle type.

    Paramiters:
                       str|list field_name   -> The name(s) of the field to save to disk.
                       str|list description  -> The discription(s) to add to the dataset.
                       int|list part_type    -> The particle type dataset(s) the field lies within.
        swiftsimio.SWIFTDataset current_file -> The loaded current dataset.
                       str|None new_file     -> New file to create. Set to None if the origanal should be overwritten.
    """
    if isinstance(field_name, str):
        field_name = [field_name]
    if isinstance(description, str):
        description = [description]
    if isinstance(part_type, PartType):
        part_type = [part_type] * len(field_name)

    if new_file is not None and new_file != "":
        with open(current_file.metadata.filename, "rb") as file:
            data = file.read()
        with open(new_file, "wb") as file:
            file.write(data)
    else:
        new_file = data.metadata.filename

    with h5py.File(new_file, "r+") as file:
        for i in range(len(field_name)):
            #new_field = "/" + ("" if part_type is None else f"PartType{part_type[i].value}") + "/" + field_name
            new_field = f"/PartType{part_type[i].value}/" + field_name[i]
            
            file.copy(f"/PartType{part_type[i].value}/" + "Masses", new_field)

            file[new_field][:] = parse_string(field_name[i], part_type[i].get_dataset(current_file))
            string_type = h5py.string_dtype("ascii", len(description[i]))
            file[new_field].attrs["Description"] = np.array(description[i], dtype = string_type)