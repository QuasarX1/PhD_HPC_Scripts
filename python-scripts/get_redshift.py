AUTHOR = "Christopher Rowe"
VERSION = "2.0.0"
DATE = "06/07/2023"
DESCRIPTION = "Gets the redshift for the specified SWIFT snapshot."

import swiftsimio as sw

from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.calculations import get_redshift

def __main(file):
    print(get_redshift(sw.load(file)))

if __name__ == "__main__":
    args_info = [["file", "SWIFT snapshot file.", None]]
    kwargs_info = []
    
    script = ScriptWrapper("get_redshift.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["swiftsimio", "QuasarCode"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
