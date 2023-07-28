#!/bin/bash

scripts_directory=$(dirname "$(readlink -f ${BASH_SOURCE})")

mkdir logs
mkdir logs/errors

# Process positional arguments
cfg_file="${1}"

# Process options
shift 1

time_flag=""
partition=""

while getopts "t:p:" opt
do
    case "$opt" in
        t)
            time_flag="--time $OPTARG "
            ;;
        n)
            partition="--partition $OPTARG "
            ;;
        \?)
            ;;
    esac
done

#if [ ! -z "${2}" ]
#then
#    time_flag="--time ${2} "
#else
#    time_flag=""
#fi

jobid=$(sbatch $time_flag$partition"$scripts_directory/data_reduction.sh" "$scripts_directory" "$(readlink -f $cfg_file)" | awk '{print $4}')

echo "Use \`scancel $jobid\` to cancel."
echo "Use \`watch tail \"$(readlink -f "logs/data-reduction-log-$jobid.txt")\" -n 40\` to view live output."
