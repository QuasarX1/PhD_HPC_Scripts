import numpy as np
import swiftsimio as sw

from QuasarCode import Console

from ..io.swift_parttype_enum import PartType
from ..io.velociraptor_multi_load import Multifile_VR_Catalogue
from .match_particles import reorder_data
from ..tools import Stopwatch
from ..calculations.simple_fields import get_redshift

def reverse_search(snapshot__present_day: sw.SWIFTDataset, snap_numbers, catalogue_directory, catalogue_prefix_template: str = "haloes_{}", particle_type: PartType = PartType.gas, allow_printing = False):
    stopwatch = Stopwatch()
    
    # Read present day data
    particle_ids__present_day: np.ndarray = particle_type.get_dataset(snapshot__present_day).particle_ids.value
    #indexes_restore_present_day_snapshot_order = particle_ids__present_day.argsort().argsort()
    n_particles_at_present_day = particle_ids__present_day.shape[0]
    present_day_redshift = get_redshift(snapshot__present_day)
    if allow_printing: Console.print_info(f"Got {n_particles_at_present_day} {particle_type} particles at z={present_day_redshift}\n")

    # Maintain a filter list to avoid checking for particles already found
    ids_to_check_filter = np.full(n_particles_at_present_day, True)

    # Collect these values for each particle
    # Where nothing is found, make the value -1
    final_halo_snap_number_index = np.full(n_particles_at_present_day, -1, dtype = np.int16)
    final_halo_ids = np.full(n_particles_at_present_day, -1, dtype = np.int64)
    final_halo_masses = np.full(n_particles_at_present_day, -1.0, dtype = np.float64)

    # For each snapshot, working backwards
    for i in range(len(snap_numbers) - 1, -1, -1):

        # If all the IDs have been found (unlikley), exis the loop
        if ids_to_check_filter.sum() == 0: break

        if allow_printing: Console.print_info(f"Searching snapshot {snap_numbers[i]}.")

        stopwatch.reset()
        stopwatch.start()# ID: 6u7y <- yes, I bashed my head on my keyboard to generate this

        # Open the catalogue file and read data
        catalogue_data = Multifile_VR_Catalogue(catalogue_directory, catalogue_prefix_template.format(snap_numbers[i]))
        
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        halo_ids = catalogue_data.ids.id.value.value
        halo_masses = np.array(catalogue_data.masses.mass_200crit.value.to("Msun"), dtype = np.float64)

        n_halos_by_file, parent_halo_ids, offsets__bound, offsets__unbound, group_size = catalogue_data.read_raw_file_data("catalog_groups",
            [lambda file: np.array([file["Num_of_groups"][0]], dtype = np.int64),
             lambda file: np.array(file["Parent_halo_ID"], dtype = np.int64),
             lambda file: np.array(file["Offset"], dtype = np.int64),
             lambda file: np.array(file["Offset_unbound"], dtype = np.int64),
             lambda file: np.array(file["Group_Size"], dtype = np.int64)])
        
        n_haloes = n_halos_by_file.sum()

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
        
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        halo_data_by_particle = catalogue_data.halo_properties_by_particle(fields = ["particle_ids", ("root_parent_halo_id", mass_tracking_ids)],
                                                                           parttype = particle_type.value)
        halo_particle_ids__catalogue_order = halo_data_by_particle["particle_ids"]
        halo_ids__catalogue_order = halo_data_by_particle["root_parent_halo_id"]
        halo_masses__catalogue_order = np.array([actual_halo_id_to_mass[parent_halo_id] for parent_halo_id in halo_ids__catalogue_order], dtype = np.float64)

        stopwatch.stop()# ID: 6u7y
        if allow_printing: Console.print_verbose_info("Reading catalogue data for snapshot {} took {} s\n(includes sorting by halo particle order)".format(snap_numbers[i], stopwatch.elapsed.total_seconds()))
        if allow_printing: Console.print_info("Snapshot {} contains {} haloes".format(snap_numbers[i], n_haloes))

        stopwatch.reset()
        stopwatch.start()# ID: uyhjn
        
        identified_particle_filter, particle_ids__filtered_snapshot_order, halo_ids__filtered_snapshot_order, halo_masses__filtered_snapshot_order = reorder_data(
            target_ids = particle_ids__present_day[ids_to_check_filter],
            source_ids = halo_particle_ids__catalogue_order,
            source_data = [halo_ids__catalogue_order, halo_masses__catalogue_order],
            missing_data_fill_value = -1.0)
        
        stopwatch.stop()# ID: uyhjn
        if allow_printing: Console.print_verbose_info("Ordering catalogue data for snapshot {} took {} s".format(snap_numbers[i], stopwatch.elapsed.total_seconds()))
        if allow_printing: Console.print_info("Snapshot {} contains {} newly identified halo {} particles".format(snap_numbers[i], identified_particle_filter.sum(), particle_type))

        stopwatch.reset()
        stopwatch.start()# ID: nbbn
        
        expanded_identified_particle_filter = ids_to_check_filter.copy()
        expanded_identified_particle_filter[expanded_identified_particle_filter] = identified_particle_filter

        final_halo_snap_number_index[expanded_identified_particle_filter] = i
        final_halo_ids[expanded_identified_particle_filter] = halo_ids__filtered_snapshot_order[identified_particle_filter]
        final_halo_masses[expanded_identified_particle_filter] = halo_masses__filtered_snapshot_order[identified_particle_filter]
        
        ids_to_check_filter[ids_to_check_filter] = ~identified_particle_filter

        stopwatch.stop()# ID: nbbn
        if allow_printing: Console.print_verbose_info("Inserting {} particles worth of data took {} s".format(identified_particle_filter.sum(), stopwatch.elapsed.total_seconds()))

        if allow_printing: Console.print_info("Completed snapshot {} with {} / {} {} particles identified leaving {} unacounted for\n".format(snap_numbers[i], (~ids_to_check_filter).sum(), n_particles_at_present_day, particle_type, ids_to_check_filter.sum()))

    final_halo_snap_numbers = np.array([snap_numbers[i] if i != -1 else "-999" for i in final_halo_snap_number_index], dtype = str)

    return final_halo_snap_number_index, final_halo_snap_numbers, final_halo_ids, final_halo_masses