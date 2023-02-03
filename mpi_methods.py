"""
File: mpi_methods.py

Author: Christopher Rowe
Vesion: 1.2.1
Date:   24/01/2023

Provides functions for managing MPI processes.

Public API:

    broadcast_value(type, _, int)
    get_broardcast_value(type, int)
    broadcast_array(type, np.ndarray, int)
    get_broardcast_array(type, int)
    gather_values(type, _, type, int)
    gather_arrays(type, np.ndarray, type, int)
    all_gather_values(type, _, type)
    all_gather_arrays(type, np.ndarray, type)
    reduce_arrays(type, np.ndarray, type, type, int)
    all_reduce_arrays(type, np.ndarray, type, type)

Dependancies:

    mpi4py
    mpi_settings.py (local file)
    numpy

To import all methods, use the following:
from mpi_methods import is_root, get_equal_chunks, broadcast_value, get_broardcast_value, broadcast_array, get_broardcast_array, gather_values, gather_arrays, all_gather_values, all_gather_arrays, reduce_arrays, all_reduce_arrays
"""


from mpi_settings import MPI_Objects, get_MPI_avalible
import numpy as np

if get_MPI_avalible():
    from mpi4py import MPI

def __force_MPI_avalible(func):
    def wrapper(*args, **kwargs):
        if not get_MPI_avalible(): raise ImportError("MPI was not avalible.")
        return func(*args, **kwargs)
    return wrapper

@__force_MPI_avalible
def is_root(root_process = 0):
    return root_process == MPI_Objects.MPI_RANK

@__force_MPI_avalible
def get_equal_chunks(n_items: int):
    start = int(n_items * MPI_Objects.MPI_RANK / MPI_Objects.MPI_COMM_SIZE)
    end = int(n_items * (MPI_Objects.MPI_RANK + 1) / MPI_Objects.MPI_COMM_SIZE)
    return start if start < n_items else n_items , end if end < n_items else n_items

@__force_MPI_avalible
def broadcast_value(value_type: type, value = None, root = 0):
    if MPI_Objects.MPI_RANK == root:
        if value is None:
            raise ValueError("Value not provided by root process.")
        if not isinstance(value, value_type):
            raise TypeError("Value had the wrong type.")
        send_buffer = np.array([value], dtype = value_type)
        MPI_Objects.MPI_COMM.Bcast(send_buffer, root = root)
        return value
    else:
        recive_buffer = np.empty(1, dtype = value_type)
        MPI_Objects.MPI_COMM.Bcast(recive_buffer, root = root)
        return recive_buffer[0]

@__force_MPI_avalible
def get_broardcast_value(value_type: type, root = 0):
    if MPI_Objects.MPI_RANK == root:
        raise RuntimeError("Cannot recive a broardcast value on the root brocess for the broardcast!")
    return broadcast_value(value_type, root = root)

@__force_MPI_avalible
def broadcast_array(value_type: type, array = None, root = 0):
    if MPI_Objects.MPI_RANK == root:
        if array is None:
            raise ValueError("Value not provided by root process.")
        if not isinstance(array[0], value_type):
            raise TypeError("Input array had the wrong type.")
        broadcast_value(int, len(array), root)
        MPI_Objects.MPI_COMM.Bcast(array, root = root)
        return array
    else:
        recive_buffer = np.empty(get_broardcast_value(int, root), dtype = value_type)
        MPI_Objects.MPI_COMM.Bcast(recive_buffer, root = root)
        return recive_buffer

@__force_MPI_avalible
def get_broardcast_array(value_type: type, root = 0):
    if MPI_Objects.MPI_RANK == root:
        raise RuntimeError("Cannot recive a broardcast value on the root brocess for the broardcast!")
    return broadcast_array(value_type, root = root)

@__force_MPI_avalible
def gather_values(value_type: type, value, mpi_type, root = 0):
    if value_type is None:
        raise ValueError("'None' value provided for type argument.")
    if mpi_type is None:
        raise ValueError("'None' value provided for MPI type argument.")
    if value is None:
        raise ValueError("'None' value provided.")
    if not isinstance(value, value_type):
        raise TypeError("Input value had the wrong type.")
        
    receve_buffer = None
    if MPI_Objects.MPI_RANK == root:
        receve_buffer = np.empty(MPI_Objects.MPI_COMM_SIZE, dtype = value_type)
    sizes = np.ones(MPI_Objects.MPI_COMM_SIZE)
    offsets = np.zeros(MPI_Objects.MPI_COMM_SIZE)
    offsets[1:] = np.cumsum(sizes)[:-1]
    MPI_Objects.MPI_COMM.Gatherv(np.array([value], dtype = value_type),
                            [receve_buffer, list(sizes), list(offsets), mpi_type] if MPI_Objects.MPI_RANK == root else None,
                            root = root)
    return receve_buffer

