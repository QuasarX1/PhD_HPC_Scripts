AUTHOR = "Christopher Rowe"
VERSION = "1.0.1"
DATE = "27/03/2023"
DESCRIPTION = "Creates a graph for the distribution of galaxy stellar mass radial profiles."

import h5py
from matplotlib import pyplot as plt
import numpy as np
import os
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_debug
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
import sys
from time import time
import unyt
import velociraptor as vr



def __main(snap_number, snap_directory, snap_file_template, cat_directory, cat_file_template, groups_directory, groups_file_template):
    snapshot_file_path_template = os.path.join(snap_directory, snap_file_template)
    catalogue_file_path_template = os.path.join(cat_directory, cat_file_template)
    group_file_path_template = os.path.join(groups_directory, groups_file_template)
    
    snap_data = sw.load(snapshot_file_path_template.format(snap_number))
    
    print_verbose_info("Loading star particle data from snapshot.")
    star_particle_ids = snap_data.stars.particle_ids
    star_particle_masses = snap_data.stars.masses.to("Msun")
    star_particle_positions = snap_data.stars.coordinates.to("Mpc")
    print_info(f"Got {len(star_particle_ids)} star particles from snapshot {snap_number}.")

    catalogue_filepath = catalogue_file_path_template.format(snap_number)
    groups_filepath = group_file_path_template.format(snap_number)
    bound_particles_filepath = groups_filepath.replace("catalog_groups", "catalog_particles")
    unbound_particles_filepath = groups_filepath.replace("catalog_groups", "catalog_particles.unbound")
    bound_parttypes_filepath = groups_filepath.replace("catalog_groups", "catalog_parttypes")
    unbound_parttypes_filepath = groups_filepath.replace("catalog_groups", "catalog_parttypes.unbound")

    print_verbose_info("Loading catalogue data.")
    catalogue_data = vr.load(catalogue_filepath)
    halo_ids = np.array(catalogue_data.ids.id, dtype = np.int64)
    halo_masses = np.array(catalogue_data.masses.mass_200crit.to("Msun"), dtype = np.float64)
    halo_centre_x_coords = catalogue_data.positions.xc.to("Mpc")
    halo_centre_y_coords = catalogue_data.positions.yc.to("Mpc")
    halo_centre_z_coords = catalogue_data.positions.zc.to("Mpc")
    halo_r_200 = catalogue_data.radii.r_200crit.to("Mpc")
    
    # Open the catalogue particles files and read data
    with h5py.File(bound_particles_filepath, "r") as file:
        bound_particle_ids = np.array(file["Particle_IDs"], dtype = np.int64)
    with h5py.File(unbound_particles_filepath, "r") as file:
        unbound_particle_ids = np.array(file["Particle_IDs"], dtype = np.int64)

    # Open the catalogue particle types files and read data
    with h5py.File(bound_parttypes_filepath, "r") as file:
        bound_parttypes = np.array(file["Particle_types"], dtype = np.int16)
    with h5py.File(unbound_parttypes_filepath, "r") as file:
        unbound_parttypes = np.array(file["Particle_types"], dtype = np.int16)
        
    # Open the catalogue groups file and read data
    with h5py.File(groups_filepath, "r") as file:
        n_halos = file["Total_num_of_groups"][0]

#        parent_halo_ids = np.array(file["Parent_halo_ID"], dtype = np.int64)

        offsets__bound = np.array(file["Offset"], dtype = np.int64)
        offsets__unbound = np.array(file["Offset_unbound"], dtype = np.int64)

        group_size = np.array(file["Group_Size"], dtype = np.int64)

    print_info(f"Got {n_halos} halos.")
        
