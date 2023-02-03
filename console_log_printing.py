"""
File: console_log_printing.py

Author: Christopher Rowe
Vesion: 1.3.3
Date:   24/01/2023

Provides printing functions that are MPI aware and have verbose
and debug variants.

Public API:

    get_verbose()
    set_verbose(bool)
    enable_verbose()
    disable_verbose()
    toggle_verbose()
    get_debug()
    set_debug(bool)
    enable_debug()
    disable_debug()
    toggle_debug()
    print_info()
    print_info(str, *args, **kwargs)
    print_verbose_info(str, *args, **kwargs)
    print_warning(str, *args, **kwargs)
    print_verbose_warning(str, *args, **kwargs)
    print_error(str, *args, **kwargs)
    print_verbose_error(str, *args, **kwargs)
    print_debug(str, *args, **kwargs)

Dependancies:

    mpi4py (optional)
    mpi_methods.py (local file, optional)
    mpi_settings.py (local file, optional)

To import all printing methods, use:
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
"""

from mpi_settings import MPI_Objects, get_MPI_avalible

class __Settings(object):
    VERBOSE_ENABLED = False
    DEBUG_ENABLED = False
    CUDA_THREADS_PER_BLOCK = 512

def get_verbose(): return __Settings.VERBOSE_ENABLED
def set_verbose(state: bool): __Settings.VERBOSE_ENABLED = state
def enable_verbose(): set_verbose(True)
def disable_verbose(): set_verbose(False)
def toggle_verbose(): set_verbose(not get_verbose())

def get_debug(): return __Settings.DEBUG_ENABLED
def set_debug(state: bool): __Settings.DEBUG_ENABLED = state
def enable_debug(): set_debug(True)
def disable_debug(): set_debug(False)
def toggle_debug(): set_debug(not get_debug())

def get_cuda_threads_per_block(): return __Settings.CUDA_THREADS_PER_BLOCK



def __debug_wrapper(func):
    def wrapper(*args, **kwargs):
        if __Settings.DEBUG_ENABLED:
            if "flush" not in kwargs:
                kwargs["flush"] = True
        return func(*args, **kwargs)
    return wrapper

def __mpi_wrapper(func):
    mpi_rank_insert = f" ({MPI_Objects.MPI_RANK})" if get_MPI_avalible() else ""
    def wrapper(*args, **kwargs):
        if get_MPI_avalible():
            if "flush" not in kwargs:
                kwargs["flush"] = True
        return func(mpi_rank_insert, *args, **kwargs)
    return wrapper

__print_custom_newline_spaces = "                "
def __print_custom_newline_format(s):
    return str(s).replace("\n", f"\n{__print_custom_newline_spaces}")

@__mpi_wrapper
@__debug_wrapper
def print_info(mpi_rank_insert, firstValue = "", *args, **kwargs):
    if get_MPI_avalible():
        if "flush" not in kwargs:
            kwargs["flush"] = True
    print(f"--|| INFO ||--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)

def print_verbose_info(firstValue = "", *args, **kwargs):
    if __Settings.VERBOSE_ENABLED:
        print_info(firstValue, *args, **kwargs)

@__mpi_wrapper
@__debug_wrapper
def print_warning(mpi_rank_insert, firstValue = "", *args, **kwargs):
    print(f"--¿¿ WARN ??--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)

def print_verbose_warning(firstValue = "", *args, **kwargs):
    if __Settings.VERBOSE_ENABLED:
        print_warning(firstValue, *args, **kwargs)

@__mpi_wrapper
@__debug_wrapper
def print_error(mpi_rank_insert, firstValue = "", *args, **kwargs):
    print(f"--!! ERRO !!--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)

def print_verbose_error(firstValue = "", *args, **kwargs):
    if __Settings.VERBOSE_ENABLED:
        print_error(firstValue, *args, **kwargs)

@__mpi_wrapper
@__debug_wrapper
def print_debug(mpi_rank_insert, firstValue = "", *args, **kwargs):
    if __Settings.DEBUG_ENABLED:
        print(f"--<< DEBG >>--{mpi_rank_insert}  {__print_custom_newline_format(firstValue)}", *[__print_custom_newline_format(arg) for arg in args], **kwargs)
