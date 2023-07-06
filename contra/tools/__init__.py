import unyt
import numpy as np
from typing import List

def join_unyt_arrays(*arrays: List[unyt.unyt_array]):
    data_unit = arrays[0].units
    lengths = []
    for array in arrays:
        if array.units != data_unit:
            raise ValueError("Inconsistent units on data provided.")
        lengths.append(array.shape[0])

    offsets = np.empty((len(lengths) + 1,), dtype = int)
    offsets[0] = 0
    offsets[1:] = np.array(lengths).cumsum()
    return_array = unyt.unyt_array(np.empty((lengths.sum(),), dtype = arrays[0].dtype), units = data_unit)

    for i, array in arrays:
        return_array[offsets[i] : offsets[i + 1]] = array

    return return_array
