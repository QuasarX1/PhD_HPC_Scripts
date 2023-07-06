"""
File: save_swift_snap_field.py

Author: Christopher Rowe
Vesion: 1.2.1
Date:   24/04/2023

Save new fields to disk.

Public API:

    save_particle_fields(str, str, int, swiftsimio.SWIFTDataset, Union[str, None])

Dependancies:

    h5py
    numpy
    QuasarCode
    sph_map.py (local file)
    swift_data_expression.py (local file)
    swiftsimio
    sys
    typing
"""

import h5py
import numpy as np
import swiftsimio as sw
from typing import Union, List
from .swift_parttype_enum import PartType
from .swift_data_expression import parse_string

UNSIGNED_INT_8 = "u1"
SIGNED_INT_8 = "i1"
UNSIGNED_INT_16 = "u2"
SIGNED_INT_16 = "i2"
UNSIGNED_INT_32 = "u4"
SIGNED_INT_32 = "i4"
UNSIGNED_INT_64 = "u8"
SIGNED_INT_64 = "i8"

SIGNED_FLOAT_64 = np.float64#"H5T_IEEE_F64LE"

def get_cgs_conversions(field_name: str, part_type: PartType, current_file: sw.SWIFTDataset) -> List[float]:
    value = None
    with h5py.File(current_file.metadata.filename, "r") as file:
        value = [file[f"/PartType{part_type.value}/" + field_name].attrs["Conversion factor to CGS (not including cosmological corrections)"],
                 file[f"/PartType{part_type.value}/" + field_name].attrs["Conversion factor to physical CGS (including cosmological corrections)"]
                ]
    return value

def save_particle_fields(field_name: Union[str, List[str]], description: Union[str, List[str]], part_type: Union[PartType, List[PartType]], current_file: sw.SWIFTDataset, new_file: Union[str, None], template_field: Union[str, List[str]] = "Masses", datatype_override: Union[str, List[str]] = ""):
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
    if isinstance(template_field, str):
        template_field = [template_field] * len(field_name)
    if isinstance(datatype_override, str):
        datatype_override = [datatype_override] * len(field_name)

    if new_file is not None and new_file != "":
        with open(current_file.metadata.filename, "rb") as file:
            data = file.read()
        with open(new_file, "wb") as file:
            file.write(data)
    else:
        new_file = current_file.metadata.filename

    with h5py.File(new_file, "r+") as file:
        for i in range(len(field_name)):
            template_field_path = f"/PartType{part_type[i].value}/" + template_field[i]

            #new_field = "/" + ("" if part_type is None else f"PartType{part_type[i].value}") + "/" + field_name
            new_field = f"/PartType{part_type[i].value}/" + field_name[i]
            
##            file.copy(f"/PartType{part_type[i].value}/" + "Masses", new_field)
#            file.copy(f"/PartType{part_type[i].value}/" + template_field[i], new_field)
#            if datatype_override[i] is not None and datatype_override[i] != "":
#                file[new_field].dtype = datatype_override[i]

            file.create_dataset(new_field,
                                shape = file[template_field_path].shape,
                                dtype = file[template_field_path].dtype if datatype_override[i] is None or datatype_override[i] == "" else datatype_override[i])
            
            for attribute_key in file[template_field_path].attrs.keys():
                if attribute_key not in list(file[new_field].attrs):
                    file[new_field].attrs[attribute_key] = file[template_field_path].attrs[attribute_key]

            

            file[new_field][:] = parse_string(field_name[i], part_type[i].get_dataset(current_file))
            string_type = h5py.string_dtype("ascii", len(description[i]))
            file[new_field].attrs["Description"] = np.array(description[i], dtype = string_type)