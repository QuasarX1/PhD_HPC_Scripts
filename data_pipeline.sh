#!/bin/bash
#
#SBATCH --job-name=qx1-Colibre-Pipline
#SBATCH --time=01:00:00
#SBATCH --partition=compute
#SBATCH --output=logs/pipline-log-%j.txt
#SBATCH --error=logs/errors/pipline-log-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --threads-per-core=1



scripts_directory=$(readlink -f "${1}")

shopt -s expand_aliases
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



# Critical Gas Density
critical_gas_density=$(gas-crit-density "$present_day_data" -u "Msun/Mpc**3")



## Maps
#
## Surface Density Map
#echo ""
#echo "Surface Density Map"
#sph-map $present_day_data map_surface_density.png -t "\$\Sigma^{\rm gas}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
#
## Metal Surface Density Map
#echo ""
#echo "Metal Surface Density Map"
#sph-map $present_day_data map_mean_mass_weighted_metal_mass.png -t "\$\Sigma^{\rm gas}_{\rm metal}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.metal_mass_fractions*gas.masses -u "Msun" -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
#
## Metal Mass Fraction Map
#echo ""
#echo "Metal Mass Fraction Map"
#sph-map $present_day_data map_mean_mass_weighted_metal_mass_fraction.png -t "\$M_Z/M\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s "gas.metal_mass_fractions" -u "" -p -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
#
## Metalicity Map
#echo ""
#echo "Metalicity Map"
#sph-map $present_day_data map_mean_mass_weighted_metalicity.png -t "\$Z/Z_{\\odot}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s "(gas.metal_mass_fractions/(1-gas.metal_mass_fractions))/0.0134" -u "" -p -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
#
## Mean Metal Mass Weighted Redshift Map
#echo ""
#echo "Mean Metal Mass Weighted Redshift Map"
#sph-map $present_day_data map_mean_metal_weighted_redshift.png -t "\$z_Z\$+1" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.mean_metal_weighted_redshifts+1 -u "" -p --filter-attr gas.mean_metal_weighted_redshifts --filter-unit "" --filter-min 0.0 -c gas.masses --exclude-filter-from-contour --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP



## Temperature Density Diagrams
#
## Temp Density Colour=z_Z Weighting=Mass Contours=Mass
#echo ""
#echo "Temp Density Colour=z_Z Weighting=Mass Contours=Mass"
#t-d $present_day_data -v -d -o plot_temp_dens_redshift.png -c gas.mean_metal_weighted_redshifts -u "" --colour-name "\$z_Z\$" --colour-min 0.0 --colour-max 10.2 -l gas.masses --contour-unit Msun $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass
#echo ""
#echo "Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass"
#t-d $present_day_data -o plot_temp_dens_log_redshift.png -c 1+gas.mean_metal_weighted_redshifts -u "" --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 -l gas.masses --contour-unit Msun $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=z_Z Weighting=Volume Contours=Volume
#echo ""
#echo "Temp Density Colour=z_Z Weighting=Volume Contours=Volume"
#t-d $present_day_data -o plot_temp_dens_redshift_volume_weighting_volume_contours.png -c gas.mean_metal_weighted_redshifts -u "" --colour-name "\$z_Z\$" --colour-min 0.0 --colour-max 10.2 --colour-weight gas.masses/gas.densities -l gas.masses/gas.densities --contour-unit kpc**3 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume
#echo ""
#echo "Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume"
#t-d $present_day_data -o plot_temp_dens_log_redshift_volume_weighting_volume_contours.png -c 1+gas.mean_metal_weighted_redshifts -u "" --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 --colour-weight gas.masses/gas.densities -l gas.masses/gas.densities --contour-unit kpc**3 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(Mass) Weighting=Mass
#echo ""
#echo "Temp Density Colour=log_10(Mass) Weighting=Mass"
#t-d $present_day_data -o plot_temp_dens_mass.png --colour-name "\$M\$" --fraction-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(Metal Mass Fraction) Weighting=Mass
#echo ""
#echo "Temp Density Colour=log_10(Metal Mass Fraction) Weighting=Mass"
#t-d $present_day_data -v -d -o plot_temp_dens_metal_mass_fraction.png -c gas.metal_mass_fractions -u "" --colour-name "\$M_Z/M\$" --log-colour --colour-min 0.0 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(Metallicitys) Weighting=Mass
#echo ""
#echo "Temp Density Colour=log_10(Metallicitys) Weighting=Mass"
#t-d $present_day_data -v -d -o plot_temp_dens_metallicity.png -c "(gas.metal_mass_fractions/(1-gas.metal_mass_fractions))/0.0134" -u "" --colour-name "\$Z/Z_{\\odot}\$" --colour-min 0.0 --log-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(Metal Mass) Weighting=Mass
#echo ""
#echo "Temp Density Colour=log_10(Metal Mass) Weighting=Mass"
#t-d $present_day_data -o plot_temp_dens_metal_mass.png -c gas.masses*gas.metal_mass_fractions -u "Msun" --colour-name "\$M_{\\rm Z}\$" --fraction-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#
## Temp Density Colour=log_10(Volume) Weighting=Volume
#echo ""
#echo "Temp Density Colour=log_10(Volume) Weighting=Volume"
#t-d $present_day_data -o plot_temp_dens_volume.png -c gas.masses/gas.densities -u "kpc**3" --colour-name "\$V\$" --fraction-colour --log-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP



