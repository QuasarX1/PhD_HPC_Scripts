AUTHOR = "Christopher Rowe"
VERSION = "2.0.1"
DATE = "27/03/2023"
DESCRIPTION = "Run an expression against a swift snapshot file."

from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw

source_file_relitive_add_to_path(__file__)
from swift_data_expression import parse_string

def __main(file: str, expression: str, print_attrs: bool):
    data = sw.load(file)
    result = parse_string(expression, data) if expression != "" else data
    print(result)
    if print_attrs:
        print(dir(result))

if __name__ == "__main__":
    args_info = [["file", "SWIFT snapshot file.", None],
                 ["expression", "Valid expression (see swift_data_expression.py).", None]]
    kwargs_info = [["print-attrs", "l", "Display the object members.", False, True, None, None]]
    
    script = ScriptWrapper("get_gas_crit_density.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["os", "script_wrapper.py (local file)", "swift_data_expression.py (local file)", "swiftsimio", "sys"],
                           ["/path/to/data.hdf5 \"\" -l", "/path/to/data.hdf5 metadata.boxsize"],
                           args_info,
                           kwargs_info)

    script.run(__main)