#    # Make a lookup to retrive indexed from halo IDs (prevents future searching)
#    halo_index_lookup = { halo_id : halo_index for halo_index, halo_id in enumerate(halo_ids) }
    
    print_verbose_info("Parsing catalogue particle data.")

    # The final storage array contains both bound and unbound particles - calculate the offsets for each halo from the group_size data
    storage_offsets = np.zeros(n_halos, dtype = np.int64)
    storage_offsets[1:] = np.cumsum(group_size[:-1])

    # Only the offsets are stored for the bound/unbound files - compute the number of particles for each halo in each file
    halo_read_lengths__bound = np.zeros(offsets__bound.shape, dtype = np.int64)#TODO: check this call to shape works
    halo_read_lengths__bound[:-1] = offsets__bound[1:] - offsets__bound[:-1]
    halo_read_lengths__bound[-1] = bound_particle_ids.shape[0] - offsets__bound[-1]
    
    halo_read_lengths__unbound = np.zeros(offsets__unbound.shape, dtype = np.int64)#TODO: check this call to shape works
    halo_read_lengths__unbound[:-1] = offsets__unbound[1:] - offsets__unbound[:-1]
    halo_read_lengths__unbound[-1] = unbound_particle_ids.shape[0] - offsets__unbound[-1]
    
    # Create arrays to store the (unfiltered) data
    all_halo_particles__particle_ids = np.empty(group_size.sum(), dtype = np.int64)
    all_halo_particles__particle_types = np.empty(all_halo_particles__particle_ids.shape, dtype = np.int64)
    all_halo_particles__halo_ids = np.empty(all_halo_particles__particle_ids.shape, dtype = np.int64)

    # Read in the data for each halo
    halo_n_stars = np.empty(n_halos, dtype = np.int64)
    for halo_index in range(n_halos):
        all_halo_particles__particle_ids[
            storage_offsets[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index]
        ] = bound_particle_ids[
            offsets__bound[halo_index] : offsets__bound[halo_index] + halo_read_lengths__bound[halo_index]
        ]

        all_halo_particles__particle_ids[
            storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] + halo_read_lengths__unbound[halo_index]
        ] = unbound_particle_ids[
            offsets__unbound[halo_index] : offsets__unbound[halo_index] + halo_read_lengths__unbound[halo_index]
        ]

        all_halo_particles__particle_types[
            storage_offsets[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index]
        ] = bound_parttypes[
            offsets__bound[halo_index] : offsets__bound[halo_index] + halo_read_lengths__bound[halo_index]
        ]

        all_halo_particles__particle_types[
            storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] + halo_read_lengths__unbound[halo_index]
        ] = unbound_parttypes[
            offsets__unbound[halo_index] : offsets__unbound[halo_index] + halo_read_lengths__unbound[halo_index]
        ]

        all_halo_particles__halo_ids[storage_offsets[halo_index] : storage_offsets[halo_index] + group_size[halo_index]] = halo_ids[halo_index]

        halo_n_stars[halo_index] = (all_halo_particles__particle_types[
                                                                         storage_offsets[halo_index] : storage_offsets[halo_index] + halo_read_lengths__bound[halo_index] + halo_read_lengths__unbound[halo_index]
                                                                     ] == 4).sum()

    print_verbose_info("Filtering catalogue particles for the stars.")
        
    # Filter all read data to get only star particles
    halo_star_particles__filter = np.array(all_halo_particles__particle_types, dtype = np.int64) == 4#TODO: stars are type 4, right???

    all_halo_star_particles__particle_ids = all_halo_particles__particle_ids[halo_star_particles__filter]
    all_halo_star_particles__halo_ids = all_halo_particles__halo_ids[halo_star_particles__filter]
    
    sorted_halo_star_indexes = all_halo_star_particles__particle_ids.argsort()
    unsorted_halo_star_indexes = sorted_halo_star_indexes.argsort()
    sorted_halo_star_ids = all_halo_star_particles__particle_ids[sorted_halo_star_indexes]

    sorted_all_star_indexes = star_particle_ids.argsort()
    sorted_all_star_ids = star_particle_ids[sorted_all_star_indexes]
    in_halos_filter = np.isin(sorted_all_star_ids, sorted_halo_star_ids)

    # Sort the data, remove non-halo particles, then un-sort to recover the halo array ordering
    halo_order__star_particle_masses = star_particle_masses[sorted_all_star_indexes][in_halos_filter][unsorted_halo_star_indexes]
    halo_order__star_particle_positions = star_particle_positions[sorted_all_star_indexes][in_halos_filter][unsorted_halo_star_indexes]



    print_verbose_info("Calculating galaxy properties.")
    halo_stellar_masses = np.full(n_halos, -1.0, dtype = np.float64)
    halo_fwhm = np.full(n_halos, -1.0, dtype = np.float64)
    for halo_index in range(n_halos):
        if halo_n_stars[halo_index] > 100:
            print_debug(f"\r{halo_index + 1} out of {n_halos}                ", end = "")
            halo_id = halo_ids[halo_index]
            this_halo_particle_filter = all_halo_star_particles__halo_ids == halo_id
            
            #particle_ids = all_halo_star_particles__particle_ids[this_halo_particle_filter]
            m_stars_halo = halo_order__star_particle_masses[this_halo_particle_filter]
            coords_stars_halo = halo_order__star_particle_positions[this_halo_particle_filter]

            # Find the relitive positions
            #coords_stars_halo -= halo_centres[halo_index]
            coords_stars_halo -= unyt.unyt_array([halo_centre_x_coords[halo_index], halo_centre_y_coords[halo_index], halo_centre_z_coords[halo_index]], units = "Mpc")

            # Radi
            r = np.sqrt((coords_stars_halo**2).sum(axis = 1))

            # Stellar Mass
            halo_stellar_masses[halo_index] = m_stars_halo.sum()

            # cant use fwhm = 2 sqrt(2 ln 2) sigma
            # the radial distribution proberbly isn't gaussian!
            
            hist, bin_edges = np.histogram(r, int(np.sqrt(len(m_stars_halo))), weights = m_stars_halo)
            half_maximum = hist.max() / 2
            halo_fwhm[halo_index] = (bin_edges[:-1][(hist < half_maximum) & (hist != 0.0)][0] + bin_edges[1:][(hist > half_maximum)][-1]) / 2 / halo_r_200[halo_index]
    print_debug("")

    missing_data_filter = halo_stellar_masses != -1.0
    halo_stellar_masses = halo_stellar_masses[missing_data_filter]
    halo_fwhm = halo_fwhm[missing_data_filter]
    n_values = len(halo_fwhm)
    print_info(f"Got FWHM values for {n_values} halos ({100 * n_values / n_halos:.2f}%).")

    print_verbose_info("Plotting.")
    plt.scatter(np.log10(halo_stellar_masses), np.log10(halo_fwhm), s = 2)
    plt.xlabel("${\\rm log_{10}}$ $M_*$ (${\\rm M_\odot}$)")
    plt.ylabel("${\\rm log_{10}}$ ${\\rm FWHM}_*$ / $R_{\\rm 200}$")
    plt.savefig("GalaxySize.png")

if __name__ == "__main__":
    args_info = [
                 ["snap_number",          "String that can be inserted into the templates provided to create a valid file name.", None],
                 ["snap_directory",       "Directory path that holds the snapshot files.", None],
                 ["snap_file_template",   "File name template that produces a valid file name.\nUse '{}' to indicate where the snapshot number string should be inserted.", None],
                 ["cat_directory",        "The same as snap_directory, but for the catalogue files.", None],
                 ["cat_file_template",    "The same as snap_file_template, but for the catalogue files.", None],
                 ["groups_directory",     "The same as snap_directory, but for the groups files.", None],
                 ["groups_file_template", "The same as snap_file_template, but for the groups files.", None],
                ]
    kwargs_info = []
    
    script = ScriptWrapper("galaxy_mass_profiles.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["console_log_printing (local file)", "h5py", "matplotlib", "numpy", "os", "script_wrapper (local file)", "swiftsimio", "sys", "time", "velociraptor"],
                           ["0007 /storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/snapshots snapshot_{}.hdf5 /storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/haloes_sig_1p00 halo_{}.properties.0 /storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/haloes_sig_1p00 halo_{}.catalog_groups.0"],
                           args_info,
                           kwargs_info)

    script.run(__main)