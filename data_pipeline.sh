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

Zsun=0.0134
just_above_zero=0.000000001



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

if ! [ -f ./gas_particle_ejection_tracking__halo_masses.pickle ]
then
    echo ""
    echo "Trace Gas Halo Interactions"
    get-past-halo-masses $COLIBRE_DATA_PIPLINE__SNAPSHOTS $COLIBRE_DATA_PIPLINE__SNAPSHOT_DIRECTORY $COLIBRE_DATA_PIPLINE__SNAPSHOT_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_FILE_TEMPLATE $COLIBRE_DATA_PIPLINE__CATALOGUE_DIRECTORY $COLIBRE_DATA_PIPLINE__CATALOGUE_GROUPS_FILE_TEMPLATE -v -d
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



# Maps

# Surface Density Map
if ! [ -f ./map_surface_density*.png ]
then
    echo ""
    echo "Surface Density Map"
    sph-map $present_day_data map_surface_density.png -t "\$\Sigma^{\rm gas}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi

# Metal Surface Density Map
#if ! [ -f ./map_mean_mass_weighted_metal_mass*.png ]
if [ $(ls -1 ./map_mean_mass_weighted_metal_mass*.png 2>/dev/null | wc -l) -eq 0 ]
then
    echo ""
    echo "Metal Surface Density Map"
    sph-map $present_day_data map_mean_mass_weighted_metal_mass.png -t "\$\Sigma^{\rm gas}_{\rm metal}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.metal_mass_fractions*gas.masses -u "Msun" -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi

# Metal Mass Fraction Map
if ! [ -f ./map_mean_mass_weighted_metal_mass_fraction*.png ]
then
    echo ""
    echo "Metal Mass Fraction Map"
    sph-map $present_day_data map_mean_mass_weighted_metal_mass_fraction.png -t "\$M_Z/M\$ \$\rm Z_{\odot}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s "gas.metal_mass_fractions/$Zsun" -u "" -p --log-pre-intergration -c gas.masses --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi

# Mean Metal Mass Weighted Redshift Map
if ! [ -f ./map_mean_metal_weighted_redshift*.png ]
then
    echo ""
    echo "Mean Metal Mass Weighted Redshift Map"
    sph-map $present_day_data map_mean_metal_weighted_redshift.png -t "\$z_Z\$+1" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.mean_metal_weighted_redshifts+1 -u "" -p --log-pre-intergration --limit-fields gas.mean_metal_weighted_redshifts --limit-units "" --limits-min 0.0 -c gas.masses --exclude-limits-from-contour --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi

# Last Halo Mass Map
if ! [ -f ./map_last_enrichment_halo_mass*.png ]
then
    echo ""
    echo "Last Halo Mass Map"
    sph-map modified_present_day_snap.hdf5 map_last_enrichment_halo_mass.png -v -d -t "\$M_{\rm halo}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.last_halo_masses -u "Msun" -p --log-pre-intergration --limit-fields gas.last_halo_masses --limit-units "Msun" --limits-min "$just_above_zero" -c gas.masses --exclude-limits-from-contour --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi
if ! [ -f ./map_low_density_last_enrichment_halo_mass*.png ]
then
    echo ""
    echo "(Low Density) Last Halo Mass Map"
    sph-map modified_present_day_snap.hdf5 map_low_density_last_enrichment_halo_mass.png -t "\$M_{\rm halo}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.last_halo_masses -u "Msun" -p --log-pre-intergration --limit-fields "gas.last_halo_masses;gas.densities/#<$critical_gas_density>#" --limit-units "Msun;" --limits-min "$just_above_zero;" --limits-max ";2.5" -c gas.masses --exclude-limits-from-contour --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi
if ! [ -f ./map_mid_density_last_enrichment_halo_mass*.png ]
then
    echo ""
    echo "(Mid Density) Last Halo Mass Map"
    sph-map modified_present_day_snap.hdf5 map_mid_density_last_enrichment_halo_mass.png -t "\$M_{\rm halo}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.last_halo_masses -u "Msun" -p --log-pre-intergration --limit-fields "gas.last_halo_masses;gas.densities/#<$critical_gas_density>#" --limit-units "Msun;" --limits-min "$just_above_zero;2.5" --limits-max ";7.5" -c gas.masses --exclude-limits-from-contour --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi
