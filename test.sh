#!/bin/bash

dir_path="/home/aricrowe/"
f_template="file_{}.txt"
f_num="0001"

file_number_placeholder_str="{}"
double_slash_string="//"
single_slash_string="/"
filepath_template=$(echo $dir_path/$f_template | sed "s/$double_slash_string/$single_slash_string/")
data=$(echo $filepath_template | sed "s/$file_number_placeholder_str/$f_num/")
echo $data
