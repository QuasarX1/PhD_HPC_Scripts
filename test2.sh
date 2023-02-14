#!/bin/bash
echo "${BASH_SOURCE}"
echo $(dirname "$(readlink -f ${BASH_SOURCE})")
echo $(dirname "$(readlink -f $0)")