if ! [ -f ./map_high_density_last_enrichment_halo_mass*.png ]
then
    echo ""
    echo "(High Density) Last Halo Mass Map"
    sph-map modified_present_day_snap.hdf5 map_high_density_last_enrichment_halo_mass.png -t "\$M_{\rm halo}\$" --gas -x $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X -y $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y -z "0" --projection -w $COLIBRE_DATA_PIPLINE__SLICE_WIDTH -s gas.last_halo_masses -u "Msun" -p --log-pre-intergration --limit-fields "gas.last_halo_masses;gas.densities/#<$critical_gas_density>#" --limit-units "Msun;" --limits-min "$just_above_zero;7.5" -c gas.masses --exclude-limits-from-contour --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --centre-z-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --side-length 25 --z-side-length $COLIBRE_DATA_PIPLINE__SLICE_DEPTH $COLIBRE_DATA_PIPLINE__MAP_COLOURMAP
fi



# Particle Density Histograms

# Particle Density Histogram
if ! [ -f ./particle_density_hist.png ]
then
    echo ""
    echo "Particle Density Histogram"
    density-hist $present_day_data particle_density_hist.png --log-y-axis
fi

# Particle Density Histogram
if ! [ -f ./particle_density_hist__matched_halo_particles.png ]
then
    echo ""
    echo "(Matched) Particle Density Histogram"
    density-hist modified_present_day_snap.hdf5 particle_density_hist__matched_halo_particles.png --log-y-axis
fi



# Temperature Density Diagrams

# Temp Density Colour=z_Z Weighting=Mass Contours=Mass
if ! [ -f ./plot_temp_dens_redshift.png ]
then
    echo ""
    echo "Temp Density Colour=z_Z Weighting=Mass Contours=Mass"
    t-d $present_day_data -o plot_temp_dens_redshift.png -c gas.mean_metal_weighted_redshifts -u "" --colour-name "\$z_Z\$" --colour-min 0.0 --colour-max 10.2 -l gas.masses --contour-unit Msun --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass
if ! [ -f ./plot_temp_dens_log_redshift.png ]
then
    echo ""
    echo "Temp Density Colour=log_10(1+z_Z) Weighting=Mass Contours=Mass"
    t-d $present_day_data -o plot_temp_dens_log_redshift.png -c 1+gas.mean_metal_weighted_redshifts -u "" --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 -l gas.masses --contour-unit Msun --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=z_Z Weighting=Volume Contours=Volume
if ! [ -f ./plot_temp_dens_redshift_volume_weighting_volume_contours.png ]
then
    echo ""
    echo "Temp Density Colour=z_Z Weighting=Volume Contours=Volume"
    t-d $present_day_data -o plot_temp_dens_redshift_volume_weighting_volume_contours.png -c gas.mean_metal_weighted_redshifts -u "" --colour-name "\$z_Z\$" --colour-min 0.0 --colour-max 10.2 --colour-weight gas.masses/gas.densities -l gas.masses/gas.densities --contour-unit kpc**3 --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume
if ! [ -f ./plot_temp_dens_log_redshift_volume_weighting_volume_contours.png ]
then
    echo ""
    echo "Temp Density Colour=log_10(1+z_Z) Weighting=Volume Contours=Volume"
    t-d $present_day_data -o plot_temp_dens_log_redshift_volume_weighting_volume_contours.png -c 1+gas.mean_metal_weighted_redshifts -u "" --colour-name "\$1+z_Z\$" --log-colour --colour-min 1.0 --colour-max 11.2 --colour-weight gas.masses/gas.densities -l gas.masses/gas.densities --contour-unit kpc**3 --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(Mass) Weighting=Mass
if ! [ -f ./plot_temp_dens_mass.png ]
then
    echo ""
    echo "Temp Density Colour=log_10(Mass) Weighting=Mass"
    t-d $present_day_data -o plot_temp_dens_mass.png --colour-name "\$M\$" --fraction-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(Metal Mass Fraction) Weighting=Mass
