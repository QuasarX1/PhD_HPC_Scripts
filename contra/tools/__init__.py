from .unit_string_formatter import format_unit_string

import unyt
import numpy as np
from typing import List
from datetime import timedelta
from time import time

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

class Stopwatch(object):
    def __init__(self):
        self.__set = False
        self.__running = False
        self.__start_time = None
        self.__stop_time = None
        self.reset()

    def start(self):
        if self.__set:
            self.__set = False
            self.__running = True
            self.__start_time = time()

    def stop(self):
        call_time = time()# Used for accuracy
        if self.__running:
            self.__stop_time = call_time
            self.__running = False

    def reset(self, force = False):
        if not self.__set and (not self.__running or force):
            self.__set = True
            self.__running = False
            self.__start_time = None
            self.__stop_time = None
    
    @property
    def ready(self) -> bool:
        return self.__set
    
    @property
    def running(self) -> bool:
        return self.__running
    
    @property
    def elapsed(self) -> timedelta:
        call_time = time()# Used for accuracy if the timer is still running
        if self.__set:
            return timedelta(seconds = 0)
        elif self.__running:
            return timedelta(seconds = call_time - self.__start_time)
        else:
            return timedelta(seconds = self.__stop_time - self.__start_time)
