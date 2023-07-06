raise DeprecationWarning("This dosen't work and is not up-to-date!")

AUTHOR = "Christopher Rowe"
VERSION = "1.1.0"
DATE = "24/04/2023"
DESCRIPTION = "Finds the distance at present day between the ejected gas particles and their last host haloes."

import h5py
import numpy as np
import os
import pickle
from QuasarCode import source_file_relitive_add_to_path
#from QuasarCode.IO.Text.console import print_info, Console.print_verbose_info, print_warning, print_debug
from QuasarCode import Console
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
import sys
from unyt import unyt_array
import velociraptor as vr

source_file_relitive_add_to_path(__file__)
from save_swift_snap_field import save_particle_fields, get_cgs_conversions, PartType, SIGNED_FLOAT_64

Mpc_cgs = 3.0857E24#1E6 * 3.0857E16 * 100

def __main(data: str, present_day_snap_number: str, cat_directory: str, cat_file_template: str):
    # Create template paths
    catalogue_file_path_template = os.path.join(cat_directory, cat_file_template)

    # Load the present day snapshot with the extra fields
    Console.print_verbose_info("Loading data file.")
    Console.print_debug(f"Loading data from {data}")
    snap_data = sw.load(data)
    gas_coords = snap_data.gas.coordinates
    try:
        traced_halo_ids = snap_data.gas.traced_halo_ids
    except:
        Console.print_warning("The data file provided does not include the additional fields created by the pipeline. These fields must be present. Assuming this file to be a souce snapshot and force terminating to avoid modifying the origanal snapshots!")
        sys.exit()
    

    
    Console.print_verbose_info("Loading catalogue data.")
    Console.print_debug(f"Loading data from {catalogue_file_path_template.format(present_day_snap_number)}")

    catalogue = vr.load(catalogue_file_path_template.format(present_day_snap_number))
    halo_ids = catalogue.ids.id
    potential_centres = unyt_array(np.stack((catalogue.positions.xcminpot.to("Mpc").v, catalogue.positions.ycminpot.to("Mpc").v, catalogue.positions.zcminpot.to("Mpc").v), axis = -1), "Mpc")

    unique_halo_ids = np.unique(traced_halo_ids[traced_halo_ids != -1])

    Console.print_verbose_info("Calculating particle displacement from last halo.")
    #halo_position_deltas = unyt_array(np.full(gas_coords.shape, 0), "Mpc")
    halo_centre_by_particle = unyt_array(np.full(gas_coords.shape, 0), "Mpc")
    output_ids = [unique_halo_ids[unique_halo_ids >= value][0] for value in np.percentile(unique_halo_ids, [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95])]
    n_unique_halos = len(unique_halo_ids)
    for i, halo_id in enumerate(unique_halo_ids):
        try:
            if halo_id in output_ids:
                Console.print_verbose_info(f"Doing halo {i + 1} out of {n_unique_halos}")
        except Exception as e:
            Console.print_debug(i, halo_id)
            Console.print_debug(output_ids)
            raise e
        #snap_filter = traced_halo_ids == halo_id
        #halo_position_deltas[snap_filter, :] = gas_coords[snap_filter, :] - potential_centres[halo_ids == halo_id][0]
        halo_centre_by_particle[traced_halo_ids == halo_id, :] = potential_centres[halo_ids == halo_id][0]
    halo_position_deltas = gas_coords - halo_centre_by_particle

    # Wrap the coordinates in each dimension
    Console.print_verbose_info("Box wrapping vectors.")
    halo_ejection_vectors = halo_position_deltas.copy()
    box_size = unyt_array(snap_data.metadata.header["BoxSize"], "Mpc")
    half_box_size = box_size / 2

    #Console.print_debug(np.abs(halo_ejection_vectors[:, :]) > np.tile(half_box_size, (halo_ejection_vectors.shape[0], 1)))

    halo_ejection_vectors = np.where(np.abs(halo_ejection_vectors[:, :]) > np.tile(half_box_size, (halo_ejection_vectors.shape[0], 1)),
                                     halo_ejection_vectors[:, :] - ((halo_ejection_vectors[:, :] / np.abs(halo_ejection_vectors[:, :])) * np.tile(box_size, (halo_ejection_vectors.shape[0], 1))),
                                     halo_ejection_vectors)
    
    # Calculate radii
    Console.print_verbose_info("Calculating radii.")
    halo_position_radii = np.sqrt((halo_ejection_vectors**2).sum(axis = 1))
    halo_position_radii[traced_halo_ids == -1] = -1
        


    # Write data to temp files and append to the modified snapshot

    Console.print_verbose_info("Saving data to serialised file.")

    with open("gas_particle_ejection_tracking__present_day_ejection_displacement.pickle", "wb") as file:
        pickle.dump(halo_position_deltas[:, :], file)
    with open("gas_particle_ejection_tracking__present_day_ejection_vector.pickle", "wb") as file:
        pickle.dump(halo_ejection_vectors[:, :], file)
    with open("gas_particle_ejection_tracking__present_day_ejection_distance.pickle", "wb") as file:
        pickle.dump(halo_position_radii[:], file)

    Console.print_verbose_info("Appending to modified snapshot file.")

    halo_position_deltas = halo_position_deltas[:, :] * Mpc_cgs / get_cgs_conversions("Coordinates", PartType.gas, snap_data)[0]
    halo_ejection_vectors = halo_ejection_vectors[:, :] * Mpc_cgs / get_cgs_conversions("Coordinates", PartType.gas, snap_data)[0]
    halo_position_radii = halo_position_radii[:] * Mpc_cgs / get_cgs_conversions("SmoothingLengths", PartType.gas, snap_data)[0]

    snap_data.gas.last_halo_ejection_displacement = halo_position_deltas
    snap_data.gas.last_halo_ejection_vector = halo_ejection_vectors
    snap_data.gas.last_halo_ejection_distance = halo_position_radii
    save_particle_fields(field_name = ["last_halo_ejection_displacement", "last_halo_ejection_vector", "last_halo_ejection_distance"],
                         description = ["Displacement vectors for ejected gas particles where the last known halo has been identified at present day. Defaluts to [0, 0, 0] if no halo is found.",
                                        "Ejection vectors for ejected gas particles where the last known halo has been identified at present day. A box wrapped version of last_halo_ejection_displacement. Defaluts to [0, 0, 0] if no halo is found.",
                                        "Ejection radius for gas particles where the last known halo has been identified at present day. Defaluts to -1 if no halo is found."],
                         part_type = PartType.gas,
                         current_file = snap_data,
                         new_file = None,
                         template_field = ["Coordinates", "Coordinates", "SmoothingLengths"],
                         datatype_override = [None, None, SIGNED_FLOAT_64])

    Console.print_verbose_info("DONE")



if __name__ == "__main__":
    args_info = [
                 ["data",                    "Path to the modified present day SWIFT data file.", None],
                 ["present_day_snap_number", "Snapshot number string of the snapshot being used as the 'present day'.", None],
                 ["cat_directory",           "The same as snap_directory, but for the catalogue files.", None],
                 ["cat_file_template",       "The same as snap_file_template, but for the catalogue files.", None]
                ]
    kwargs_info = []
    
    script = ScriptWrapper("calculate_ejection_distance.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["numpy", "os", "pickle", "QuasarCode", "save_swift_snap_field (local file)", "swiftsimio", "unyt"],
                           ["/storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/snapshots/snapshot_0007.hdf5"],
                           args_info,
                           kwargs_info)

    script.run(__main)
