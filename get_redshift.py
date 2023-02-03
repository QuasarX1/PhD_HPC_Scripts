AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "12/01/2023"
DESCRIPTION = "Gets the redshift for the specified SWIFT snapshot."

import os
import swiftsimio as sw
import sys

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from script_wrapper import ScriptWrapper

def __main(file):
    print(sw.load(file).metadata.z)

if __name__ == "__main__":
    args_info = [["file", "SWIFT snapshot file.", None]]
    kwargs_info = []
    
    script = ScriptWrapper("get_redshift.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["os", "script_wrapper.py (local file)", "swiftsimio", "sys"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
