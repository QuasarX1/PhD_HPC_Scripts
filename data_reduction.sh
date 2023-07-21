#!/bin/bash
#
#SBATCH --job-name=contra
#SBATCH --time=01:00:00
#SBATCH --partition=compute
#SBATCH --output=logs/data-reduction-log-%j.txt
#SBATCH --error=logs/errors/data-reduction-log-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --threads-per-core=1

Zsun=0.0134
just_above_zero=0.000000001



scripts_directory=$(readlink -f "${1}")

shopt -s expand_aliases
# Load Prospero Python distro module
module purge
module load apps/python3/3.9.16
source $scripts_directory/.command_aliases

# Read the paramiters exported in the settings script file passes in
source $(readlink -f "${2}")

# Create the directory paths
export COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY="$(readlink -f $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY)"
export COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY="$(readlink -f $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY)"
present_day_data=$COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY/$(echo $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE | sed "s@$COLIBRE_DATA_PIPLINE__TEMPLATE_PLACEHOLDER@$COLIBRE_DATA_PIPLINE__LAST_SNAPSHOT@")

# Insert optional paramiter flags
if ! [[ -z "$COLIBRE_DATA_PIPLINE__MAP_COLOURMAP" ]]
then
    export COLIBRE_DATA_PIPLINE__MAP_COLOURMAP="--colour-map $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP"
fi

if ! [[ -z "$COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP" ]]
then
    export COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP="--colour-map $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP"
fi

# Move to the output directory
export COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY="$(readlink -f $COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY)"
mkdir $COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY
cd $COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY



#if ! [ -f ./stars_particle_ejection_tracking__halo_masses.pickle ]
#then
#    echo ""
#    echo "Trace Gas Halo Interactions"
#    get-past-halo-masses "stars" $COLIBRE_DATA_PIPLINE__SNAPSHOTS $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE -v -d
#else
#    echo ""
#    echo "Found saved star-halo interaction data. Remove or rename this data to re-generate."
#fi



# Make modified snapshot

if ! [ -f ./gas_particle_ejection_tracking__halo_masses.pickle ]
then
    echo ""
    echo "Trace Gas Halo Interactions"
#    get-past-halo-masses $COLIBRE_DATA_PIPLINE__SNAPSHOTS $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_GROUPS_FILE_TEMPLATE -v -d
    get-past-halo-masses "gas" $COLIBRE_DATA_PIPLINE__SNAPSHOTS $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE -v -d
else
    echo ""
    echo "Found saved gas-halo interaction data. Remove or rename this data to re-generate."
fi

if ! [ -f ./modified_present_day_snap.hdf5 ]
then
    echo ""
    echo "Creating Updated Snapshot"
    create-new-z0-data "$present_day_data" -v -d
else
    echo ""
    echo "Found updated snapshot. Remove or rename this data to re-generate."
fi

#if ! [ -f ./gas_particle_ejection_tracking__present_day_halo_id.pickle ]
#then
#    echo ""
#    echo "Tracking Haloes To Present Day"
#    get-matched-present-day-haloes modified_present_day_snap.hdf5 "$COLIBRE_DATA_PIPLINE__LAST_SNAPSHOT" "$COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY" "$COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE" "$COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY" "$COLIBRE_DATA_PIPLINE__CATALOGUE_GROUPS_FILE_TEMPLATE" -v -d
#else
#    echo ""
#    echo "Found forward tracked haloes. Remove or rename this data to re-generate."
#fi

# if ! [ -f ./gas_particle_ejection_tracking__present_day_ejection_distance.pickle ]
# then
#     echo ""
#     echo "Calculate Gas Ejection Displacement"
#     get-matched-halo-particle-ejection modified_present_day_snap.hdf5 "$COLIBRE_DATA_PIPLINE__LAST_SNAPSHOT" "$COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY" "$COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE" -v -d
# else
#     echo ""
#     echo "Found saved gas ejection data. Remove or rename this data to re-generate."
# fi

echo ""
echo "DATA REDUCTION COMPLETE"
