#!/bin/bash
#
#SBATCH --partition=<>
#SBATCH --job-name=<job>
#SBATCH --time=<>
#SBATCH --ntasks=<>
#SBATCH --mem-per-cpu=4GB

source /usr/share/modules/init/bash
module purge

# MPI
source /usr/local/intel_2019U3/compilers_and_libraries_2019.3.199/linux/bin/compilervars.sh intel64
module load openmpi/4.0.1/intel_2019
mpirun -np $SLURM_NTASKS <target>
# END MPI
