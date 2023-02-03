AUTHOR = "Christopher Rowe"
VERSION = "1.1.1"
DATE = "16/01/2023"
DESCRIPTION = "Creates line graphs (with errors) for binned data from SWIFT gas particles."

from argparse import ArgumentError
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm, ListedColormap
from matplotlib.patches import Polygon
import numpy as np
import os
from scipy.interpolate import Rbf
import swiftsimio as sw
import sys
from unyt import Mpc, unyt_array as u_arr

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from box_region import BoxRegion
import console_log_printing as clp
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
from script_wrapper import ScriptWrapper
from swift_data_expression import parse_string as make_attribute



def make_graph(particle_data_list, data_name_list, output_file_path, x_axis_field, x_axis_unit, y_axis_field, y_axis_unit, box_region = BoxRegion(), x_axis_name = None, y_axis_name = None, fraction_x_axis = False, log_x_axis = False, log_y_axis = False, y_axis_weight_field = "masses", min_y_field_value = None, max_y_field_value = None, keep_outliers = False, show_errors = False):
    nBins = 40
    
    stylesheet_directory = __file__.rsplit(os.path.sep, 1)[0]
    normal_stylesheet = os.path.join(stylesheet_directory, "temp_diagram_stylesheet.mplstyle")
    plt.style.use(normal_stylesheet)
    
    fig = plt.figure()
    ax = fig.gca()

    cycle_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    n_colours = len(cycle_colors)
    for i, data in enumerate(particle_data_list):
        coords = np.array(data.gas.coordinates)
        box_region.complete_bounds_from_coords(coords)
        print_verbose_info(f"Final bounds: {box_region.x_min}-{box_region.x_min}, {box_region.y_min}-{box_region.y_max}, {box_region.z_min}-{box_region.z_max}")
        array_filter = box_region.make_array_filter(coords)

        y_axis_filter = None
        print_verbose_info("Reading Y-axis data.")
        y_axis_data = make_attribute(y_axis_field, data.gas)[array_filter].to(y_axis_unit)
        if keep_outliers:
            if min_y_field_value is not None:
                y_axis_data[y_axis_data < min_y_field_value] = min_y_field_value
            if max_y_field_value is not None:
                y_axis_data[y_axis_data > max_y_field_value] = max_y_field_value
        else:
            y_axis_filter = (y_axis_data >= (min_y_field_value if min_y_field_value is not None else -np.Infinity)) & (y_axis_data <= (max_y_field_value if max_y_field_value is not None else np.Infinity))
            y_axis_data = y_axis_data[y_axis_filter]
        
        print_verbose_info("Reading in data.")
        x_axis_data = make_attribute(x_axis_field, data.gas)[array_filter][y_axis_filter].to(x_axis_unit)
        if fraction_x_axis:
            x_axis_data = np.array(x_axis_data) / np.mean(np.array(x_axis_data))
        if log_x_axis:
            x_axis_data = np.log10(x_axis_data)
        y_axis_weights = make_attribute(y_axis_weight_field, data.gas)[array_filter][y_axis_filter]
        
        hist, bin_edges = np.histogram(x_axis_data, bins = nBins, weights = y_axis_data * np.array(y_axis_weights))
        hist[hist != 0] /= np.histogram(x_axis_data, bins = nBins, weights = np.array(y_axis_weights))[0][hist != 0]
        bin_centres = (bin_edges[:len(bin_edges) - 1] + bin_edges[1:]) / 2
        bin_value_lists = [y_axis_data[(x_axis_data >= bin_edges[i]) & ((x_axis_data < bin_edges[i + 1]) if i + 1 < len(bin_edges) - 1 else (x_axis_data <= bin_edges[i + 1]))] for i in range(len(bin_edges) - 1)]
        errors = np.array([(np.std(data) if len(data) > 0 else 0) for data in bin_value_lists])

        if log_y_axis:
            errors = np.array([np.log10(hist - errors), np.log10(hist + errors)])

            lower_error_points = np.array([[bin_centres[i], errors[0][i]] for i in range(len(errors[0]))])
            upper_error_points = np.array([[bin_centres[(-1 * i) - 1], errors[1][(-1 * i) - 1]] for i in range(len(errors[1]))])
            poly = np.concatenate((lower_error_points, upper_error_points), axis = 0)

            hist[hist != 0] = np.log10(hist[hist != 0])
            errors[0] = hist - errors[0]
            errors[1] = errors[1] - hist
            
        if show_errors:
        #    ax.errorbar(x = bin_centres, y = hist, yerr = errors, ecolor = "orange", label = data_name_list[i])
            ax.add_patch(Polygon(poly, closed = False, color = cycle_colors[i % n_colours], alpha = 0.4))
        #else:
        #    ax.plot(bin_centres, hist, label = data_name_list[i])
        ax.plot(bin_centres, hist, label = data_name_list[i])

    if x_axis_name is None:
        ax.set_xlabel(("${\\rm log_{10}}$ " if log_x_axis and not fraction_x_axis else "") + f"{x_axis_field.title()} " + (("Ratio " + ("${\\rm log_{10}}$ " if log_x_axis else "") + "value/<value>") if fraction_x_axis else ""))
    else:
        ax.set_xlabel(("${\\rm log_{10}}$ " if log_x_axis else "") + f"{x_axis_name}" + (f"/<{x_axis_name}>" if fraction_x_axis else ""))

    ax.set_ylabel(("${\\rm log_{10}}$ " if log_y_axis else "") + (y_axis_field.title() if y_axis_name is None else y_axis_name))

    ax.legend()

    fig.savefig(output_file_path)

