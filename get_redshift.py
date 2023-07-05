AUTHOR = "Christopher Rowe"
VERSION = "1.0.1"
DATE = "27/03/2023"
DESCRIPTION = "Gets the redshift for the specified SWIFT snapshot."

from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from .contra.calculations import get_redshift

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
                           ["os", "script_wrapper.py (local file)", "swiftsimio", "sys"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
