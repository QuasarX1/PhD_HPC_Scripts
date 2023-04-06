AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "03/04/2023"
DESCRIPTION = "Finds the halo index of the past tracked halos."

import h5py
import numpy as np
import os
import pickle
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_warning, print_debug
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
import sys
import unyt
import velociraptor as vr

source_file_relitive_add_to_path(__file__)
from save_swift_snap_field import save_particle_fields, get_cgs_conversions, PartType, SIGNED_INT_64

def __main(data: str, present_day_snap_number: str, cat_directory: str, cat_file_template: str, groups_directory: str, groups_file_template: str):
    # Create template paths
    catalogue_file_path_template = os.path.join(cat_directory, cat_file_template)
    group_file_path_template = os.path.join(groups_directory, groups_file_template)

    # Load the present day snapshot with the extra fields
    print_verbose_info("Loading data file.")
    print_debug(f"Loading data from {data}")
    present_day_data = sw.load(data)
    


    # Read in the extra data fields and format appropriately
    # Filter down to only those with valid values
    print_verbose_info("Reading tracked halo data.")
    try:
        tracked_particle_filter = present_day_data.gas.last_halo_ids != -1
    except:
        print_warning("The data file provided does not include the additional fields created by the pipeline. These fields must be present. Assuming this file to be asouce snapshot and force terminating to avoid modifying the origanal snapshots!")
        sys.exit()
    snapshot_numbers = np.array([f"{int(i):4.0f}".replace(" ", "0") for i in present_day_data.gas.last_halo_snap_number[tracked_particle_filter]], dtype = str)
#    halo_ids = np.array(present_day_data.gas.last_halo_ids[tracked_particle_filter], dtype = int)
    halo_ids = present_day_data.gas.last_halo_ids[tracked_particle_filter]

    # Identify the unique snapshots (in case not all are used)
    unique_snap_numbers, snapshot_indices = np.unique(snapshot_numbers, return_index = True)

    # Loop over each halo in each snapshot and get the ID of its most bound particle
    print_verbose_info("Identifying most bound particles at tracked snapshot.")
    most_bound_particle_ids = np.empty(halo_ids.shape)
    for i, snap_number in enumerate(unique_snap_numbers):
        print_verbose_info(f"Doing snapshot {snap_number}")
        snapshot_filter = snapshot_numbers == snap_number
        unique_halos = np.unique(halo_ids[snapshot_filter])
    
        catalogue = vr.load(catalogue_file_path_template.format(snap_number))
        
        for halo_id in unique_halos:
            halo_filter = snapshot_filter & (halo_ids == halo_id)
            
            most_bound_particle_ids[halo_filter] = catalogue.ids.id_mbp[catalogue.ids.id == halo_id][0]
            


    # Get the halo ids that match every present day particle

    # Select the passed filepaths and create versions for other catalogue file types
    present_day_groups_filepath = group_file_path_template.format(present_day_snap_number)
    present_day_bound_particles_filepath = present_day_groups_filepath.replace("catalog_groups", "catalog_particles")
    present_day_bound_parttypes_filepath = present_day_groups_filepath.replace("catalog_groups", "catalog_parttypes")

    print_verbose_info("Reading present day catalogue particle info.")

    # Open the catalogue particles files and read data
    with h5py.File(present_day_bound_particles_filepath, "r") as file:
        bound_particle_ids = np.array(file["Particle_IDs"], dtype = np.int64)

    # Open the catalogue particle types files and read data
    with h5py.File(present_day_bound_parttypes_filepath, "r") as file:
        bound_parttypes = np.array(file["Particle_types"], dtype = np.int16)

    # Open the catalogue groups file and read data
    with h5py.File(present_day_groups_filepath, "r") as file:
        n_halos = file["Total_num_of_groups"][0]
        offsets__bound = np.array(file["Offset"], dtype = np.int64)

    offset_ends = np.empty(offsets__bound.shape, dtype = int)
    offset_ends[:-1] = offsets__bound[1:]
    offset_ends[-1] = len(bound_parttypes)

    present_day_catalogue = vr.load(catalogue_file_path_template.format(present_day_snap_number))

    print_verbose_info("Creating lookup for halo IDs")

    halo_id_by_bound_particle = np.empty(bound_parttypes.shape)
    for i in range(n_halos):
        halo_id_by_bound_particle[offsets__bound[i] : offset_ends[i]] = present_day_catalogue.ids.id[i]



    # Get the present day halo id containing the most bound particle from the tracking snapshot

    print_verbose_info("Identifying present day haloes.")

    unique_ids = np.unique(most_bound_particle_ids)
    
    number_not_traced = 0
    matched_present_day_halo_ids = np.empty(halo_ids.shape)
    for unique_id in unique_ids:
        try:
            matched_present_day_halo_ids[most_bound_particle_ids == unique_id] = halo_id_by_bound_particle[bound_particle_ids == unique_id][0]
        except IndexError as e:
            print_warning(e)
            n_affected = (most_bound_particle_ids == unique_id).sum()
            print_warning(f"Unable to identify the halo containing particle {unique_id}.\n{n_affected} particles affected.")
            matched_present_day_halo_ids[most_bound_particle_ids == unique_id] = -1
            number_not_traced = number_not_traced + n_affected
    print_info("{:.3f}% of the tracked particles have an identifiable halo at present day.\n{} were not accounted for.".format((1 - (number_not_traced / matched_present_day_halo_ids.shape[0])) * 100, number_not_traced))

    print_verbose_info("Aligning data with all particles in present day snapshot.")
    present_day_halo_ids = np.full(tracked_particle_filter.shape, -1)
    present_day_halo_ids[tracked_particle_filter] = matched_present_day_halo_ids
    


    # Write data to temp files and append to the modified snapshot

    print_verbose_info("Saving data to serialised file.")

    with open("gas_particle_ejection_tracking__present_day_halo_id.pickle", "wb") as file:
        pickle.dump(present_day_halo_ids, file)

    print_verbose_info("Appending to modified snapshot file.")

    present_day_data.gas.traced_halo_ids = present_day_halo_ids
    save_particle_fields(field_name = "traced_halo_ids",
                         description = "The id of the halo at present day which corresponds to the halo each particle last interacted with. Defaluts to -1 if no halo is found.",
                         part_type = PartType.gas,
                         current_file = present_day_data,
                         new_file = None,
                         template_field = "ParticleIDs",
                         datatype_override = SIGNED_INT_64)

    print_verbose_info("DONE")



if __name__ == "__main__":
    args_info = [
                 ["data",                    "Path to the modified present day SWIFT data file.", None],
                 ["present_day_snap_number", "Snapshot number string of the snapshot being used as the 'present day'.", None],
                 ["cat_directory",           "The same as snap_directory, but for the catalogue files.", None],
                 ["cat_file_template",       "The same as snap_file_template, but for the catalogue files.", None],
                 ["groups_directory",        "The same as snap_directory, but for the groups files.", None],
                 ["groups_file_template",    "The same as snap_file_template, but for the groups files.", None]
                ]
    kwargs_info = []
    
    script = ScriptWrapper("find_present_day_halo_counterparts.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["numpy", "os", "pickle", "QuasarCode", "save_swift_snap_field (local file)", "swiftsimio", "unyt"],
                           ["/storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/snapshots/snapshot_0007.hdf5"],
                           args_info,
                           kwargs_info)

    script.run(__main)
