#!/bin/bash

mkdir ${1}

mkdir "${1}/analysis-pipeline"
mkdir "${1}/specwizard"
cd "${1}"
ln -s ${2} simulation-outputs
cd ..
