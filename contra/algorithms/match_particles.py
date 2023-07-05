import numpy as np
from typing import Union, Callable
from unyt import unyt_array

def reorder_data(target_order_ids: np.ndarray, source_order_ids: np.ndarray, source_order_data: Union[unyt_array, np.ndarray, None] = None, missing_data_fill_value: Union[object, Callable[[int, np.int64], Union[object, None]], None] = None):
    # Copy the source arrays (they might be moddified)
    
    # Check all target ids are present in the source list
    #     if not, add the missing entries and assign null values by either calling function or assigning value

    # Filter source arrays by presence in the target order (remove missing particles)
    
    # Calculate sort orders and unsort order

    # Apply to data
    
    raise NotImplementedError("This needs doing!!!")#TODO: