AUTHOR = "Christopher Rowe"
VERSION = "7.0.0"
DATE = "06/07/2023"
DESCRIPTION = "Identifies the last halo a gas particle was found in and records the mass of the largest halo in the structure."

import h5py
import numpy as np
import os
import pickle
import swiftsimio as sw
from time import time
import velociraptor as vr

from QuasarCode import source_file_relitive_add_to_path, Settings, Console
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.io import Multifile_VR_Catalogue



def __main(snap_numbers, snap_directory, snap_file_template, cat_directory, cat_file_template, groups_directory, groups_file_template):

    __DEBUG = Settings.debug

    snapshot_file_path_template = os.path.join(snap_directory, snap_file_template)
#    catalogue_file_path_template = os.path.join(cat_directory, cat_file_template)
#    group_file_path_template = os.path.join(groups_directory, groups_file_template)

    Console.print_debug("Reading z = 0 snapshot data.")

    # Load a list of the gas particle IDs at z=0
    snap_data_present_day = sw.load(snapshot_file_path_template.format(snap_numbers[-1]))
    gas_ids_present_day = np.array(snap_data_present_day.gas.particle_ids, dtype = np.int64)

    # Sort the ID list and retain the ability to un-sort it
    indexes_to_sort__gas_ids_present_day = gas_ids_present_day.argsort()
    indexes_to_unsort__gas_ids_present_day = indexes_to_sort__gas_ids_present_day.argsort()
    gas_ids_present_day = gas_ids_present_day[indexes_to_sort__gas_ids_present_day]# Do this again with the other index list from above to reverse

    n_gas_particles_z_0 = len(gas_ids_present_day)

    Console.print_info(f"Got {n_gas_particles_z_0} gas particles at z=0.")

    # Maintain a filter list to avoid checking for particles already found
    ids_to_check = np.full(n_gas_particles_z_0, True)

    # Collect these values for each particle
    # Where nothing is found, make the value -1
    final_halo_snap_number_index = np.full(n_gas_particles_z_0, -1, dtype = np.int16)
    final_halo_ids = np.full(n_gas_particles_z_0, -1, dtype = np.int64)
    final_halo_masses = np.full(n_gas_particles_z_0, -1.0, dtype = np.float64)

    # For each snapshot, working backwards
    for i in range(len(snap_numbers) - 1, -1, -1):

        # If all the IDs have been found (unlikley), exis the loop
        if ids_to_check.sum() == 0: break

        Console.print_verbose_info(f"Searching snapshot {snap_numbers[i]}.")

        # Select the passed filepaths and create versions for other catalogue file types
#        catalogue_filepath = catalogue_file_path_template.format(snap_numbers[i])
#        groups_filepath = group_file_path_template.format(snap_numbers[i])
#        bound_particles_filepath = groups_filepath.replace("catalog_groups", "catalog_particles")
#        unbound_particles_filepath = groups_filepath.replace("catalog_groups", "catalog_particles.unbound")
#        bound_parttypes_filepath = groups_filepath.replace("catalog_groups", "catalog_parttypes")
#        unbound_parttypes_filepath = groups_filepath.replace("catalog_groups", "catalog_parttypes.unbound")

        # Start the timer
        start_time = time()
        
        # Open the catalogue file and read data
#        catalogue_data = vr.load(catalogue_filepath)
#        halo_ids = np.array(catalogue_data.ids.id, dtype = np.int64)
#        halo_masses = np.array(catalogue_data.masses.mass_200crit.to("Msun"), dtype = np.float64)

        catalogue_data = Multifile_VR_Catalogue(cat_directory, cat_file_template.format(snap_numbers[i]).split(".")[0])
        halo_ids = np.array(catalogue_data.ids.id.value, dtype = np.int64)
        halo_masses = np.array(catalogue_data.masses.mass_200crit.value.to("Msun"), dtype = np.float64)
        