## Gas Line Graphs
#
## Density Redshift Gas Line Plot X=density Y=log_10(1+z_Z) Weighting=Mass???
#echo ""
#echo "Density Redshift Gas Line Plot X=density Y=log_10(1+z_Z) Weighting=Mass???"
#gas-line $present_day_data "z=0" "plot_dens_log_redshift.png" "densities/#<$critical_gas_density>#" "" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e
#
## Temp Redshift Gas Line Plot X=temp Y=log_10(1+z_Z) Weighting=Mass???
#echo ""
#echo "Temp Redshift Gas Line Plot X=temp Y=log_10(1+z_Z) Weighting=Mass???"
#gas-line $present_day_data "z=0" "plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(1+z_Z) Weighting=Mass???
echo ""
echo "Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(1+z_Z) Weighting=Mass???"
gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "convergence_test__plot_dens_log_redshift.png" "densities/#<$critical_gas_density>#" "" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# Temp Redshift Gas Line Plot Convergence Test X=temp Y=log_10(1+z_Z) Weighting=Mass???
echo ""
echo "Temp Redshift Gas Line Plot Convergence Test X=temp Y=log_10(1+z_Z) Weighting=Mass???"
gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "convergence_test__plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e


if ! [ -f ./gas_particle_ejection_tracking__halo_masses.pickle ]
then
    echo ""
    echo "Trace Gas Halo Interactions"
    get-past-halo-masses $COLIBRE_DATA_PIPLINE__SNAPSHOTS $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_GROUPS_FILE_TEMPLATE -v -d
else
    echo ""
    echo "Found saved gas-halo interaction data. Remove or rename this data to re-generate."
fi

echo ""
echo "Plot Enrichment Halo Mass"
graph-past-halo-masses "./;$COLIBRE_DATA_PIPLINE__COMPARISON_CACHED_ENRICHMENT_DATA_DIRECTORY" "plot_temp_dens_enrichment_halo_mass.png" "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" --labels "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
#graph-past-halo-masses ./ "plot_temp_dens_enrichment_halo_mass.png" $present_day_data --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --side-length $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --z-side-length inf



echo ""
echo "GRAPHS DONE"

echo ""
echo "MAKING HTML PAGE"

cp $scripts_directory/_example_pipeline_view.html ./view.html
search_result=( map_surface_density*.png )
sed -i "s@{sd_map_file}@${search_result[0]}@" ./view.html
search_result=( map_mean_mass_weighted_metal_mass*.png )
sed -i "s@{mmwmm_map_file}@${search_result[0]}@" ./view.html
search_result=( map_mean_mass_weighted_metal_mass_fraction*.png )
sed -i "s@{mmwmmf_map_file}@${search_result[0]}@" ./view.html
search_result=( map_mean_mass_weighted_metalicity*.png )
sed -i "s@{mmwm_map_file}@${search_result[0]}@" ./view.html
search_result=( map_mean_metal_weighted_redshift*.png )
sed -i "s@{mmwr_map_file}@${search_result[0]}@" ./view.html



echo ""
echo "COMPRESSING FILES"

zip -r ./download_me.zip ./*.png ./*.html



echo ""
echo "PIPELINE COMPLETE"
