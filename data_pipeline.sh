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
#TODO: does this actually make them absolute paths, or just relitive without symlinks???
export COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY="$(readlink -f $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY)"
export COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY="$(readlink -f $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY)"
present_day_data=$COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY/$(echo $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE | sed "s@$COLIBRE_DATA_PIPLINE__TEMPLATE_PLACEHOLDER@$COLIBRE_DATA_PIPLINE__LAST_SNAPSHOT@")

# Move to the output directory
export COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY="$(readlink -f $COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY)"
mkdir $COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY
cd $COLIBRE_DATA_PIPLINE__PIPELINE_OUTPUT_DIRECTORY



# Critical Gas Density
critical_gas_density=$(gas-crit-density "$present_day_data" -u "Msun/Mpc**3")



# Maps

# Surface Density Map
echo ""
echo "Surface Density Map"
sph-map $present_day_data map_surface_density.png -t "\$\Sigma^{\rm gas}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH

# Metal Surface Density Map
echo ""
echo "Metal Surface Density Map"
sph-map $present_day_data map_mean_mass_weighted_metal_mass.png -t "\$\Sigma^{\rm gas}_{\rm metal}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.metal_mass_fractions*gas.masses -u "Msun" -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH

# Metalicity Map
echo ""
echo "Metalicity Map"
sph-map $present_day_data map_mean_mass_weighted_metalicity.png -t "\$Z/Z_{\\odot}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s "gas.metal_mass_fractions/0.0134" -u "" -p -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH

# Mean Metal Mass Weighted Redshift Map
echo ""
echo "Mean Metal Mass Weighted Redshift Map"
sph-map $present_day_data map_mean_metal_weighted_redshift.png -t "\$z_Z\$+1" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.mean_metal_weighted_redshifts+1 -u "" -p --filter-attr gas.mean_metal_weighted_redshifts --filter-unit "" --filter-min 0.0 -c gas.masses --exclude-filter-from-contour -v -d --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH



# Temperature Density Diagrams

# Temp Density Colour=z_Z Weighting=Mass Contours=Mass
echo ""
echo "Temp Density Colour=z_Z Weighting=Mass Contours=Mass"
t-d $present_day_data -o plot_temp_dens_redshift.png -c gas.mean_metal_weighted_redshifts -u "" --colour-name "\$z_Z\$" --colour-min 0.0 --colour-max 10.2 -l gas.masses --contour-unit Msun

# Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass
echo ""
echo "Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass"
t-d $present_day_data -o plot_temp_dens_log_redshift.png -c 1+gas.mean_metal_weighted_redshifts -u "" --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 -l gas.masses --contour-unit Msun

# Temp Density Colour=z_Z Weighting=Volume Contours=Volume
echo ""
echo "Temp Density Colour=z_Z Weighting=Volume Contours=Volume"
t-d $present_day_data -o plot_temp_dens_redshift_volume_weighting_volume_contours.png -c gas.mean_metal_weighted_redshifts -u "" --colour-name "\$z_Z\$" --colour-min 0.0 --colour-max 10.2 --colour-weight gas.masses/gas.densities -l gas.masses/gas.densities --contour-unit kpc**3

# Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume
echo ""
echo "Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume"
t-d $present_day_data -o plot_temp_dens_log_redshift_volume_weighting_volume_contours.png -c 1+gas.mean_metal_weighted_redshifts -u "" --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 --colour-weight gas.masses/gas.densities -l gas.masses/gas.densities --contour-unit kpc**3

# Temp Density Colour=log_10(Mass) Weighting=Mass
echo ""
echo "Temp Density Colour=log_10(Mass) Weighting=Mass"
t-d $present_day_data -o plot_temp_dens_mass.png --colour-name "\$M\$" --fraction-colour

# Temp Density Colour=log_10(Metallicitys) Weighting=Mass
echo ""
echo "Temp Density Colour=log_10(Metallicitys) Weighting=Mass"
t-d $present_day_data -o plot_temp_dens_metallicity.png -c gas.metal_mass_fractions/0.0134 -u "" --colour-name "\$Z/Z_{\\odot}\$" --log-colour

# Temp Density Colour=log_10(Metal Mass) Weighting=Mass
echo ""
echo "Temp Density Colour=log_10(Metal Mass) Weighting=Mass"
t-d $present_day_data -o plot_temp_dens_metal_mass.png -c gas.masses*gas.metal_mass_fractions -u "Msun" --colour-name "\$M_{\\rm Z}\$" --fraction-colour

# Temp Density Colour=log_10(Volume) Weighting=Volume
echo ""
echo "Temp Density Colour=log_10(Volume) Weighting=Volume"
t-d $present_day_data -o plot_temp_dens_volume.png -c gas.masses/gas.densities -u "kpc**3" --colour-name "\$V\$" --fraction-colour --log-colour



# Gas Line Graphs

# Density Redshift Gas Line Plot X=density Y=log_10(1+z_Z) Weighting=Mass???
echo ""
echo "Density Redshift Gas Line Plot X=density Y=log_10(1+z_Z) Weighting=Mass???"
gas-line $present_day_data "z=0" "plot_dens_log_redshift.png" "densities/#<$critical_gas_density>#" "" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# Temp Redshift Gas Line Plot X=temp Y=log_10(1+z_Z) Weighting=Mass???
echo ""
echo "Temp Redshift Gas Line Plot X=temp Y=log_10(1+z_Z) Weighting=Mass???"
gas-line $present_day_data "z=0" "plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(1+z_Z) Weighting=Mass???
echo ""
echo "Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(1+z_Z) Weighting=Mass???"
gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "convergence_test__plot_dens_log_redshift.png" "densities/#<$critical_gas_density>#" "" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# Temp Redshift Gas Line Plot Convergence Test X=temp Y=log_10(1+z_Z) Weighting=Mass???
echo ""
echo "Temp Redshift Gas Line Plot Convergence Test X=temp Y=log_10(1+z_Z) Weighting=Mass???"
gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "convergence_test__plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e



echo ""
echo "Trace Gas Halo Interactions"
get-past-halo-masses $COLIBRE_DATA_PIPLINE__SNAPSHOTS $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_GROUPS_FILE_TEMPLATE -v -d
echo ""
echo "Plot Enrichment Halo Mass"
graph-past-halo-masses ./ "plot_temp_dens_enrichment_halo_mass.png" $present_day_data
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
search_result=( map_mean_mass_weighted_metalicity*.png )
sed -i "s@{mmwm_map_file}@${search_result[0]}@" ./view.html
search_result=( map_mean_metal_weighted_redshift*.png )
sed -i "s@{mmwr_map_file}@${search_result[0]}@" ./view.html



echo ""
echo "PIPELINE COMPLETE"
