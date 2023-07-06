import numpy as np
from typing import Union, Callable
from unyt import unyt_array
from ..tools import join_unyt_arrays

def reorder_data(target_ids: np.ndarray, source_ids: np.ndarray, source_data: Union[unyt_array, np.ndarray, None] = None, missing_data_fill_value: Union[object, Callable[[int, np.int64], Union[object, None]], None] = None):
    # Copy the source arrays (they might be moddified)
    target_order = target_ids.copy()
    source_order = source_ids.copy()
    if source_data is not None:
        source_order_data = source_data.copy()
    
    # Check all target ids are present in the source list
    #     if not, add the missing entries and assign null values by either calling function or assigning value
    missing_id_filter = ~np.isin(target_order, source_order)
    if missing_id_filter.sum() > 0:
        missing_ids = target_order[missing_id_filter]
        source_order = np.append(source_order, missing_ids)
        if source_data is not None:
            if isinstance(source_order_data, unyt_array):
                source_order_data = join_unyt_arrays(source_order_data, unyt_array([missing_data_fill_value(i, target_order[i]) for i in np.where(missing_id_filter)], units = source_order_data.units) if callable(missing_data_fill_value) else unyt_array([missing_data_fill_value for _ in range(missing_ids.shape[0])], units = source_order_data.units))
            else:
                source_order_data = np.append(source_order_data, np.array([missing_data_fill_value(i, target_order[i]) for i in np.where(missing_id_filter)], dtype = source_order_data.dtype) if callable(missing_data_fill_value) else np.full(missing_ids.shape[0], missing_data_fill_value, dtype = source_order_data.dtype))

    # Filter source arrays by presence in the target order (remove missing particles)
    modified_source_filter = np.isin(source_order, target_order)
    source_order = source_order[modified_source_filter]
    if source_data is not None:
        source_order_data = source_order_data[modified_source_filter]
    
    # Calculate sort orders and unsort order
    reordering_indexes = np.argsort(source_order)[np.argsort(np.argsort(target_order))]

    # Apply to data
    ordered_source_ids = source_order[reordering_indexes]

    if source_data is not None:
        ordered_source_data = source_order_data[reordering_indexes]
        return ordered_source_ids, ordered_source_data
    
    else:
        return ordered_source_ids