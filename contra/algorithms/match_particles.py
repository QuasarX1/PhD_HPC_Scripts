import numpy as np
from typing import Union, List, Tuple, Callable, Optional
from unyt import unyt_array
from ..tools import join_unyt_arrays

def reorder_data(target_ids: np.ndarray, source_ids: np.ndarray, source_data: Union[unyt_array, np.ndarray, List[Union[unyt_array, np.ndarray]]] = [], missing_data_fill_value: Union[object, Callable[[int, int, np.int64], Union[object, None]], None] = None) -> Tuple[np.ndarray, np.ndarray, Optional[Union[unyt_array, np.ndarray]]]:
    """
    missing_data_fill_value when callable takes: (int -> index of dataset, int -> index of dataset item, np.int64 -> item source id)
    """
    
    # Copy the source arrays (they might be moddified)
    target_order = target_ids.copy()
    source_order = source_ids.copy()
    handle_data = False
    source_order_data = []
    if source_data != [] and source_data is not None:# Check for None in case user tries to specify its absence without reading the type hint
        handle_data = True
        if not isinstance(source_data, list):
            source_order_data = [source_data.copy()]
        else:
            source_order_data = [data.copy() for data in source_data]
    
    # Check all target ids are present in the source list
    #     if not, add the missing entries and assign null values by either calling function or assigning value
    missing_id_filter = ~np.isin(target_order, source_order)
    if missing_id_filter.sum() > 0:
        missing_ids = target_order[missing_id_filter]
        source_order = np.append(source_order, missing_ids)
        if handle_data:
            for dataset_index in range(len(source_order_data)):
                if isinstance(source_order_data[dataset_index], unyt_array):
                    source_order_data[dataset_index] = join_unyt_arrays(source_order_data[dataset_index], unyt_array([missing_data_fill_value(dataset_index, i, target_order[i]) for i in np.where(missing_id_filter)], units = source_order_data[dataset_index].units) if callable(missing_data_fill_value) else unyt_array([missing_data_fill_value for _ in range(missing_ids.shape[0])], units = source_order_data[dataset_index].units))
                else:
                    source_order_data[dataset_index] = np.append(source_order_data[dataset_index], np.array([missing_data_fill_value(dataset_index, i, target_order[i]) for i in np.where(missing_id_filter)], dtype = source_order_data[dataset_index].dtype) if callable(missing_data_fill_value) else np.full(missing_ids.shape[0], missing_data_fill_value, dtype = source_order_data[dataset_index].dtype))

    # Filter source arrays by presence in the target order (remove missing particles)
    modified_source_filter = np.isin(source_order, target_order)
    source_order = source_order[modified_source_filter]
    if handle_data:
        for dataset_index in range(len(source_order_data)):
            source_order_data[dataset_index] = source_order_data[dataset_index][modified_source_filter]
    
    # Calculate sort orders and unsort order
    reordering_indexes = np.argsort(source_order)[np.argsort(np.argsort(target_order))]

    # Apply to data
    ordered_source_ids = source_order[reordering_indexes]

    if handle_data:
        ordered_source_data = [source_order_data[dataset_index][reordering_indexes] for dataset_index in range(len(source_order_data))]
        return ~missing_id_filter, ordered_source_ids, *ordered_source_data
    
    else:
        return ~missing_id_filter, ordered_source_ids