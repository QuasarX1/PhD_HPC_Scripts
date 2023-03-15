#!/bin/bash
#
##SBATCH --account=aricrowe
#SBATCH --partition=test
#SBATCH --job-name=MPI_job
#SBATCH --output=log-%j.txt
#SBATCH --time=01:00:00
#SBATCH --ntasks=1#128#512
##SBATCH --ntasks-per-core=1
#SBATCH --mem-per-cpu=1GB
##SBATCH --chdir=./

module purge

# MPI
module load /software/intel/modulefiles/mpi/2021.1.1

echo "Running with $SLURM_NTASKS processes."
echo ""

mpirun -np $SLURM_NTASKS $@
# END MPI
