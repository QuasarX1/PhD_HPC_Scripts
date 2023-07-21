#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc
scripts_directory=$(dirname "$(readlink -f ${BASH_SOURCE})")
source $scripts_directory/.command_aliases

if [ $# -ge 2 ]
then
    root_folder="${1}"
    redshift_number="${2}"
else
    root_folder="."
    redshift_number="${1}"
fi



function find_target_snapshot(){
    local sim_folder="$1"
    local target_z="$2"

    local file
    local snap_num
    local result
    for file in "$sim_folder"/*
    do
        if [[ $file =~ colibre_([0-9]{4})\.hdf5 ]]
        then
            snap_num="${BASH_REMATCH[1]}"
            result=$(cat-z "$file")
            #if [[ $result -eq $target_z ]]
            if (( $(echo "$result == $target_z" | bc -l) ))
            then
                echo "$snap_num"
                return 0
            fi
        fi
    done

    return 1
}

function get_snapshots(){
    local sim_folder="$1"
    local target_z="$2"

    local snapshot_list_string=""

    local file
    local snap_num
    local result
    for file in "$sim_folder"/*
    do
        if [[ $file =~ colibre_([0-9]{4})\.hdf5 ]]
        then
            snap_num="${BASH_REMATCH[1]}"
            result=$(cat-z "$file")
            #if [[ $result -ge $target_z ]]
            if (( $(echo "$result >= $target_z" | bc -l) ))
            then
                snapshot_list_string="$snapshot_list_string;$snap_num"
            else
                break
            fi
        fi
    done

    if [[ ${snapshot_list_string:0:1} == ";" ]]
    then
        snapshot_list_string="${snapshot_list_string:1}"
    fi

    echo $snapshot_list_string
    return 0
}

function make_sw_scripts(){ #TODO: change titles dynamicly!!! use read in box size and change the defualt contra slice at the same time!
    echo '#!/bin/bash

shopt -s expand_aliases
source ~/software/specwizard/.command_aliases

module purge
source ~/software/specwizard/environment/bin/activate

# Ion relation (H I - C IV)
make-sw-ion-relation-plot ./unmodified/SpecWizard-config.yaml H-C-relation_halo-mass-limited.png hydrogen_1 carbon_4 \
    -t "H I to C IV relation for different Enrichment Schemes
(L12N188 @ z=3)" \
    -c "./tracked-only/SpecWizard-config.yaml;./m-8/SpecWizard-config.yaml;./m-10/SpecWizard-config.yaml;./m-12/SpecWizard-config.yaml;./untracked-only/SpecWizard-config.yaml" \
    -l "Unmodified;Tracked Metals Only;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals Only" \
    -m -15.0 \
    -e

make-sw-metal-filter-hist filter-hist.png \
    "tracked-only/SpecWizard-config.yaml;m-8/SpecWizard-config.yaml;m-10/SpecWizard-config.yaml;m-12/SpecWizard-config.yaml;untracked-only/SpecWizard-config.yaml" \
    -l "Tracked Metals;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals" \
    -t "Metal Particle Selection Histograms" \
    -c

make-sw-metal-filter-hist filter-hist-log.png \
    "tracked-only/SpecWizard-config.yaml;m-8/SpecWizard-config.yaml;m-10/SpecWizard-config.yaml;m-12/SpecWizard-config.yaml;untracked-only/SpecWizard-config.yaml" \
    -l "Tracked Metals;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals" \
    -t "Metal Particle Selection Histograms" \
    -c \
    -g

make-sw-metal-filter-hist filter-mass-fraction.png \
    "tracked-only/SpecWizard-config.yaml;m-8/SpecWizard-config.yaml;m-10/SpecWizard-config.yaml;m-12/SpecWizard-config.yaml;untracked-only/SpecWizard-config.yaml" \
    -l "Tracked Metals;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals" \
    -t "Metal Particle Selection Metal Mass Distribution" \
    -c \
    --sum-mass

make-sw-metal-filter-hist filter-mass-fraction-log.png \
    "tracked-only/SpecWizard-config.yaml;m-8/SpecWizard-config.yaml;m-10/SpecWizard-config.yaml;m-12/SpecWizard-config.yaml;untracked-only/SpecWizard-config.yaml" \
    -l "Tracked Metals;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals" \
    -t "Metal Particle Selection Metal Mass Distribution" \
    -c \
    -g --sum-mass

make-sw-metal-filter-hist filter-volume-fraction.png \
    "tracked-only/SpecWizard-config.yaml;m-8/SpecWizard-config.yaml;m-10/SpecWizard-config.yaml;m-12/SpecWizard-config.yaml;untracked-only/SpecWizard-config.yaml" \
    -l "Tracked Metals;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals" \
    -t "Metal Particle Selection Metal Volume Distribution" \
    -c \
    --sum-volume

make-sw-metal-filter-hist filter-volume-fraction-log.png \
    "tracked-only/SpecWizard-config.yaml;m-8/SpecWizard-config.yaml;m-10/SpecWizard-config.yaml;m-12/SpecWizard-config.yaml;untracked-only/SpecWizard-config.yaml" \
    -l "Tracked Metals;\$Z(M_{\rm halo}<10^8)=0\$;\$Z(M_{\rm halo}<10^{10})=0\$;\$Z(M_{\rm halo}<10^{12})=0\$;Untracked Metals" \
    -t "Metal Particle Selection Metal Volume Distribution" \
    -c \
    -g --sum-volume

echo '\''<!doctype html>
<html>
<head></head>
<body>
<img src="./filter-hist.png">
<img src="./filter-hist-log.png">
</br>
<img src="./filter-mass-fraction.png">
<img src="./filter-mass-fraction-log.png">
</br>
<img src="./filter-volume-fraction.png">
<img src="./filter-volume-fraction-log.png">
</body>
</html>
'\'' > view_comparason.html
' > make_all_comparason.sh
    chmod u+x make_all_comparason.sh

    echo 'shopt -s expand_aliases
source ~/software/specwizard/.command_aliases

module purge
source ~/software/specwizard/environment/bin/activate

function carbon3() {
    make-sw-ion-relation-plot ./SpecWizard-config.yaml H-C3-relation.png hydrogen_1 carbon_3 \
        -t '\''H I to C III relation'\'' -m -15.0
}

function carbon4() {
    make-sw-ion-relation-plot ./SpecWizard-config.yaml H-C4-relation.png hydrogen_1 carbon_4 \
        -t '\''H I to C IV relation'\'' -m -15.0
}
function oxygen6() {
    make-sw-ion-relation-plot ./SpecWizard-config.yaml H-O-relation.png hydrogen_1 oxygen_6 \
        -t '\''H I to O VI relation'\'' -m -15.0
}

function silicon3() {
    make-sw-ion-relation-plot ./SpecWizard-config.yaml H-Si3-relation.png hydrogen_1 silicon_3 \
        -t '\''H I to Si III relation'\'' -m -15.0
}

function silicon4() {
    make-sw-ion-relation-plot ./SpecWizard-config.yaml H-Si4-relation.png hydrogen_1 silicon_4 \
        -t '\''H I to Si IV relation'\'' -m -15.0
}

function graph_all() {
    carbon3
    carbon4
    oxygen6
    silicon3
    silicon4
}

cd unmodified
graph_all
cd ../m-8
graph_all
cd ../m-10
graph_all
cd ../m-12
graph_all
cd ../tracked-only
graph_all
cd ../untracked-only
graph_all
cd ..
' > plot-all.sh
    chmod u+x plot-all.sh

    echo 'shopt -s expand_aliases
source ~/software/specwizard/.command_aliases

module purge
source ~/software/specwizard/environment/bin/activate

cd unmodified
specwizard-grid SpecWizard-config.yaml 10:00:00
cd ../m-8
specwizard-grid SpecWizard-config.yaml 10:00:00
cd ../m-10
specwizard-grid SpecWizard-config.yaml 10:00:00
cd ../m-12
specwizard-grid SpecWizard-config.yaml 10:00:00
cd ../tracked-only
specwizard-grid SpecWizard-config.yaml 10:00:00
cd ../untracked-only
specwizard-grid SpecWizard-config.yaml 10:00:00
cd ..
' > run-all.sh
    chmod u+x run-all.sh
}

function insert_sw_metalicity_zeroing_filter(){
    local insert_name="$1"
    local insert_min="$2"
    local insert_inc_min="$3"
    local insert_max="$4"
    local insert_inc_max="$5"
    local insert_ignore_null="$6"

    local template_placeholder="#    zero_metalicity_filters: # Remove this entire section if no metalicity filters are needed\\n#\\n#      high_mass_halos:\\n#        field_name: \"gas.last_halo_masses\"\\n#        field_unit: \"Msun\"\\n#        min: Null # Set to Null to disregard lower bound limit or -.inf to encapsulate all data if max is unset\\n#        include_lower: True\\n#        max: Null # Set to Null to disregard upper bound limit or .inf to encapsulate all data if min is unset\\n#        include_upper: True\\n#        null_data_value: -1 # Null will check for NaN values\\n#        ignore_null_data: True"

    local insertion_value="    zero_metalicity_filters: # Remove this entire section if no metalicity filters are needed\n\n      $insert_name:\n        field_name: \"gas.last_halo_masses\"\n        field_unit: \"Msun\"\n        min: $insert_min # Set to Null to disregard lower bound limit or -.inf if max is unset or .inf to encapsulate all data\n        include_lower: $insert_inc_min\n        max: $insert_max # Set to Null to disregard upper bound limit or .inf if min is unset or -.inf to encapsulate all data\n        include_upper: $insert_inc_max\n        null_data_value: -1.000003 # Null will check for NaN values\n        ignore_null_data: $insert_ignore_null"

    sed -i -z "s@$template_placeholder@$insertion_value@" ./SpecWizard-config.yaml
    return 0
}



mkdir "$root_folder/analysis-pipeline/z$redshift_number"
mkdir "$root_folder/specwizard/z$redshift_number"
sim_data_folder="$(readlink -f $root_folder/simulation-outputs)"
target_snapshot="$(find_target_snapshot "${sim_data_folder}" "$redshift_number")"
echo $target_snapshot

cd "$root_folder/analysis-pipeline/z$redshift_number"
module purge
source $scripts_directory/activate
contra-new-config
mv contra_settings_copy.sh contra_settings.sh

sed -i "s@COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY=\"..\"@COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY=\"${sim_data_folder}\"@" ./contra_settings.sh

if [ -e "${sim_data_folder}/haloes" ]
then
    sed -i "s@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"../haloes\"@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"${sim_data_folder}/haloes\"@" ./contra_settings.sh
elif [ -e "${sim_data_folder}/halos" ]
then
    sed -i "s@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"../haloes\"@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"${sim_data_folder}/halos\"@" ./contra_settings.sh
elif [ -e "${sim_data_folder}/catalogue" ]
then
    sed -i "s@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"../haloes\"@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"${sim_data_folder}/catalogue\"@" ./contra_settings.sh
elif [ -e "${sim_data_folder}/catalog" ]
then
    sed -i "s@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"../haloes\"@COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY=\"${sim_data_folder}/catalog\"@" ./contra_settings.sh
fi

sed -i "s@COLIBRE_DATA_PIPLINE__SNAPSHOTS=\"0000;0001;0002;0003;0004;0005;0006;0007\"@COLIBRE_DATA_PIPLINE__SNAPSHOTS=\"$(get_snapshots "${sim_data_folder}" "$redshift_number")\"@" ./contra_settings.sh

sed -i "s@COLIBRE_DATA_PIPLINE__LAST_SNAPSHOT=\"0007\"@COLIBRE_DATA_PIPLINE__LAST_SNAPSHOT=\"${target_snapshot}\"@" ./contra_settings.sh

cd ../..



if command -v activate-sw >/dev/null 2>&1
then
    activate-sw

    cd "$root_folder/specwizard/z$redshift_number"

    make_sw_scripts

    mkdir unmodified
    cd unmodified
    $(sw-new-config)
    mv SpecWizard-config-copy.yaml SpecWizard-config.yaml
    sed -i "s@simulation_snapshots: \"/storage/simulations/COLIBRE/examples/hawk_scaling_test/L012N0188/\"@simulation_snapshots: \"${sim_data_folder}\"@" ./SpecWizard-config.yaml
    sed -i "s@snapshot_file: \"colibre_0036.hdf5\"@snapshot_file: \"colibre_${target_snapshot}.hdf5\"@" ./SpecWizard-config.yaml
    sed -i "s@spacing_mpc: 1.0 # 1 ray per Mpc@spacing_mpc: 0.125 # 8 rays per Mpc@" ./SpecWizard-config.yaml
    sed -i "s@run_parallel: False@run_parallel: True@" ./SpecWizard-config.yaml
    cd ..

    folders=(     "untracked-only"           "tracked-only"           "m-8"                          "m-10"                          "m-12"                          "no-metals" )
    names=(       "untracked_particles_only" "tracked_particles_only" "halo_mass_above_10_to_the_8"  "halo_mass_above_10_to_the_10"  "halo_mass_above_10_to_the_12"  "no_metals" )
    mins=(        "-.inf"                    "Null"                   "Null"                         "Null"                          "Null"                          "-.inf"     )
    inc_mins=(    "True"                     "True"                   "False"                        "False"                         "False"                         "True"      )
    maxes=(       ".inf"                     "0.0"                    "10.0e+8"                      "10.0e+10"                      "10.0e+12"                      ".inf"      )
    inc_maxes=(   "True"                     "False"                  "False"                        "False"                         "False"                         "True"      )
    ignore_null=( "True"                     "False"                  "False"                        "False"                         "False"                         "False"     )

    #for folder in 
    for i in "${!folders[@]}"
    do
        mkdir ${folders[$i]}
        cd ${folders[$i]}
        $(sw-new-config)
        mv SpecWizard-config-copy.yaml SpecWizard-config.yaml
        sed -i "s@simulation_snapshots: \"/storage/simulations/COLIBRE/examples/hawk_scaling_test/L012N0188/\"@simulation_snapshots: \"$(readlink -f "../../../analysis-pipeline/z$redshift_number")\"@" ./SpecWizard-config.yaml
        sed -i "s@snapshot_file: \"colibre_0036.hdf5\"@snapshot_file: \"modified_present_day_snap.hdf5\"@" ./SpecWizard-config.yaml
        insert_sw_metalicity_zeroing_filter ${names[$i]} ${mins[$i]} ${inc_mins[$i]} ${maxes[$i]} ${inc_maxes[$i]} ${ignore_null[$i]}
        sed -i "s@spacing_mpc: 1.0 # 1 ray per Mpc@spacing_mpc: 0.125 # 8 rays per Mpc@" ./SpecWizard-config.yaml
        sed -i "s@run_parallel: False@run_parallel: True@" ./SpecWizard-config.yaml
        cd ..
    done
    
    cd ../..
fi















# Yes, you can use sed -i with a multi-line string. However, it can be a bit tricky to get it to work correctly.
#One way to do this is to use the N, D, and P commands in sed to manage multi-line operations1.
#For example, you can match the first line of your pattern, use N to append the second line to the pattern space, and then use s to perform your substitution1. Here’s an example:
# 
# sed '/a test$/{ N s/a test\\nPlease do not/not a test\\nBe/ }' input.txt
# Copy
# This command matches lines that end with “a test”, appends the next line to the pattern space using the N command, and then performs a substitution on the two lines using the s command1.
# 
# Another way to use a multi-line string with sed -i is to escape the newlines in the string so that sed knows where the string ends and additional commands, if any, start2. Here’s an example:
# 
# test="This is a multi-line string that we want to replace with a new string."
# testEscapedForSed=${test//$'\\n'/\\\\$'\\n'}
# sed -i "s/This is a multi-line string that we want to replace with a new string./$testEscapedForSed/g" input.txt
# Copy
# This script reads the contents of a file into a shell variable $test, escapes the newlines in $test for use in sed, and then uses sed -i to perform an in-place substitution on the input file2.
# 
# I hope this helps! Let me know if you have any further questions. 😊
