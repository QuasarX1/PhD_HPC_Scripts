AUTHOR = "Christopher Rowe"
VERSION = "3.0.3"
DATE = "31/01/2023"
DESCRIPTION = "Creates a temprature vs. density diagram from SWIFT particle data."

from argparse import ArgumentError
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm, ListedColormap
import numpy as np
import os
from scipy.interpolate import Rbf
import swiftsimio as sw
import sys
from unyt import Mpc, unyt_quantity, unyt_array as u_arr

TOL_AVAILABLE = False
try:
    import tol_colors
    TOL_AVAILABLE = True
except: pass

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from box_region import BoxRegion
import console_log_printing as clp
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
from get_gas_crit_density import critical_gas_density
from script_wrapper import ScriptWrapper
from swift_data_expression import parse_string

def make_diagram(particle_data, output_file_path, colour_variable_name = "gas.masses", colour_unit = "Msun", colour_name = None, fraction_colour = False, fraction_mean_colour = False, log_colour = False, colour_weight = "gas.masses", contour_variable_name = None, contour_unit = None, box_region = BoxRegion(), min_colour_value = None, max_colour_value = None, keep_outliers = False, limit_fields: List[str] = None, limit_units: List[str] = None, limits_min: List[float] = None, limits_max: List[float] = None, colour_map = None):
    print_debug(f"make_diagram arguments: {particle_data} {output_file_path} {colour_variable_name} {contour_variable_name} {box_region.x_min} {box_region.x_max} {box_region.y_min} {box_region.y_max} {box_region.z_min} {box_region.z_max}")
    
    coords = np.array(particle_data.gas.coordinates)
    box_region.complete_bounds_from_coords(coords)
    print_verbose_info(f"Final bounds: {box_region.x_min}-{box_region.x_max}, {box_region.y_min}-{box_region.y_max}, {box_region.z_min}-{box_region.z_max}")
    array_filter = box_region.make_array_filter(coords)

    manual_filter = np.full_like(array_filter, True)
    if limit_fields is not None:
        for i, field in enumerate(limit_fields):
            field_value = parse_string(field, particle_data)[array_filter].to(limit_units[i])
            if limits_min is not None and limits_min[i] != "":
                manual_filter &= field_value >= limits_min[i]
            if limits_max is not None and limits_max[i] != "":
                manual_filter &= field_value <= limits_max[i]

    colour_weights = None
    colour_filter = None
    divide_agg_colour = fraction_colour or fraction_mean_colour
    colour_field_divisor_value = None
    if colour_variable_name is not None:
        colour_weights = parse_string(colour_variable_name, particle_data)[array_filter & manual_filter].to(colour_unit)

        if keep_outliers:
            if min_colour_value is not None:
                colour_weights[colour_weights < min_colour_value] = min_colour_value
            if max_colour_value is not None:
                colour_weights[colour_weights > max_colour_value] = max_colour_value
        else:
            colour_filter = (colour_weights >= (min_colour_value if min_colour_value is not None else -np.Infinity)) & (colour_weights <= (max_colour_value if max_colour_value is not None else np.Infinity))
            colour_weights = colour_weights[colour_filter]
    if colour_filter is None:
        colour_filter = np.full_like(colour_weights, True)

    if fraction_colour:
        colour_field_divisor_value = np.sum(colour_weights)
    elif fraction_mean_colour:
        colour_field_divisor_value = np.mean(colour_weights)

    combined_data_filter = (array_filter & manual_filter)
    combined_data_filter[colour_filter == False] = False

    contour_values = None
    if contour_variable_name is not None:
        print_verbose_info("Reading contour data.")
#        contour_values = parse_string(contour_variable_name, particle_data)[array_filter][manual_filter][colour_filter].to(contour_unit)
        contour_values = parse_string(contour_variable_name, particle_data)[combined_data_filter].to(contour_unit)

    print_verbose_info("Reading in data.")
#    x = parse_string("gas.densities", particle_data)[array_filter][manual_filter][colour_filter]
    x = parse_string("gas.densities", particle_data)[combined_data_filter]
    x = x / critical_gas_density(particle_data, x.units)
    #x = x / unyt_quantity.from_astropy(particle_data.metadata.cosmology.Ob(particle_data.metadata.z) * particle_data.metadata.cosmology.critical_density(particle_data.metadata.z)).to(x.units)
    #x = x / critical_gas_density(particle_data, x.units)
    #x = np.log10(x / np.mean(np.array(x)))
    #x = np.log10(np.array(x) / np.mean(np.array(x)))
    x = np.log10(np.array(x))