#        # Open the catalogue particles files and read data
#        with h5py.File(bound_particles_filepath, "r") as file:
#            bound_particle_ids = np.array(file["Particle_IDs"], dtype = np.int64)
#        with h5py.File(unbound_particles_filepath, "r") as file:
#            unbound_particle_ids = np.array(file["Particle_IDs"], dtype = np.int64)
#
#        # Open the catalogue particle types files and read data
#        with h5py.File(bound_parttypes_filepath, "r") as file:
#            bound_parttypes = np.array(file["Particle_types"], dtype = np.int16)
#        with h5py.File(unbound_parttypes_filepath, "r") as file:
#            unbound_parttypes = np.array(file["Particle_types"], dtype = np.int16)
#
#        # NOTE: this assumes there is only one of each file per snapshot!
#        # Open the catalogue groups file and read data
#        with h5py.File(groups_filepath, "r") as file:
#            n_halos = file["Total_num_of_groups"][0]
#
#            parent_halo_ids = np.array(file["Parent_halo_ID"], dtype = np.int64)
#
#            offsets__bound = np.array(file["Offset"], dtype = np.int64)
#            offsets__unbound = np.array(file["Offset_unbound"], dtype = np.int64)
#
#            group_size = np.array(file["Group_Size"], dtype = np.int64)

        # Open the catalogue particles files and read data
        bound_particle_ids, bound_particle_number_by_file = catalogue_data.read_raw_file_data("catalog_particles",
            [lambda file: np.array(file["Particle_IDs"], dtype = np.int64),
             lambda file: np.array([file["Num_of_particles_in_groups"][0]], dtype = np.int64)])
        unbound_particle_ids, unbound_particle_number_by_file = catalogue_data.read_raw_file_data("catalog_particles.unbound",
            [lambda file: np.array(file["Particle_IDs"], dtype = np.int64),
             lambda file: np.array([file["Num_of_particles_in_groups"][0]], dtype = np.int64)])

        # Open the catalogue particle types files and read data
        bound_parttypes = catalogue_data.read_raw_file_data("catalog_parttypes",
                                                            lambda file: np.array(file["Particle_types"], dtype = np.int16))
        unbound_parttypes = catalogue_data.read_raw_file_data("catalog_parttypes.unbound",
                                                              lambda file: np.array(file["Particle_types"], dtype = np.int16))
        
        # Open the catalogue groups file and read data
        n_halos_by_file, parent_halo_ids, offsets__bound, offsets__unbound, group_size = catalogue_data.read_raw_file_data("catalog_groups",
            [lambda file: np.array([file["Num_of_groups"][0]], dtype = np.int64),
             lambda file: np.array(file["Parent_halo_ID"], dtype = np.int64),
             lambda file: np.array(file["Offset"], dtype = np.int64),
             lambda file: np.array(file["Offset_unbound"], dtype = np.int64),
             lambda file: np.array(file["Group_Size"], dtype = np.int64)])
        
        n_halos = n_halos_by_file.sum()

        modified_offset_haloes = 0
        next_offset_boost_bound = 0
        next_offset_boost_unbound = 0
        for file_index, n_halos_in_file in enumerate(n_halos_by_file):
            data_slice = slice(modified_offset_haloes, modified_offset_haloes + n_halos_in_file)

            offsets__bound[data_slice] = offsets__bound[data_slice] + next_offset_boost_bound
            offsets__unbound[data_slice] = offsets__unbound[data_slice] + next_offset_boost_unbound

            modified_offset_haloes += n_halos_in_file

            #last_item = modified_offset_haloes - 1
            #next_offset_boost_bound = offsets__bound[last_item] + bound_particle_number_by_file[file_index]
            #next_offset_boost_unbound = offsets__unbound[last_item] + unbound_particle_number_by_file[file_index]
            next_offset_boost_bound += bound_particle_number_by_file[file_index]
            next_offset_boost_unbound += unbound_particle_number_by_file[file_index]
            
        # Stop the timer
        stop_time = time()

        Console.print_verbose_info("Reading catalogue data for snapshot {} took {} s for {} halos".format(i, stop_time - start_time, n_halos))



        # Start the timer
        start_time = time()

        # Make a lookup to retrive indexed from halo IDs (prevents future searching)
        halo_index_lookup = { halo_id : halo_index for halo_index, halo_id in enumerate(halo_ids) }
        
        # The parent halo is the tracking target - where a parent is not present, assign the halo's own ID
        # Itterate untill the top level parent is found in all cases
        parent_halos_filter = parent_halo_ids == -1

        mass_tracking_ids = parent_halo_ids.copy()
        parent_not_found_filter = np.full(halo_ids.shape, True)

        mass_tracking_ids[parent_halos_filter] = halo_ids[parent_halos_filter]
        parent_not_found_filter[parent_halos_filter] = False

        while parent_not_found_filter.sum() > 0:
            for halo_index in np.where(parent_not_found_filter)[0]:
                new_parent_id = parent_halo_ids[halo_index_lookup[mass_tracking_ids[halo_index]]]

                if new_parent_id == -1:
                    parent_not_found_filter[halo_index] = False
                else:
                    mass_tracking_ids[halo_index] = new_parent_id

        # Make a lookup to easily retrive the mass of a given (parent) halo - only the parent halos are being looked up, so no point in processing the others
        actual_halo_id_to_mass = { halo_ids[i]: halo_masses[i] for i in np.where(parent_halos_filter)[0] }

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
            
        # Stop the timer
        stop_time = time()

        Console.print_verbose_info("Prep to collect data for snapshot {} took {} s".format(i, stop_time - start_time))



        # Start the timer
        start_time = time()

        # Create arrays to store the (unfiltered) data
        all_halo_particles__particle_ids = np.empty(group_size.sum(), dtype = np.int64)
        all_halo_particles__particle_types = np.empty(all_halo_particles__particle_ids.shape, dtype = np.int64)
        all_halo_particles__halo_ids = np.empty(all_halo_particles__particle_ids.shape, dtype = np.int64)
        halo_masses = np.empty(all_halo_particles__particle_ids.shape, dtype = np.float64)

        

        # Read in the data for each halo
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

            halo_masses[storage_offsets[halo_index] : storage_offsets[halo_index] + group_size[halo_index]] = actual_halo_id_to_mass[mass_tracking_ids[halo_index]]
            
        # Filter all read data to get only gas particles
        halo_gas_particles__filter = np.array(all_halo_particles__particle_types, dtype = np.int64) == 0

        all_halo_gas_particles__particle_ids = all_halo_particles__particle_ids[halo_gas_particles__filter]
        all_halo_gas_particles__halo_ids = all_halo_particles__halo_ids[halo_gas_particles__filter]
        all_halo_gas_particles__halo_masses = halo_masses[halo_gas_particles__filter]
            
        # Stop the timer
        stop_time = time()

        Console.print_verbose_info("Filtering data for snapshot {} took {} s for {} gas particles".format(i, stop_time - start_time, len(all_halo_gas_particles__particle_ids)))



        # Start the timer
        start_time = time()

        sorted_id_indexes = all_halo_gas_particles__particle_ids.argsort()

        all_halo_gas_particles__particle_ids = all_halo_gas_particles__particle_ids[sorted_id_indexes]
        all_halo_gas_particles__halo_ids = all_halo_gas_particles__halo_ids[sorted_id_indexes]
        all_halo_gas_particles__halo_masses = all_halo_gas_particles__halo_masses[sorted_id_indexes]

        unselected_data_in_halos_filter = np.isin(all_halo_gas_particles__particle_ids, gas_ids_present_day[ids_to_check])
        unselected_data_avalible_filter = ids_to_check & np.isin(gas_ids_present_day, all_halo_gas_particles__particle_ids[unselected_data_in_halos_filter])

        final_halo_ids[unselected_data_avalible_filter] = all_halo_gas_particles__halo_ids[unselected_data_in_halos_filter]
        final_halo_masses[unselected_data_avalible_filter] = all_halo_gas_particles__halo_masses[unselected_data_in_halos_filter]
        final_halo_snap_number_index[unselected_data_avalible_filter] = i
        ids_to_check[unselected_data_avalible_filter] = False

        # Stop the timer
        stop_time = time()

        Console.print_verbose_info("Matching IDs for snapshot {} took {} s".format(i, stop_time - start_time))

        Console.print_verbose_info("{} gas particles at z=0 still unaccounted for.".format(ids_to_check.sum()))



    # Return all data to the snapshot data order
    final_halo_snap_number_index = final_halo_snap_number_index[indexes_to_unsort__gas_ids_present_day]
    final_halo_snap_numbers = np.array([snap_numbers[i] if i != -1 else "-999" for i in final_halo_snap_number_index], dtype = str)
    final_halo_ids = final_halo_ids[indexes_to_unsort__gas_ids_present_day]
    final_halo_masses = final_halo_masses[indexes_to_unsort__gas_ids_present_day]

    Console.print_verbose_info(f"All data retrived. Saving to files.")

    with open("gas_particle_ejection_tracking__halo_snapshot_number_indexes.pickle", "wb") as file:
        pickle.dump(final_halo_snap_number_index, file)
    with open("gas_particle_ejection_tracking__halo_snapshot_numbers.pickle", "wb") as file:
        pickle.dump(final_halo_snap_numbers, file)
    with open("gas_particle_ejection_tracking__halo_ids_in_snapshot.pickle", "wb") as file:
        pickle.dump(final_halo_ids, file)
    with open("gas_particle_ejection_tracking__halo_masses.pickle", "wb") as file:
        pickle.dump(final_halo_masses, file)



