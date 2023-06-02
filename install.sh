#!/bin/bash

scripts_directory=$(dirname "$(readlink -f ${BASH_SOURCE})")

python3 -m venv environment
source ./environment/bin/activate

pip install --upgrade pip
pip install numpy

pip install -r $scripts_directory/requirements.txt

deactivate

echo "export QX1_PYTHON=$(readlink -f ./environment/bin)/python">$scripts_directory/.python_interpreter_path.sh
