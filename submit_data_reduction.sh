#!/bin/bash

scripts_directory=$(dirname "$(readlink -f ${BASH_SOURCE})")

mkdir logs
mkdir logs/errors

if [ ! -z "${2}" ]
then
    time_flag="--time ${2} "
else
    time_flag=""
fi

jobid=$(sbatch $time_flag"$scripts_directory/data_reduction.sh" "$scripts_directory" "$(readlink -f ${1})" | awk '{print $4}')

echo "Use \`scancel $jobid\` to cancel."
echo "Use \`watch tail \"$(readlink -f "logs/data-reduction-log-$jobid.txt")\" -n 40\` to view live output."
