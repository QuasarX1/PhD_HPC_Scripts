AUTHOR = "Christopher Rowe"
VERSION = "2.0.0"
DATE = "06/07/2023"
DESCRIPTION = "Gets the number of each type of particle listed as being part of halos for the specified SWIFT parttypes file."

import numpy as np
import os

from QuasarCode import source_file_relitive_add_to_path, Console
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.io import Multifile_VR_Catalogue

__PARTTYPE_NAMES = ("Dark Matter",
                    "Gas        ",
                    "Stars      ",
                    "Black Holes")
__PARTTYPE_NUMBERS = (1, 0, 4, 5)

def __main(file):
    folder_and_file = file.rsplit(os.path.sep, maxsplit = 1)
    catalogue = Multifile_VR_Catalogue(folder_and_file[0] if len(folder_and_file) > 1 else ".", folder_and_file[-1].split(".", maxsplit = 1)[0])

    bound_parttype_ids = catalogue.read_raw_file_data("catalog_parttypes", lambda file: np.array(file["Particle_types"], dtype = np.int16))
    unboundparttype_ids = catalogue.read_raw_file_data("catalog_parttypes.unbound", lambda file: np.array(file["Particle_types"], dtype = np.int16))

    n_bound = []
    n_unbound = []
    n_all = []
    for i in range(len(__PARTTYPE_NAMES)):
        n_bound.append((bound_parttype_ids == __PARTTYPE_NUMBERS[i]).sum())
        n_unbound.append((unboundparttype_ids == __PARTTYPE_NUMBERS[i]).sum())
        n_all.append(n_bound[-1] + n_unbound[-1])

    max_bound_string_len = max([len(str(v)) for v in n_bound])
    max_unbound_string_len = max([len(str(v)) for v in n_unbound])
    max_all_string_len = max([len(str(v)) for v in n_all])

    Console.print_info("Number of each particle type:")
    
    for i in range(len(__PARTTYPE_NAMES)):
        padding_all = " " * (max_all_string_len - len(str(n_all[i])))
        padding_bound = " " * (max_bound_string_len - len(str(n_bound[i])))
        padding_unbound = " " * (max_unbound_string_len - len(str(n_unbound[i])))
        Console.print_info("{}:    {}{} total ({}{} bound, {}{} unbound)".format(__PARTTYPE_NAMES[i], padding_all, n_all[i], padding_bound, n_bound[i], padding_unbound, n_unbound[i]))

if __name__ == "__main__":
    args_info = [["file", "VELOCIraptor catalogue parttypes file.", None]]
    kwargs_info = []
    
    script = ScriptWrapper("get_redshift.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["numpy", "os", "QuasarCode"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
