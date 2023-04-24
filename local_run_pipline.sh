#!/bin/bash

scripts_directory=$(dirname "$(readlink -f ${BASH_SOURCE})")

mkdir logs

out_file="./logs/local-pipline-log-$(date +%Y-%m-%d-%H-%M-%S).txt"

"$scripts_directory/data_pipeline.sh" "$scripts_directory" "$(readlink -f ${1})" > "$out_file" 2>&1 &

echo "Terminate with \`kill $!\`. Use the -9 flag to force kill the process."

if ! [[ -z "$2" ]]
then
    n_watch_lines=$2
else
    n_watch_lines=40
fi

echo "Use \`watch tail \"$(readlink -f "$out_file")\" -n $n_watch_lines\` to view live output."

watch tail "$out_file" -n $n_watch_lines
