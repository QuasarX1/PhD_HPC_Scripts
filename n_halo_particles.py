AUTHOR = "Christopher Rowe"
VERSION = "1.0.2"
DATE = "27/03/2023"
DESCRIPTION = "Gets the number of each type of particle listed as being part of halos for the specified SWIFT parttypes file."

import h5py
import numpy as np
from QuasarCode.IO.Text.console import print_info
from QuasarCode.Tools import ScriptWrapper

__PARTTYPE_NAMES = ("Dark Matter",
                    "Gas        ",
                    "Stars      ",
                    "Black Holes")
__PARTTYPE_NUMBERS = (1, 0, 4, 5)

def __main(file):
    print_info("Number of each particle type:")
    data_file = h5py.File(file)
    data = np.array(data_file["Particle_types"], dtype = np.int64)
    data_file.close()
    for i in range(len(__PARTTYPE_NAMES)):
        print_info("{}:    {}".format(__PARTTYPE_NAMES[i], (data == __PARTTYPE_NUMBERS[i]).sum()))

if __name__ == "__main__":
    args_info = [["file", "VELOCIraptor catalogue parttypes file.", None]]
    kwargs_info = []
    
    script = ScriptWrapper("get_redshift.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["console_log_printing (local file)", "h5py", "os", "script_wrapper.py (local file)", "sys"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
