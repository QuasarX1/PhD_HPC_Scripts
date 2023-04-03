AUTHOR = "Christopher Rowe"
VERSION = "3.0.0"
DATE = "03/04/2023"
DESCRIPTION = "Run an expression against a swift snapshot file."

import numpy as np
from QuasarCode import console, source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw

source_file_relitive_add_to_path(__file__)
from swift_data_expression import parse_string

def __main(file: str, expression: str, print_attrs: bool, print_range_stats: bool, unit: str = None):
    data = sw.load(file)
    result = parse_string(expression, data) if expression != "" else data
    if unit is not None:
        try:
            result = result.to(unit)
        except:
            console.print_warning(f"Unable to convert this expression to unit {unit}.")
    print(result)
    if print_attrs:
        console.print_info(dir(result))
    if print_range_stats:
        console.print_info(f"Minimum: {result[:].min()}\nMaximum: {result[:].max()}\nMean:    {result[:].mean()}\nMedian:  {np.median(result[:])}")

if __name__ == "__main__":
    args_info = [["file", "SWIFT snapshot file.", None],
                 ["expression", "Valid expression (see swift_data_expression.py).", None]]
    kwargs_info = [["unit", "u", "Optionally, convert the dataset to a given unit.", False, False, None, None],
                   ["print-attrs", "l", "Display the object members.", False, True, None, None],
                   ["print-range-stats", "r", "Display the min, max, mean and median.", False, True, None, None]]
    
    script = ScriptWrapper("get_gas_crit_density.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["numpy", "QuasarCode", "swift_data_expression.py (local file)", "swiftsimio"],
                           ["/path/to/data.hdf5 \"\" -l", "/path/to/data.hdf5 metadata.boxsize"],
                           args_info,
                           kwargs_info)

    script.run(__main)