@__force_MPI_avalible
def gather_arrays(value_type: type, array, mpi_type, root = 0):
    if is_root(): print("HIT 9")
    if value_type is None:
        raise ValueError("'None' value provided for type argument.")
    if mpi_type is None:
        raise ValueError("'None' value provided for MPI type argument.")
    if array is None:
        raise ValueError("'None' value provided.")
    try:
        if is_root(): print("HIT 10")
        array = np.array(array, dtype = value_type)
        if is_root(): print("HIT 11")
    except:
        raise TypeError("Unable to cooerse array input to a numpy array with the specified type.")
    
    if is_root(): print("HIT 12")
    if len(array) > 0 and not isinstance(array[0], value_type):
        raise TypeError("Input array had the wrong type.")#TODO: can this ever get called???
    if is_root(): print("HIT 13")
        
    number_per_process = gather_values(int, len(array), MPI.LONG, root = root)
    if is_root(): print("HIT 14")

    receve_buffer = None
    if MPI_Objects.MPI_RANK == root:
        print("HIT 15")
        receve_buffer = np.empty(sum(number_per_process), dtype = value_type)
        print("HIT 16")
        offsets = np.zeros(MPI_Objects.MPI_COMM_SIZE)
        print("HIT 17")
        offsets[1:] = np.cumsum(number_per_process)[:-1]
        print("HIT 18")

    MPI_Objects.MPI_COMM.Gatherv(array,
                    [receve_buffer, list(number_per_process), list(offsets), mpi_type] if MPI_Objects.MPI_RANK == root else None,
                    root = root)
    if is_root(): print("HIT 19")

    return receve_buffer

@__force_MPI_avalible
def all_gather_values(value_type: type, value, mpi_type):
    if value_type is None:
        raise ValueError("'None' value provided for type argument.")
    if mpi_type is None:
        raise ValueError("'None' value provided for MPI type argument.")
    if value is None:
        raise ValueError("'None' value provided.")
    if not isinstance(value, value_type):
        raise TypeError("Input value had the wrong type.")
        
    receve_buffer = np.empty(MPI_Objects.MPI_COMM_SIZE, dtype = value_type)
    sizes = np.ones(MPI_Objects.MPI_COMM_SIZE)
    offsets = np.zeros(MPI_Objects.MPI_COMM_SIZE)
    offsets[1:] = np.cumsum(sizes)[:-1]
    MPI_Objects.MPI_COMM.Allgatherv(np.array([value], dtype = value_type),
                                    [receve_buffer, list(sizes), list(offsets), mpi_type])
    return receve_buffer

@__force_MPI_avalible
def all_gather_arrays(value_type: type, array, mpi_type):
    if value_type is None:
        raise ValueError("'None' value provided for type argument.")
    if mpi_type is None:
        raise ValueError("'None' value provided for MPI type argument.")
    if array is None:
        raise ValueError("'None' value provided.")
    try:
        array = np.array(array, dtype = value_type)
    except:
        raise TypeError("Unable to cooerse array input to a numpy array with the specified type.")
    if len(array) > 0 and not isinstance(array[0], value_type):
        raise TypeError("Input array had the wrong type.")#TODO: can this ever get called???
        
    number_per_process = all_gather_values(int, len(array), MPI.LONG)

    receve_buffer = np.empty(sum(number_per_process), dtype = value_type)
    offsets = np.zeros(MPI_Objects.MPI_COMM_SIZE)
    offsets[1:] = np.cumsum(number_per_process)[:-1]

    MPI_Objects.MPI_COMM.Allgatherv(array,
                                    [receve_buffer, list(number_per_process), list(offsets), mpi_type])

    return receve_buffer

@__force_MPI_avalible
def reduce_arrays(value_type: type, array, mpi_operation, root = 0):
    if value_type is None:
        raise ValueError("'None' value provided for type argument.")
    if array is None:
        raise ValueError("'None' value provided.")
    try:
        array = np.array(array, dtype = value_type)
    except:
        raise TypeError("Unable to cooerse array input to a numpy array with the specified type.")
    if len(array) > 0 and not isinstance(array[0], value_type):
        raise TypeError("Input array had the wrong type.")#TODO: can this ever get called???

    receve_buffer = None
    if MPI_Objects.MPI_RANK == root:
        receve_buffer = np.empty(len(array), dtype = value_type)

    MPI_Objects.MPI_COMM.Reduce(array, receve_buffer, op = mpi_operation, root = root)

    return receve_buffer

@__force_MPI_avalible
def all_reduce_arrays(value_type: type, array, mpi_operation):
    if value_type is None:
        raise ValueError("'None' value provided for type argument.")
    if array is None:
        raise ValueError("'None' value provided.")
    try:
        array = np.array(array, dtype = value_type)
    except:
        raise TypeError("Unable to cooerse array input to a numpy array with the specified type.")
    if len(array) > 0 and not isinstance(array[0], value_type):
        raise TypeError("Input array had the wrong type.")#TODO: can this ever get called???

    receve_buffer = np.empty(len(array), dtype = value_type)

    MPI_Objects.MPI_COMM.Allreduce(array, receve_buffer, op = mpi_operation)

    return receve_buffer