if ! [ -f ./plot_temp_dens_metal_mass_fraction.png ]
then
echo ""
echo "Temp Density Colour=log_10(Metal Mass Fraction) Weighting=Mass"
t-d $present_day_data -o plot_temp_dens_metal_mass_fraction.png -c "gas.metal_mass_fractions/$Zsun" -u "" --colour-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-colour --colour-min 0.0 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi
if ! [ -f ./plot_temp_dens_metal_mass_fraction_only_halo_matches.png ]
then
echo ""
echo "(Matched) Temp Density Colour=log_10(Metal Mass Fraction) Weighting=Mass"
t-d modified_present_day_snap.hdf5 -o plot_temp_dens_metal_mass_fraction_only_halo_matches.png -c "gas.metal_mass_fractions/$Zsun" -u "" --colour-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-colour --colour-min 0.0 --limit-fields gas.last_halo_masses --limit-units Msun --limits-min 0 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi
if ! [ -f ./plot_temp_dens_metal_mass_fraction_no_dwarfs.png ]
then
echo ""
echo "(M > 10**10) Temp Density Colour=log_10(Metal Mass Fraction) Weighting=Mass"
t-d modified_present_day_snap.hdf5 -o plot_temp_dens_metal_mass_fraction_no_dwarfs.png -c "gas.metal_mass_fractions/$Zsun" -u "" --colour-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-colour --colour-min 0.0 --limit-fields gas.last_halo_masses --limit-units Msun --limits-min 10000000000 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(Metal Mass) Weighting=Mass
if ! [ -f ./plot_temp_dens_metal_mass.png ]
then
    echo ""
    echo "Temp Density Colour=log_10(Metal Mass) Weighting=Mass"
    t-d $present_day_data -o plot_temp_dens_metal_mass.png -c gas.masses*gas.metal_mass_fractions -u "Msun" --colour-name "\$M_{\\rm Z}\$" --fraction-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(Volume) Weighting=Volume
if ! [ -f ./plot_temp_dens_volume.png ]
then
    echo ""
    echo "Temp Density Colour=log_10(Volume) Weighting=Volume"
    t-d $present_day_data -o plot_temp_dens_volume.png -c gas.masses/gas.densities -u "kpc**3" --colour-name "\$V\$" --fraction-colour --log-colour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=log_10(last halo mass) Weighting=Metal Mass
if ! [ -f ./plot_temp_dens_enrichment_halo_mass.png ]
then
    echo ""
    echo "Temp Density Colour=log_10(last halo mass) Weighting=Metal Mass"
    t-d modified_present_day_snap.hdf5 -o plot_temp_dens_enrichment_halo_mass.png -c gas.last_halo_masses -u "Msun" --colour-name "\$Halo Mass\$" --log-colour --colour-min 0.0 $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
    #graph-past-halo-masses "./;$COLIBRE_DATA_PIPLINE__COMPARISON_CACHED_ENRICHMENT_DATA_DIRECTORY" "plot_temp_dens_enrichment_halo_mass.png" "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" --labels "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP -v -d
    #graph-past-halo-masses ./ "plot_temp_dens_enrichment_halo_mass.png" $present_day_data --centre-x-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_X --centre-y-position $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Y --side-length $COLIBRE_DATA_PIPLINE__SLICE_CENTRE_Z --z-side-length inf
fi

# Temp Density Colour=EnergiesReceivedFromAGNFeedback Weighting=Mass Contours=Mass
if ! [ -f ./plot_temp_dens_agn_energy.png ]
then
    echo ""
    echo "Temp Density Colour=EnergiesReceivedFromAGNFeedback Weighting=Mass Contours=Mass"
    t-d $present_day_data -v -d -o plot_temp_dens_agn_energy.png -c gas.energies_received_from_agnfeedback -u "Mpc**2*Msun/Gyr**2" --colour-name "\$E_{\rm AGN}\$" --colour-min $just_above_zero --log-colour -l gas.masses --contour-unit Msun --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=DensitiesAtLastAGNEvent Weighting=Mass Contours=Mass