def __main(data_list, data_name_list, output_file, x_axis_field, x_axis_unit, y_axis_field, y_axis_unit, x_axis_name, y_axis_name, fraction_x_axis, log_x_axis, log_y_axis, y_axis_weight_field, min_y_field_value, max_y_field_value, keep_outliers, show_errors, **kwargs):
    box_region_object = BoxRegion(**kwargs)
    
    print_verbose_info(f"Loading data files ({data_list}).")
    if data_list is None or (isinstance(data_list, list) and len(data_list) == 0):
        raise ArgumentError(None, "No data is provided. Data must be the first argument (other than the '-h' flag).")
    particle_data_list = [sw.load(data) for data in data_list]

    kwargs = {}
    if x_axis_name is not None: kwargs["x_axis_name"] = x_axis_name
    if y_axis_name is not None: kwargs["y_axis_name"] = y_axis_name
    if y_axis_weight_field is not None: kwargs["y_axis_weight_field"] = y_axis_weight_field
    if min_y_field_value is not None: kwargs["min_y_field_value"] = min_y_field_value
    if max_y_field_value is not None: kwargs["max_y_field_value"] = max_y_field_value

    make_graph(particle_data_list, data_name_list, output_file, x_axis_field, x_axis_unit, y_axis_field, y_axis_unit, box_region = box_region_object, fraction_x_axis = fraction_x_axis, log_x_axis = log_x_axis, log_y_axis = log_y_axis, keep_outliers = keep_outliers, show_errors = show_errors, **kwargs)

if __name__ == "__main__":
    args_info = [["data_list",      "Semicolon seperated list of filepaths to snapshot data files.",                                      ScriptWrapper.make_list_converter(";")],
                 ["data_name_list", "Semicolon seperated list of names - one for each file.",                                             ScriptWrapper.make_list_converter(";")],
                 ["output_file",    "Name (or relitive file path) to store the resulting image.",                                         None],
                 ["x_axis_field",   "Name (or expression with no spaces) of the data set containing data to be binned along the X-axis.", None],
                 ["x_axis_unit",    "Unit expression for the X-axis data.",                                                               None],
                 ["y_axis_field",   "Name (or expression with no spaces) of the data set containing data to be averaged on the Y-axis.",  None],
                 ["y_axis_unit",    "Unit expression for the Y-axis data.",                                                               None]]
    #               name                   char. desc.                                              requ.  flag   conv.  def.  mutually exclusive flags
    kwargs_info = [["x-axis-name",         None, "Prety printing name to use on the X-axis.",       False, False, None,  None],
                   ["y-axis-name",         None, "Prety printing name to use on the Y-axis.",       False, False, None,  None],
                   ["fraction-x-axis",     "f",  "Make the X-axis the fraction of the mean value.", False, True,  None,  None],
                   ["log-x-axis",          None, "Should the X-axis be displayed using log10?",     False, True,  None,  None],
                   ["log-y-axis",          None, "Should the Y-axis be displayed using log10?",     False, True,  None,  None],
                   ["y-axis-weight-field", "k",  "Name (or expression with no spaces) of the data set containing data to be used for weighting the Y-axis data. Default is \"masses\".",
                                                                                                    False, False, None, "masses"],
                   ["min-y-field-value",   None, "Minimum value for the Y-axis data. Points with lower values will be ignored by default or will be set to this value if the \"--keep-outliers\" flag is specified.",
                                                                                                    False, False, float, None],
                   ["max-y-field-value",   None, "maximum value for the Y-axis data. Points with higher values will be ignored by default or will be set to this value if the \"--keep-outliers\" flag is specified.",
                                                                                                    False, False, float, None],
                   ["keep-outliers",       None, "Force points outside the Y-axis field range specified to either the upper or lower bound (whichever appropriate).",
                                                                                                    False, True,  None,  None],
                   ["show-errors",         "e",   "Display the standard deviation of the data in the Y-axis using error bars.",
                                                                                                    False, True,  None,  None],
                    *BoxRegion.get_command_params()
                  ]
    
    script = ScriptWrapper("gas_particle_line_graph.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["argparse", "BoxRegion.py  (local file)", "console_log_printing.py (local file)", "matplotlib", "numpy", "os", "scipy", "swift_data_expression.py (local file)", "swiftsimio", "script_wrapper.py (local file)", "sys", "unyt"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
    