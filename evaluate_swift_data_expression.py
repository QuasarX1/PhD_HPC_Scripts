AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "31/01/2023"
DESCRIPTION = "Run an expression against a swift snapshot file."

import os
import swiftsimio as sw
import sys

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from script_wrapper import ScriptWrapper
from swift_data_expression import parse_string

def __main(file, expression):
    data = sw.load(file)
    print(parse_string(expression, data))

if __name__ == "__main__":
    args_info = [["file", "SWIFT snapshot file.", None],
                 ["expression", "Valid expression (see swift_data_expression.py).", None]]
    kwargs_info = []
    
    script = ScriptWrapper("get_gas_crit_density.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["os", "script_wrapper.py (local file)", "swift_data_expression.py (local file)", "swiftsimio", "sys"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