if ! [ -f ./plot_temp_dens_density_at_agn.png ]
then
    echo ""
    echo "Temp Density Colour=DensitiesAtLastAGNEvent Weighting=Mass Contours=Mass"
    t-d $present_day_data -o plot_temp_dens_density_at_agn.png -c "gas.densities_at_last_agnevent/#<$critical_gas_density>#" -u "" --colour-name "\$\rho_{\rm AGN}\$ / <\$\rho\$>" --log-colour --limit-fields gas.densities_at_last_agnevent --limit-units "Msun/Mpc**3" --limits-min 0.0 -l gas.masses --contour-unit Msun --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi

# Temp Density Colour=DensitiesAtLastSupernovaEvent Weighting=Mass Contours=Mass
if ! [ -f ./plot_temp_dens_density_at_sn.png ]
then
    echo ""
    echo "Temp Density Colour=DensitiesAtLastSupernovaEvent Weighting=Mass Contours=Mass"
    t-d $present_day_data -o plot_temp_dens_density_at_sn.png -c "gas.densities_at_last_supernova_event/#<$critical_gas_density>#" -u "" --colour-name "\$\rho_{\rm SNe}\$ / <\$\rho\$>" --log-colour --limit-fields gas.densities_at_last_supernova_event --limit-units "Msun/Mpc**3" --limits-min 0.0 -l gas.masses --contour-unit Msun --exclude-limits-from-contour $COLIBRE_DATA_PIPLINE__RHO_T_COLOURMAP
fi







# Gas Line Graphs

# Density Redshift Gas Line Plot X=density Y=log_10(1+z_Z) Weighting=Mass
if ! [ -f ./plot_dens_log_redshift.png ]
then
    echo ""
    echo "Density Redshift Gas Line Plot X=density Y=log_10(1+z_Z) Weighting=Mass"
    gas-line $present_day_data "Data" "plot_dens_log_redshift.png" "densities/#<$critical_gas_density>#" "" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e
fi

# Temp Redshift Gas Line Plot X=temp Y=log_10(1+z_Z) Weighting=Mass
if ! [ -f ./plot_temp_log_redshift.png ]
then
    echo ""
    echo "Temp Redshift Gas Line Plot X=temp Y=log_10(1+z_Z) Weighting=Mass"
    gas-line $present_day_data "Data" "plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e
fi

# Density Metal Mass Fraction Gas Line Plot X=density Y=log_10(M_Z/M) Weighting=Mass
if ! [ -f ./plot_dens_metal_mass_fraction.png ]
then
    echo ""
    echo "Density Redshift Gas Line Plot X=density Y=log_10(M_Z/M) Weighting=Mass"
    gas-line $present_day_data "All Particles" "plot_dens_metal_mass_fraction.png" "densities/#<$critical_gas_density>#" "" "metal_mass_fractions/$Zsun" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 0.0 -e
fi
if ! [ -f ./plot_dens_metal_mass_fraction_only_halo_matches.png ]
then
    echo ""
    echo "(Matched) Density Redshift Gas Line Plot X=density Y=log_10(M_Z/M) Weighting=Mass"
    gas-line modified_present_day_snap.hdf5 "Halo Matched Particles" "plot_dens_metal_mass_fraction_only_halo_matches.png" "densities/#<$critical_gas_density>#" "" "metal_mass_fractions/$Zsun" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 0.0 --limit-fields last_halo_masses --limit-units Msun --limits-min 0 -e
fi
if ! [ -f ./plot_dens_metal_mass_fraction_no_dwarfs.png ]
then
    echo ""
    echo "(M > 10**10) Density Redshift Gas Line Plot X=density Y=log_10(M_Z/M) Weighting=Mass"
    gas-line modified_present_day_snap.hdf5 "\$M_{\rm halo}>10^{10}\$" "plot_dens_metal_mass_fraction_no_dwarfs.png" "densities/#<$critical_gas_density>#" "" "metal_mass_fractions/$Zsun" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 0.0 --limit-fields last_halo_masses --limit-units Msun --limits-min 10000000000 -e
