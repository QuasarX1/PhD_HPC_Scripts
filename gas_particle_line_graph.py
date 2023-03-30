AUTHOR = "Christopher Rowe"
VERSION = "1.3.1"
DATE = "27/03/2023"
DESCRIPTION = "Creates line graphs (with errors) for binned data from SWIFT gas particles."

from argparse import ArgumentError
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm, ListedColormap
from matplotlib.patches import Polygon
import numpy as np
import os
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
from QuasarCode.Tools import ScriptWrapper
from scipy.interpolate import Rbf
import swiftsimio as sw
import sys
from typing import List
from unyt import Mpc, unyt_array as u_arr

source_file_relitive_add_to_path(__file__)
from box_region import BoxRegion
from swift_data_expression import parse_string as make_attribute



def make_graph(particle_data_list, data_name_list, output_file_path, x_axis_field: List[float], x_axis_unit, y_axis_field: List[float], y_axis_unit, box_region = BoxRegion(), x_axis_name = None, y_axis_name = None, fraction_x_axis = False, log_x_axis = False, log_y_axis = False, y_axis_weight_field = "masses", min_y_field_value = None, max_y_field_value = None, keep_outliers = False, limit_fields: List[str] = None, limit_units: List[str] = None, limits_min: List[float] = None, limits_max: List[float] = None, show_errors = False):
    nBins = 40

    if not isinstance(x_axis_field, list):
        x_axis_field = [x_axis_field]
    if not isinstance(y_axis_field, list):
        y_axis_field = [y_axis_field]
    
    stylesheet_directory = __file__.rsplit(os.path.sep, 1)[0]
    normal_stylesheet = os.path.join(stylesheet_directory, "temp_diagram_stylesheet.mplstyle")
    plt.style.use(normal_stylesheet)
    
    fig = plt.figure()
    ax = fig.gca()

    cycle_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    n_colours = len(cycle_colors)
    line_data = []
    error_data = []
    for i, data in enumerate(particle_data_list):
        coords = np.array(data.gas.coordinates)
        box_region.complete_bounds_from_coords(coords)
        print_verbose_info(f"Final bounds: {box_region.x_min}-{box_region.x_min}, {box_region.y_min}-{box_region.y_max}, {box_region.z_min}-{box_region.z_max}")
        array_filter = box_region.make_array_filter(coords)

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
#                field_value = make_attribute(field, data.gas)[array_filter].to(limit_units[j])
                field_value = make_attribute(field, data.gas).to(limit_units[j])
                if limits_min is not None and limits_min[j] != "":
                    manual_filter &= field_value >= limits_min[j]
                if limits_max is not None and limits_max[j] != "":
                    manual_filter &= field_value <= limits_max[j]

        y_axis_filter = None
        print_verbose_info("Reading Y-axis data.")
        y_axis_data = make_attribute(y_axis_field[i] if len(y_axis_field) > 1 else y_axis_field[0], data.gas)[array_filter & manual_filter].to(y_axis_unit)
        if keep_outliers:
            if min_y_field_value is not None:
                y_axis_data[y_axis_data < min_y_field_value] = min_y_field_value
            if max_y_field_value is not None:
                y_axis_data[y_axis_data > max_y_field_value] = max_y_field_value
        else:
            y_axis_filter = (y_axis_data >= (min_y_field_value if min_y_field_value is not None else -np.Infinity)) & (y_axis_data <= (max_y_field_value if max_y_field_value is not None else np.Infinity))
            y_axis_data = y_axis_data[y_axis_filter]

        combined_data_filter = (array_filter & manual_filter)
        combined_data_filter[np.where(combined_data_filter)[0][y_axis_filter == False]] = False
        
        print_verbose_info("Reading in data.")
        x_axis_data = make_attribute(x_axis_field[i] if len(x_axis_field) > 1 else x_axis_field[0], data.gas)[combined_data_filter].to(x_axis_unit)
        if fraction_x_axis:
            x_axis_data = np.array(x_axis_data) / np.mean(np.array(x_axis_data))
        if log_x_axis:
            x_axis_data = np.log10(x_axis_data)
        y_axis_weights = make_attribute(y_axis_weight_field, data.gas)[combined_data_filter]
        
        hist, bin_edges = np.histogram(x_axis_data, bins = nBins, weights = y_axis_data * np.array(y_axis_weights))
        hist[hist != 0] /= np.histogram(x_axis_data, bins = nBins, weights = np.array(y_axis_weights))[0][hist != 0]
        bin_centres = (bin_edges[:len(bin_edges) - 1] + bin_edges[1:]) / 2
        bin_value_lists = [y_axis_data[(x_axis_data >= bin_edges[i]) & ((x_axis_data < bin_edges[i + 1]) if i + 1 < len(bin_edges) - 1 else (x_axis_data <= bin_edges[i + 1]))] for i in range(len(bin_edges) - 1)]
        errors = np.array([(np.std(data) if len(data) > 0 else 0) for data in bin_value_lists])

        line_data.append((bin_centres, hist))
        error_data.append(errors)

    # make the polygons for plotting (account for log of y-axis)
    data_lower_position_options = []
    min_error_options = []
    if show_errors:
        for i in range(len(line_data)):
            if log_y_axis:
                bound_errors = np.array([np.log10(line_data[i][1] - error_data[i]), np.log10(line_data[i][1] + error_data[i])])
            else: 
                bound_errors = np.array([line_data[i][1] - error_data[i], line_data[i][1] + error_data[i]])

            error_data[i] = bound_errors
            min_error_options.append(bound_errors[0][np.isnan(bound_errors[0]) == False].min())

            percentage_below_min = 10
            data_lower_position_options.append(np.log10(line_data[i][1].min()) - ((np.log10(line_data[i][1].max()) - np.log10(line_data[i][1].min())) / percentage_below_min))

        lower_error_cuttoff = min(min(data_lower_position_options), min(min_error_options))

    for i in range(len(line_data)):
        if show_errors:
