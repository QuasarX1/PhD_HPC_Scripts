AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "28/03/2023"
DESCRIPTION = "Creates a histogram for the desnities of gas particles from a SWIFT snapshot."

from matplotlib import pyplot as plt
import numpy as np
from QuasarCode.Tools import DirectoryTools
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from typing import List

DirectoryTools.source_file_relitive_add_to_path(__file__)
from box_region import BoxRegion
from get_gas_crit_density import critical_gas_density
from swift_data_expression import parse_string as make_attribute

def __main(data, output_file, log_y_axis: bool, limit_fields: List[str], limit_units: List[str], limits_min: List[float], limits_max: List[float], **kwargs):
    nBins = 40

    box_region_object = BoxRegion(**kwargs)

    snap_data = sw.load(data)
    positions = snap_data.gas.coordinates.to("Mpc")

    box_region_object.complete_bounds_from_coords(positions)
    array_filter = box_region_object.make_array_filter(positions)

    manual_filter = np.full_like(array_filter, True)
    if limit_fields is not None:
        if isinstance(limit_fields, str):
            limit_fields = [limit_fields]
            limit_units = [limit_units]
            if limits_min is not None:
                limits_min = [limits_min]
            if limits_max is not None:
                limits_max = [limits_max]

        for j, field in enumerate(limit_fields):
            field_value = make_attribute(field, data.gas).to(limit_units[j])
            if limits_min is not None and limits_min[j] != "":
                manual_filter &= field_value >= limits_min[j]
            if limits_max is not None and limits_max[j] != "":
                manual_filter &= field_value <= limits_max[j]

    combined_data_filter = (array_filter & manual_filter)

    density_data = np.log10(snap_data.gas.densities.to("Msun/Mpc**3")[combined_data_filter] / critical_gas_density(snap_data, unit = "Msun/Mpc**3"))

    #stylesheet_directory = DirectoryTools.get_source_file_directory(__file__)
    #normal_stylesheet = os.path.join(stylesheet_directory, "temp_diagram_stylesheet.mplstyle")
    #plt.style.use(normal_stylesheet)
    
    plt.hist(density_data, bins = nBins, log = log_y_axis)
    plt.xlabel("$\\rm log_{10}$ $\\rho$/<$\\rho$>")
    #plt.ylabel("$\\rm log_{10}$ Frequency" if log_y_axis else "Frequency")
    plt.ylabel("Frequency")
    plt.savefig(output_file)

if __name__ == "__main__":
    args_info = [["data",        "File name/path of the source SWIFT snapshot.",               None],
                 ["output_file", "Name (or relitive file path) to store the resulting image.", None]]
    #               name            char. desc.                                          requ.  flag   conv.  def.  mutually exclusive flags
    kwargs_info = [["log-y-axis",   None, "Should the Y-axis be displayed using log10?", False, True,  None,  None],
                   ["limit-fields", None, "Names (or expressions with no spaces) as a semicolon seperated list of the data set to be used for filtering the list of particles. Only supports * and / operators, and permits int and float constants.",
                                                                                         False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["limit-units",  None, "Unit expression for the limits specified. Uses a semicolon seperated list.",
                                                                                         False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["limits-min",   None, "",
                                                                                         False, False, ScriptWrapper.make_list_converter(";", float), None],
                   ["limits-max",   None, "",
                                                                                         False, False, ScriptWrapper.make_list_converter(";", float), None],
                    *BoxRegion.get_command_params()
                  ]
    
    script = ScriptWrapper("density_histogram.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["BoxRegion.py  (local file)", "matplotlib", "numpy", "os", "QuasarCode", "swift_data_expression.py (local file)", "swiftsimio", "typing"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
    