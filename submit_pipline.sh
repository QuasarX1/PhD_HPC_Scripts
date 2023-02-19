#!/bin/bash

scripts_directory=$(dirname "$(readlink -f ${BASH_SOURCE})")

mkdir logs
mkdir logs/errors

sbatch "$scripts_directory/data_pipeline.sh" "$scripts_directory" "$(readlink -f ${1})"