fi

# Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(1+z_Z) Weighting=Mass
if ! [ -f ./convergence_test__plot_dens_log_redshift.png ]
then
    echo ""
    echo "Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(1+z_Z) Weighting=Mass"
    gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "convergence_test__plot_dens_log_redshift.png" "densities/#<$critical_gas_density>#" "" "1+mean_metal_weighted_redshifts" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 1.0 --max-y-field-value 11.2 -e
fi

# Temp Redshift Gas Line Plot Convergence Test X=temp Y=log_10(1+z_Z) Weighting=Mass
if ! [ -f ./convergence_test__plot_temp_log_redshift.png ]
then
    echo ""
    echo "Temp Redshift Gas Line Plot Convergence Test X=temp Y=log_10(1+z_Z) Weighting=Mass"
    gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "convergence_test__plot_temp_log_redshift.png" "temperatures" "K" "1+mean_metal_weighted_redshifts" "" --x-axis-name "\$T\$" --y-axis-name "\$1+z_Z\$" --log-x-axis --log-y-axis --y-axis-weight-field masses --min-y-field-value 1.0 --max-y-field-value 11.2 -e
fi

# Density Metal Mass Fraction Gas Line Plot Convergence Test X=density Y=log_10(M_Z/M) Weighting=Mass
if ! [ -f ./plot_dens_metal_mass_fraction_comparison.png ]
then
    echo ""
    echo "Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(M_Z/M) Weighting=Mass"
    gas-line "$present_day_data;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "plot_dens_metal_mass_fraction_comparison.png" "densities/#<$critical_gas_density>#" "" "metal_mass_fractions/$Zsun" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 0.0 -e
fi
if ! [ -f ./plot_dens_metal_mass_fraction_only_halo_matches_comparison.png ]
then
    echo ""
    echo "(Matched) Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(M_Z/M) Weighting=Mass"
    gas-line "modified_present_day_snap.hdf5;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "plot_dens_metal_mass_fraction_only_halo_matches_comparison.png" "densities/#<$critical_gas_density>#" "" "metal_mass_fractions/$Zsun" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 0.0 --limit-fields last_halo_masses --limit-units Msun --limits-min 0 -e
fi
if ! [ -f ./plot_dens_metal_mass_fraction_no_dwarfs_comparison.png ]
then
    echo ""
    echo "(M > 10**10) Density Redshift Gas Line Plot Convergence Test X=density Y=log_10(M_Z/M) Weighting=Mass"
    gas-line "modified_present_day_snap.hdf5;$COLIBRE_DATA_PIPLINE__COMPARISON_SNAPSHOTS" "$COLIBRE_DATA_PIPLINE__COMPARISON_ALL_LABELS" "plot_dens_metal_mass_fraction_no_dwarfs_comparison.png" "densities/#<$critical_gas_density>#" "" "metal_mass_fractions/$Zsun" "" --x-axis-name "$\rho$/<$\rho$>" --y-axis-name "\$M_Z/M\$ \$\rm Z_{\odot}\$" --log-x-axis --log-y-axis --y-axis-weight-field "masses" --min-y-field-value 0.0 --limit-fields last_halo_masses --limit-units Msun --limits-min 10000000000 -e
fi




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
search_result=( map_last_enrichment_halo_mass*.png )
sed -i "s@{lhm_map_file}@${search_result[0]}@" ./view.html

search_result=( map_low_density_last_enrichment_halo_mass*.png )
sed -i "s@{ldlhm_map_file}@${search_result[0]}@" ./view.html
search_result=( map_mid_density_last_enrichment_halo_mass*.png )
sed -i "s@{mdlhm_map_file}@${search_result[0]}@" ./view.html
search_result=( map_high_density_last_enrichment_halo_mass*.png )
sed -i "s@{hdlhm_map_file}@${search_result[0]}@" ./view.html



echo ""
echo "COMPRESSING FILES"

zip -r ./download_me.zip ./*.png ./*.html



echo ""
echo "PIPELINE COMPLETE"
