"""
File: mpi_settings.py

Author: Christopher Rowe
Vesion: 1.0.1
Date:   16/01/2023

Provides functions for managing MPI processes.

Public API:

    MPI_Objects (class)
    get_MPI_avalible

Dependancies:

    mpi4py (optional)
    numpy
    warnings
"""

import warnings

class MPI_Objects(object):
    MPI_COMM = None
    MPI_COMM_SIZE = None
    MPI_RANK = None

__MPI_AVALIBLE = False
try:
    from mpi4py import MPI
    MPI_Objects.MPI_COMM = MPI.COMM_WORLD
    MPI_Objects.MPI_RANK = MPI_Objects.MPI_COMM.Get_rank()
    MPI_Objects.MPI_COMM_SIZE = int(MPI_Objects.MPI_COMM.Get_size())
    __MPI_AVALIBLE = True
except:
    __MPI_AVALIBLE = False
    warnings.warn("MPI is avalible but the program was not started for use with MPI or mpi4py failed to install/load correctly. Disabling optional MPI functionality.", ImportWarning)

def get_MPI_avalible(): return __MPI_AVALIBLE
