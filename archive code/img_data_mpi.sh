n=$1
shift

python_environment_path=/home/aricrowe/python_environments
user_scripts_path=/home/aricrowe/scripts

sbatch -n $n /home/aricrowe/scripts/mpi_slurm_job.sh "$python_environment_path/data_analysis/bin/python $user_scripts_path/img_data.py $@"