#    t = np.log10(particle_data.gas.temperatures[array_filter][manual_filter][colour_filter].to("K"))
    t = np.log10(particle_data.gas.temperatures[combined_data_filter].to("K"))
    if colour_variable_name is not None:
#        w = parse_string(colour_weight, particle_data)[array_filter][manual_filter][colour_filter]
        w = parse_string(colour_weight, particle_data)[combined_data_filter]

    print_verbose_info("Making plot.")
    stylesheet_directory = __file__.rsplit(os.path.sep, 1)[0]
    normal_stylesheet = os.path.join(stylesheet_directory, "temp_diagram_stylesheet.mplstyle")
    plt.style.use(normal_stylesheet)
    fig = plt.figure()
    ax = fig.gca()
    
    kwargs = {}
    if colour_variable_name is not None:
        def colour_reduction(indices):
            filtered_w = np.take(w, indices, 0)
            c = np.sum(np.take(colour_weights, indices, 0) * filtered_w) / np.sum(filtered_w)
            if divide_agg_colour: c = c / colour_field_divisor_value
            if log_colour: c = np.log10(c)
            return c
        kwargs["reduce_C_function"] = colour_reduction
        kwargs["C"] = np.linspace(0, colour_weights.shape[0] - 1, colour_weights.shape[0], dtype = int)

    throwaway_fig = plt.figure()
    throwaway_ax = throwaway_fig.gca()
    raw_hex_out = throwaway_ax.hexbin(x, t, gridsize = 500, **kwargs)
    colour_percentiles = np.percentile(np.array(raw_hex_out.get_array()), [5, 95])
    plt.close(throwaway_fig)

    # Handle colour map
    if colour_map is None:
        colour_map = [None]
    if not TOL_AVAILABLE and (len(colour_map) > 1 or colour_map[0] in ('sunset_discrete', 'sunset',
                                            'nightfall_discrete', 'nightfall',
                                            'BuRd_discrete', 'BuRd',
                                            'PRGn_discrete', 'PRGn',
                                            'YlOrBr_discrete', 'YlOrBr',
                                            'WhOrBr', 'iridescent',
                                            'rainbow_PuRd', 'rainbow_PuBr', 'rainbow_WhRd', 'rainbow_WhBr', 'rainbow_discrete')):
        print_warning(f"Paul Tol's colours are not avalible. This is likley required for colourmap: {colour_map} and this process may fail as a result!\nSee --help for instalation instructions.")

    hex_out = ax.hexbin(x, t, gridsize = 500, vmin = colour_percentiles[0], vmax = colour_percentiles[1], cmap = (tol_colors.tol_cmap(colour_map[0]) if len(colour_map) == 1 else tol_colors.LinearSegmentedColormap.from_list("custom-map", colour_map)) if TOL_AVAILABLE and colour_map[0] in tol_colors.tol_cmap() else colour_map[0], **kwargs)

    ax.set_xlabel("${\\rm log_{10}}$ $\\rho$/<$\\rho$>")
    ax.set_ylabel("${\\rm log_{10}}$ $T$ (${\\rm K}$)")
    
    if colour_variable_name is not None:
        print_verbose_info("Making colourbar.")
        colourbar = fig.colorbar(hex_out)
        
        if colour_name is None:
            colourbar_label = ("${\\rm log_{10}}$ " if log_colour and not divide_agg_colour else "") + colour_variable_name.replace("_", " ").title() + " " + (("Ratio " + ("${\\rm log_{10}}$ " if log_colour else "") + ("value/$\Sigma$(value)" if fraction_colour else "value/<value>") if fraction_mean_colour else ""))
        else:
            colourbar_label = ("${\\rm log_{10}}$ " if log_colour else "") + f"{colour_name}" + (f"/$\Sigma$({colour_name})" if fraction_colour else f"/<{colour_name}>" if fraction_mean_colour else "")
        
        if not divide_agg_colour:
            colourbar_label += ((" (${\\rm " + str(colour_weights[0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + "}$)") if str(colour_weights[0].units.expr) != "1" else (" (dimensionless)" if not log_colour else ""))

        #colourbar_label = (("" if not log_colour else "${\\rm log_{10}}$ ") + (colour_variable_name.replace("_", " ") if colour_name is None or colour_name == "" else colour_name)) + ((" (${\\rm " + str(colour_weights[0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + "}$)") if str(colour_weights[0].units.expr) != "1" else (" (dimensionless)" if not log_colour else ""))
        
        print_debug(f"Colourbar label: \"{colourbar_label}\"")
        colourbar.set_label(colourbar_label)

    if contour_variable_name is not None:
        nBins = 50
        h, xedges, yedges = np.histogram2d(x, t, nBins, weights = contour_values)
        total_contour_value = np.sum(contour_values)
        h /= total_contour_value
        check_values = h.reshape(((len(xedges) - 1) * (len(yedges) - 1),))
        percentiles = np.percentile(check_values[check_values != 0], [10, 25, 50, 75, 90])
        
        
        #h_n, _, _ = np.histogram2d(x, t, nBins)
        contours = ax.contour(xedges[:-1] + ((xedges[1] - xedges[0])/2),
                              yedges[:-1] + ((yedges[1] - yedges[0])/2),
                              h.T,
                              levels = percentiles,
                              colors = "k",
                              alpha = 0.5,
                              linewidths = 1,#0.7,
                              linestyles = ["solid", "dotted"])
        #non_density_percentiles = percentiles * total_contour_value
        #labels = ax.clabel(contours,
        #                   contours.levels,
        #                   inline = True,
        #                   fontsize = 6)

    print_verbose_info("Saving to file.")
    fig.savefig(output_file_path)
    print_verbose_info("File saved.")

    

#TODO: implement better filter params
def __main(data, output_file, colour, colour_unit, colour_name, fraction_colour, fraction_mean_colour, log_colour, colour_weight,
           contour, contour_unit, colour_min, colour_max, keep_outliers, limit_fields, limit_units, limits_min, limits_max, colour_map, **kwargs):
    box_region_object = BoxRegion(**BoxRegion.filter_command_params(**kwargs))

    print_debug("Paramiters:\ndata: {}\noutput_file: {}\ncolour: {}\ncolour_unit: {}\ncolour_name: {}\nfraction_colour: {}\nfraction_mean_colour: {}\nlog_colour: {}\ncolour_weight: {}\ncontour: {}\ncontour_unit: {}\ncentre_x_position: {}\ncentre_y_position: {}\ncentre_z_position: {}\nside_length: {}\nx_min: {}\nx_max: {}\ny_min: {}\ny_max: {}\nz_min: {}\nz_max: {}\ncolour_min: {}\ncolour_max: {}\nkeep_outliers: {}".format(
         data, output_file, colour, colour_unit, colour_name, fraction_colour, fraction_mean_colour, log_colour, colour_weight,
         contour, contour_unit, *box_region_object.centre, box_region_object.side_length,
         box_region_object.x_min, box_region_object.x_max, box_region_object.y_min, box_region_object.y_max, box_region_object.z_min, box_region_object.z_max, colour_min, colour_max, keep_outliers))
    
    print_verbose_info(f"Loading data file ({data}).")
    if data is None:
        raise ArgumentError(None, "No data is provided. Data must be the first argument (other than the '-h' flag).")
    particle_data = sw.load(data)

    kwargs = {}

    if colour is not None: kwargs["colour_variable_name"] = colour
    if colour_unit is not None: kwargs["colour_unit"] = colour_unit
    if colour_name is not None: kwargs["colour_name"] = colour_name
    if fraction_colour is not None: kwargs["fraction_colour"] = fraction_colour
    if fraction_mean_colour is not None: kwargs["fraction_mean_colour"] = fraction_mean_colour
    if log_colour is not None: kwargs["log_colour"] = log_colour
    if colour_weight is not None: kwargs["colour_weight"] = colour_weight

    if contour is not None: kwargs["contour_variable_name"] = contour
    if contour_unit is not None: kwargs["contour_unit"] = contour_unit
    
    if colour_min is not None: kwargs["min_colour_value"] = colour_min
    if colour_max is not None: kwargs["max_colour_value"] = colour_max
    kwargs["keep_outliers"] = keep_outliers

    if limit_fields is not None: kwargs["limit_fields"] = limit_fields
    if limit_units is not None: kwargs["limit_units"] = limit_units
    if limits_min is not None: kwargs["limits_min"] = limits_min
    if limits_max is not None: kwargs["limits_max"] = limits_max

    if colour_map is not None: kwargs["colour_map"] = colour_map

    make_diagram(particle_data, output_file, box_region = box_region_object, **kwargs)

if __name__ == "__main__":
    args_info = [["data", "Path to the SWIFT data file.", None]]
    #               name                    char. desc.                             requ.  flag   conv. def.  mutually exclusive flags
    kwargs_info = [["output_file",          "o",  "Name (or relitive file path) to store\nthe resulting image.",
                                                                                    True,  False, None, None],
                   ["colour",               "c",  "Name (or expression with no spaces) of\nthe data set containing data to be\nused for colouring. Only supports *\nand / operators, and permits int and\nfloat constants.\nDefault is \"gas.masses\".",
                                                                                    False, False, None, "gas.masses"],
                   ["colour-unit",          "u",  "Unit expression for the colour data.\nDefault is \"Msun\".",
                                                                                    False, False, None, "Msun"],
                   ["colour-name",          None, "Unit expression for the colour data.\nDefault is \"Msun\".",
                                                                                    False, False, None, None],
                   ["fraction-colour",      None,  "Make the pixel colour the fraction of the total value of the (un-logged) dataset.",
                                                                                    False, True,  None,  None],
                   ["fraction-mean-colour", None,  "Make the pixel colour the fraction of the mean value of the (un-logged) dataset.",
                                                                                    False, True,  None,  None],
                   ["log-colour",           None, "Apply a base 10 log to the colour data.",
                                                                                    False, True,  None, None],
                   ["colour-weight",        None, "Name (or expression with no spaces) of\n the data set containing data to be\nused for weighting colour data. Only\n supports * and / operators, and\n permits int and float constants.\n Default is \"gas.masses\".",
                                                                                    False, False, None, "gas.masses"],
                   ["contour",              "l",  "Optionally draw contours for a specified\nvariable. See \"--colour\" for rules.",
                                                                                    False, False, None, None],
                   ["contour-unit",         None, "Unit expression for the contour data.",
                                                                                    False, False, None, None],
                    *BoxRegion.get_command_params(),
                   ["colour-min",           None, "Minimum value for the colour field data.\Particles with lower values will be\nignored by default or will be set to\nthis value if the \"--keep-outliers\"\nflag is specified.",
                                                                                    False, False, float, None],
                   ["colour-max",           None, "Maximum value for the colour field data.\Particles with higher values will be\nignored by default or will be set to\nthis value if the \"--keep-outliers\"\nflag is specified.",
                                                                                    False, False, float, None],
                   ["keep-outliers",        None, "Force points outside the colour range\nspecified to either the upper or lower\nbound (whichever appropriate).",
                                                                                    False, True,  None,  None],

                   ["limit-fields",         None, "Names (or expressions with no spaces) as a semicolon seperated list of the data set to be used for filtering the list of particles. Only supports * and / operators, and permits int and float constants.",
                                                                                    False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["limit-units",          None, "Unit expression for the limits specified. Uses a semicolon seperated list.",
                                                                                    False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["limits-min",           None, "",
                                                                                    False, False, ScriptWrapper.make_list_converter(";", float), None],
                   ["limits-max",           None, "",
                                                                                    False, False, ScriptWrapper.make_list_converter(";", float), None],
                   ["colour-map",           None, "Name of the colour map to use. Supports the avalible matplotlib colourmaps" + (", as well as those designed by Paul Tol (https://personal.sron.nl/~pault/).\nTo use a custom map, specify the colours in the format \"#RRGGBB\" as a semicolon seperated list (must have at least 2 values)." if TOL_AVAILABLE else ".\nTo add support for Paul Tol's colours, download the python file from https://personal.sron.nl/~pault/ and install using \"add-py tol_colors\".") + "\nDefaults to whatever is set by the stylesheet - usually \"viridis\".",
                                                                                    False, False, str, None]
                  ]
    
    script = ScriptWrapper("temp_density_diagram.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["argparse", "BoxRegion.py  (local file)", "console_log_printing.py (local file)", "get_gas_crit_density.py (local file)", "matplotlib", "numpy", "os", "scipy", "swift_data_expression.py (local file)", "swiftsimio", "script_wrapper.py (local file)", "sys", "unyt"],
                           ["--pressure --data ~/datafile.hdf5 -o result.png", "--density --data ~/datafile.hdf5 -o result.png --node gas --colour mean_metal_weighted_redshifts", "--pressure --data ~/datafile.hdf5 -o result.png -x 5 -y 253 -w 20", "--density --data ~/datafile.hdf5 -o result.png --z-min 10 --z-max 20"],
                           args_info,
                           kwargs_info)

    script.run(__main)
    