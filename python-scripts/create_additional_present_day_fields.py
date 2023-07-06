AUTHOR = "Christopher Rowe"
VERSION = "2.0.0"
DATE = "06/07/2023"
DESCRIPTION = "Inserts the last halo mass data into a copy of the latest snapshot."

import numpy as np
import pickle
import swiftsimio as sw
import unyt

from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.io import save_particle_fields, get_cgs_conversions, PartType, SIGNED_INT_64
from ..contra.io.save_swift_snap_field import SIGNED_INT_64

def __main(data):
    snap_data_present_day = sw.load(data)

    with open("gas_particle_ejection_tracking__halo_snapshot_number_indexes.pickle", "rb") as file:
        final_halo_snap_number_index = pickle.load(file)
    with open("gas_particle_ejection_tracking__halo_snapshot_numbers.pickle", "rb") as file:
        final_halo_snap_numbers = pickle.load(file)
    with open("gas_particle_ejection_tracking__halo_ids_in_snapshot.pickle", "rb") as file:
        final_halo_ids = pickle.load(file)
    with open("gas_particle_ejection_tracking__halo_masses.pickle", "rb") as file:
        final_halo_masses = pickle.load(file)

    final_halo_snap_numbers = np.array([int(s) for s in final_halo_snap_numbers], dtype = np.int16)

    final_halo_masses = final_halo_masses * unyt.physical_constants.Msun_cgs / get_cgs_conversions("Masses", PartType.gas, snap_data_present_day)[0]

    snap_data_present_day.gas.last_halo_snap_number_index = final_halo_snap_number_index
    snap_data_present_day.gas.last_halo_snap_number = final_halo_snap_numbers
    snap_data_present_day.gas.last_halo_ids = final_halo_ids
    snap_data_present_day.gas.last_halo_masses = final_halo_masses
    save_particle_fields(field_name = ["last_halo_snap_number_index", "last_halo_snap_number", "last_halo_ids", "last_halo_masses"],
                         description = ["The snapshot index of the last VELOCIraptor halo interacted with. Defaluts to -1 if no halo is found.",
                                        "The snapshot number of the last VELOCIraptor halo interacted with. Defaluts to -999 if no halo is found.",
                                        "The id of the last VELOCIraptor halo interacted with. Defaluts to -1 if no halo is found.",
                                        "The mass of the last VELOCIraptor halo interacted with. Defaluts to -1 if no halo is found."],
                         part_type = PartType.gas,
                         current_file = snap_data_present_day,
                         new_file = "modified_present_day_snap.hdf5",
                         template_field = ["ParticleIDs", "ParticleIDs", "ParticleIDs", "Masses"],
                         datatype_override = [SIGNED_INT_64, SIGNED_INT_64, SIGNED_INT_64, ""])

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
                           ["numpy", "pickle", "QuasarCode", "swiftsimio", "unyt"],
                           ["/storage/simulations/COLIBRE_ZOOMS/COLIBRE/five_spheres_20211006/volume04/l0/snapshots/snapshot_0007.hdf5"],
                           args_info,
                           kwargs_info)

    script.run(__main)
