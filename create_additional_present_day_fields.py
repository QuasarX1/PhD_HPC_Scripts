AUTHOR = "Christopher Rowe"
VERSION = "1.1.0"
DATE = "29/03/2023"
DESCRIPTION = "Inserts the last halo mass data into a copy of the latest snapshot."

import pickle
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.IO.Text.console import print_info, print_debug
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
import unyt

source_file_relitive_add_to_path(__file__)
from save_swift_snap_field import save_particle_fields, get_cgs_conversions, PartType

def __main(data):
    snap_data_present_day = sw.load(data)

    with open("gas_particle_ejection_tracking__halo_snapshot_numbers.pickle", "rb") as file:
        final_halo_snap_number_index = pickle.load(file)
    with open("gas_particle_ejection_tracking__halo_ids_in_snapshot.pickle", "rb") as file:
        final_halo_ids = pickle.load(file)
    with open("gas_particle_ejection_tracking__halo_masses.pickle", "rb") as file:
        final_halo_masses = pickle.load(file)

    #TODO: find fields of indexes to set as template metadata fields for other datasets
    final_halo_masses = final_halo_masses * unyt.physical_constants.Msun_cgs / get_cgs_conversions("Masses", PartType.gas, snap_data_present_day)[0]

    snap_data_present_day.gas.last_halo_snap_number_index = final_halo_snap_number_index
    snap_data_present_day.gas.last_halo_ids = final_halo_ids
    snap_data_present_day.gas.last_halo_masses = final_halo_masses
    save_particle_fields(field_name = ["last_halo_snap_number_index", "last_halo_ids", "last_halo_masses"],
                         description = ["The snapshot index of the last VELOCIraptor halo interacted with. Defaluts to -1 if no halo is found.",
                                        "The id of the last VELOCIraptor halo interacted with. Defaluts to -1 if no halo is found.",
                                        "The mass of the last VELOCIraptor halo interacted with. Defaluts to -1 if no halo is found."],
                         part_type = PartType.gas,
                         current_file = snap_data_present_day,
                         new_file = "modified_present_day_snap.hdf5")

if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the SWIFT data file.", None]
                ]
    kwargs_info = []
    
    script = ScriptWrapper("create_additional_present_day_fields.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["console_log_printing (local file)", "os", "pickle", "save_swift_snap_field (local file)", "script_wrapper (local file)", "swiftsimio", "sys"],
                           ["/storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/snapshots/snapshot_0007.hdf5"],
                           args_info,
                           kwargs_info)

    script.run(__main)