#            ax.errorbar(x = bin_centres, y = hist, yerr = errors, ecolor = "orange", label = data_name_list[i])

            error_data[i][0][np.isnan(error_data[i][0])] = lower_error_cuttoff

            lower_error_points = np.array([[line_data[i][0][e], error_data[i][0][e]] for e in range(len(error_data[i][0]))])
            upper_error_points = np.array([[line_data[i][0][(-1 * e) - 1], error_data[i][1][(-1 * e) - 1]] for e in range(len(error_data[i][1]))])

            poly = np.concatenate((lower_error_points, upper_error_points), axis = 0)
            ax.add_patch(Polygon(poly, closed = False, color = cycle_colors[i % n_colours], alpha = 0.4))
#        else:
#            ax.plot(bin_centres, hist, label = data_name_list[i])

        y_data = line_data[i][1]
        if log_y_axis:
            y_data[y_data != 0] = np.log10(y_data[y_data != 0])
        ax.plot(line_data[i][0], y_data, label = data_name_list[i])

    if x_axis_name is None:
        ax.set_xlabel(("${\\rm log_{10}}$ " if log_x_axis and not fraction_x_axis else "") + f"{x_axis_field.title()} " + (("Ratio " + ("${\\rm log_{10}}$ " if log_x_axis else "") + "value/<value>") if fraction_x_axis else ""))
    else:
        ax.set_xlabel(("${\\rm log_{10}}$ " if log_x_axis else "") + f"{x_axis_name}" + (f"/<{x_axis_name}>" if fraction_x_axis else ""))

    ax.set_ylabel(("${\\rm log_{10}}$ " if log_y_axis else "") + (y_axis_field.title() if y_axis_name is None else y_axis_name))

    ax.legend()

    fig.savefig(output_file_path)

def __main(data_list, data_name_list, output_file, x_axis_field: List[float], x_axis_unit, y_axis_field: List[float], y_axis_unit, x_axis_name, y_axis_name, fraction_x_axis, log_x_axis, log_y_axis, y_axis_weight_field, min_y_field_value, max_y_field_value, keep_outliers, show_errors, limit_fields, limit_units, limits_min, limits_max, **kwargs):
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

    if limit_fields is not None: kwargs["limit_fields"] = limit_fields
    if limit_units is not None: kwargs["limit_units"] = limit_units
    if limits_min is not None: kwargs["limits_min"] = limits_min
    if limits_max is not None: kwargs["limits_max"] = limits_max

    make_graph(particle_data_list, data_name_list, output_file, x_axis_field, x_axis_unit, y_axis_field, y_axis_unit, box_region = box_region_object, fraction_x_axis = fraction_x_axis, log_x_axis = log_x_axis, log_y_axis = log_y_axis, keep_outliers = keep_outliers, show_errors = show_errors, **kwargs)

if __name__ == "__main__":
    args_info = [["data_list",      "Semicolon seperated list of filepaths to snapshot data files.",                                      ScriptWrapper.make_list_converter(";")],
                 ["data_name_list", "Semicolon seperated list of names - one for each file.",                                             ScriptWrapper.make_list_converter(";")],
                 ["output_file",    "Name (or relitive file path) to store the resulting image.",                                         None],
                 ["x_axis_field",   "Name (or expression with no spaces) of the data set containing data to be binned along the X-axis.\nCan be set to a ; seperated list, in the event that different normalisations are required for each dataset.", ScriptWrapper.make_list_converter(";")],
                 ["x_axis_unit",    "Unit expression for the X-axis data.",                                                               None],
                 ["y_axis_field",   "Name (or expression with no spaces) of the data set containing data to be averaged on the Y-axis.\nCan be set to a ; seperated list, in the event that different normalisations are required for each dataset.",  ScriptWrapper.make_list_converter(";")],
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
                   ["limit-fields",         None, "Names (or expressions with no spaces) as a semicolon seperated list of the data set to be used for filtering the list of particles. Only supports * and / operators, and permits int and float constants.",
                                                                                                    False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["limit-units",          None, "Unit expression for the limits specified. Uses a semicolon seperated list.",
                                                                                                    False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["limits-min",           None, "",
                                                                                                    False, False, ScriptWrapper.make_list_converter(";", float), None],
                   ["limits-max",           None, "",
                                                                                                    False, False, ScriptWrapper.make_list_converter(";", float), None],
                    *BoxRegion.get_command_params()
                  ]
    
    script = ScriptWrapper("gas_particle_line_graph.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["argparse", "BoxRegion.py  (local file)", "console_log_printing.py (local file)", "matplotlib", "numpy", "os", "scipy", "swift_data_expression.py (local file)", "swiftsimio", "script_wrapper.py (local file)", "sys", "typing", "unyt"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
    