if __name__ == "__main__":
    import sys
    print(sys.argv)
    args_info = [
                 ["snap_numbers",         "Semicolon seperated list of strings that can be inserted into\nthe templates provided to create valid file names.\nSnapshots should be specified in chronological order.", ScriptWrapper.make_list_converter(";")],
                 ["snap_directory",       "Directory path that holds the snapshot files.", None],
                 ["snap_file_template",   "File name template that produces a valid file name.\nUse '{}' to indicate where the snapshot number string should be inserted.", None],
                 ["cat_directory",        "The same as snap_directory, but for the catalogue files.", None],
                 ["cat_file_template",    "The same as snap_file_template, but for the catalogue files.", None],
                 ["groups_directory",     "The same as snap_directory, but for the groups files.", None],
                 ["groups_file_template", "The same as snap_file_template, but for the groups files.", None],
                ]
    kwargs_info = []
    
    script = ScriptWrapper("find_gas_last_halo_masses.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["h5py", "numpy", "os", "pickle", "QuasarCode", "swiftsimio", "sys", "time", "velociraptor"],
                           ["0000;0001;0002;0003;0004;0005;0006;0007 /storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/snapshots snapshot_{}.hdf5 /storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/haloes_sig_1p00 halo_{}.properties.0 /storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/haloes_sig_1p00 halo_{}.catalog_groups.0"],
                           args_info,
                           kwargs_info)

    script.run(__main)
