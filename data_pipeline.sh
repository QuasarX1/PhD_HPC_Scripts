#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

x_position=$1
y_position=$2
Z_position=$3
width=$4
depth=$5

snapshot_numbers=$6
snapshot_files_directory=$7
snapshot_file_template=$8
catalogue_files_directory=$9
catalogue_file_template=${10}
groups_file_template=${11}
parttypes_file_template=${12}

file_number_placeholder_str="{}"

data=$(echo $snapshot_files_directory/$snapshot_file_template | sed "s/$file_number_placeholder_str/${snapshot_numbers##*;}/")



halo-n-part $(echo $catalogue_files_directory/$parttypes_file_template | sed "s/$file_number_placeholder_str/${snapshot_numbers##*;}/")

# Surface Density Map
sph-map $data -o map_surface_density.png               -t "\$\Sigma^{\rm gas}\$"             --gas -x $x_position -y $y_position -z $Z_position --projection -w $width

# Metal Surface Density Map
sph-map $data -o map_mean_mass_weighted_metalicity.png -t "\$\Sigma^{\rm gas}_{\rm metal}\$" --gas -x $x_position -y $y_position -z $Z_position --projection -w $width -s gas.metal_mass_fractions*gas.masses -u "Msun"                                        -c masses

# Mean Metal Mass Weighted Redshift Map
sph-map $data -o map_mean_metal_weighted_redshift.png  -t "\$z_Z\$"                          --gas -x $x_position -y $y_position -z $Z_position --projection -w $width -s gas.mean_metal_weighted_redshifts+1 -u ""     -p --filter-unit Msun --filter-min 0.0 -c masses

# Temp Density Colour=z_Z Weighting=Mass Contours=Mass
t-d $data -o plot_temp_dens_redshift.png                                      -c mean_metal_weighted_redshifts   -u ""       --colour-name "\$z_Z\$"                --colour-min 0.0 --colour-max 10.2                                  -l masses           --contour-unit Msun

# Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass
t-d $data -o plot_temp_dens_log_redshift.png                                  -c 1+mean_metal_weighted_redshifts -u ""       --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2                                  -l masses           --contour-unit Msun

# X=density Y=log_10(1+z_Z) Weighting=Mass???
gas-line $data "z=0" "plot_dens_log_redshift.png" "densities" "Msun/Mpc**3" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$" --y-axis-name "\$1+z_Z\$" --fraction-x-axis --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# X=temp Y=log_10(1+z_Z) Weighting=Mass???
gas-line $data "z=0" "plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# Temp Density Colour=z_Z Weighting=Volume Contours=Volume
t-d $data -o plot_temp_dens_redshift_volume_weighting_volume_contours.png     -c mean_metal_weighted_redshifts   -u ""       --colour-name "\$z_Z\$"                --colour-min 0.0 --colour-max 10.2 --colour-weight masses/densities -l masses/densities --contour-unit kpc**3

# Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume
t-d $data -o plot_temp_dens_log_redshift_volume_weighting_volume_contours.png -c 1+mean_metal_weighted_redshifts -u ""       --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 --colour-weight masses/densities -l masses/densities --contour-unit kpc**3

# Temp Density Colour=log_10(Mass) Weighting=Mass
t-d $data -o plot_temp_dens_mass.png                                                                                         --colour-name "\$M\$"     --log-colour

# Temp Density Colour=log_10(Volume) Weighting=Volume
t-d $data -o plot_temp_dens_volume.png                                        -c masses/densities                -u "kpc**3" --colour-name "\$V\$"     --log-colour



data_low_res="/storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/ln1/snapshots/snapshot_0007.hdf5"

# X=density Y=log_10(1+z_Z) Weighting=Mass???
gas-line "$data;$data_low_res" "l0;ln1" "convergence_test__plot_dens_log_redshift.png" "densities" "Msun/Mpc**3" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$" --y-axis-name "\$1+z_Z\$" --fraction-x-axis --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e

# X=temp Y=log_10(1+z_Z) Weighting=Mass???
gas-line "$data;$data_low_res" "l0;ln1" "convergence_test__plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e



get-past-halo-masses $snapshot_numbers $snapshot_files_directory $snapshot_file_template $catalogue_files_directory $catalogue_file_template $catalogue_files_directory $groups_file_template -v -d
