AUTHOR = "Christopher Rowe"
VERSION = "4.0.0"
DATE = "07/07/2023"
DESCRIPTION = "Creates a temprature vs. density diagram from SWIFT particle data."

from argparse import ArgumentError
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm, ListedColormap
import numpy as np
import os
import swiftsimio as sw
from typing import List, Union

TOL_AVAILABLE = False
try:
    import tol_colors
    TOL_AVAILABLE = True
except: pass

from QuasarCode import Console, source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.filters import BoxRegion, ParticleFilter
from contra.io import parse_swift_string as parse_string, PartType
from contra.calculations import get_critical_gas_density as critical_gas_density
from contra.tools import format_unit_string

def make_diagram(particle_data, output_file_path, colour_variable_name = "gas.masses", colour_unit = "Msun", colour_name = None, fraction_colour = False, fraction_mean_colour = False, log_colour = False, colour_weight = "gas.masses", contour_variable_name = None, contour_unit = None, box_region = BoxRegion(), min_colour_value = None, max_colour_value = None, keep_outliers = False, limit_fields: Union[None, str, List[str]] = None, limit_units: Union[None, str, List[str]] = None, limits_min: Union[None, float, List[float]] = None, limits_max: Union[None, float, List[float]] = None, exclude_limits_from_contour: bool = False, colour_map = None):
    Console.print_debug(f"make_diagram arguments: {particle_data} {output_file_path} {colour_variable_name} {contour_variable_name} {box_region.x_min} {box_region.x_max} {box_region.y_min} {box_region.y_max} {box_region.z_min} {box_region.z_max} {min_colour_value} {max_colour_value} {keep_outliers} {limit_fields} {limit_units} {limits_min} {limits_max} {colour_map}")
    
    coords = np.array(particle_data.gas.coordinates)
    box_region.complete_bounds_from_coords(coords)
    Console.print_verbose_info(f"Final bounds: {box_region.x_min}-{box_region.x_max}, {box_region.y_min}-{box_region.y_max}, {box_region.z_min}-{box_region.z_max}")
    spatial_filter = box_region.make_array_filter(coords)

    particle_filter = ParticleFilter(particle_data, limit_fields, limit_units, limits_min, limits_max) if ParticleFilter.check_limits_present(limit_fields) else ParticleFilter.passthrough_filter(particle_data, PartType.gas)
    particle_filter.update(spatial_filter)

    colour_weights = None
    colour_filter = None
    divide_agg_colour = fraction_colour or fraction_mean_colour
    colour_field_divisor_value = None
    if colour_variable_name is not None:
        colour_weights = parse_string(colour_variable_name, particle_data)[particle_filter.numpy_filter].to(colour_unit)

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

    particle_filter.update(colour_filter)

    Console.print_verbose_info(f"{len(particle_filter.numpy_filter)} particles selected.")
    Console.print_debug(particle_filter.numpy_filter.sum())#TODO: WHY IS THIS WRONG?!?!?!
    if len(particle_filter.numpy_filter) == 0:
        raise ValueError("No data left after applying filter(s)!")

    contour_values = None
    if contour_variable_name is not None:
        Console.print_verbose_info("Reading contour data.")
        if exclude_limits_from_contour:
            contour_values = parse_string(contour_variable_name, particle_data)[spatial_filter].to(contour_unit)
            x_no_manual_filters = parse_string("gas.densities", particle_data)[spatial_filter]
            x_no_manual_filters = x_no_manual_filters / critical_gas_density(particle_data, x_no_manual_filters.units)
            x_no_manual_filters = np.log10(np.array(x_no_manual_filters))
            t_no_manual_filters = np.log10(particle_data.gas.temperatures[spatial_filter].to("K"))
        else:
            contour_values = parse_string(contour_variable_name, particle_data)[particle_filter.numpy_filter].to(contour_unit)

    Console.print_verbose_info("Reading in data.")
    x = parse_string("gas.densities", particle_data)[particle_filter.numpy_filter]
    x = x / critical_gas_density(particle_data, x.units)
    #x = x / unyt_quantity.from_astropy(particle_data.metadata.cosmology.Ob(particle_data.metadata.z) * particle_data.metadata.cosmology.critical_density(particle_data.metadata.z)).to(x.units)
    #x = x / critical_gas_density(particle_data, x.units)
    #x = np.log10(x / np.mean(np.array(x)))
    #x = np.log10(np.array(x) / np.mean(np.array(x)))
    x = np.log10(np.array(x))
    t = np.log10(particle_data.gas.temperatures[particle_filter.numpy_filter].to("K"))
    if colour_variable_name is not None:
        w = parse_string(colour_weight, particle_data)[particle_filter.numpy_filter]

    Console.print_verbose_info("Making plot.")
    stylesheet_directory = os.path.join(__file__.rsplit(os.path.sep, 1)[0], "..", "stylesheets")
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
    Console.print_debug(x)
    Console.print_debug(t)
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
        Console.print_warning(f"Paul Tol's colours are not avalible. This is likley required for colourmap: {colour_map} and this process may fail as a result!\nSee --help for instalation instructions.")

    hex_out = ax.hexbin(x, t, gridsize = 500, vmin = colour_percentiles[0], vmax = colour_percentiles[1], cmap = (tol_colors.tol_cmap(colour_map[0]) if len(colour_map) == 1 else tol_colors.LinearSegmentedColormap.from_list("custom-map", colour_map)) if TOL_AVAILABLE and (len(colour_map) > 1 or colour_map[0] in tol_colors.tol_cmap()) else colour_map[0], **kwargs)

    ax.set_xlabel("${\\rm log_{10}}$ $\\rho$/<$\\rho$>")
    ax.set_ylabel("${\\rm log_{10}}$ $T$ (${\\rm K}$)")
    
    if colour_variable_name is not None:
        Console.print_verbose_info("Making colourbar.")
        colourbar = fig.colorbar(hex_out)
        
        if colour_name is None:
            colourbar_label = ("${\\rm log_{10}}$ " if log_colour and not divide_agg_colour else "") + colour_variable_name.replace("_", " ").title() + " " + (("Ratio " + ("${\\rm log_{10}}$ " if log_colour else "") + ("value/$\Sigma$(value)" if fraction_colour else "value/<value>") if fraction_mean_colour else ""))
        else:
            colourbar_label = ("${\\rm log_{10}}$ " if log_colour else "") + f"{colour_name}" + (f"/$\Sigma$({colour_name})" if fraction_colour else f"/<{colour_name}>" if fraction_mean_colour else "")
        
        if not divide_agg_colour:
#            colourbar_label += ((" (${\\rm " + str(colour_weights[0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + "}$)") if str(colour_weights[0].units.expr) != "1" else (" (dimensionless)" if not log_colour else ""))
            colourbar_label += ((" (${\\rm " + format_unit_string(str(colour_weights[0].units.expr)).replace("**", "^").replace("sun", "_{\odot}") + "}$)") if str(colour_weights[0].units.expr) != "1" else (" (dimensionless)" if not log_colour else ""))

        #colourbar_label = (("" if not log_colour else "${\\rm log_{10}}$ ") + (colour_variable_name.replace("_", " ") if colour_name is None or colour_name == "" else colour_name)) + ((" (${\\rm " + str(colour_weights[0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + "}$)") if str(colour_weights[0].units.expr) != "1" else (" (dimensionless)" if not log_colour else ""))
        
        Console.print_debug(f"Colourbar label: \"{colourbar_label}\"")
        colourbar.set_label(colourbar_label)

    if contour_variable_name is not None:
        nBins = 50
        if exclude_limits_from_contour:
            h, xedges, yedges = np.histogram2d(x_no_manual_filters, t_no_manual_filters, nBins, weights = contour_values)
        else:
            h, xedges, yedges = np.histogram2d(x, t, nBins, weights = contour_values)
        total_contour_value = np.sum(contour_values)
        h /= total_contour_value
        check_values = h.reshape(((len(xedges) - 1) * (len(yedges) - 1),))
        percentiles = np.percentile(check_values[check_values != 0], [10, 25, 50, 75, 90])
        
        
        #h_n, _, _ = np.histogram2d(x, t, nBins)
        contours = ax.contour(np.array(xedges[:-1] + ((xedges[1] - xedges[0])/2), dtype = np.float64),
                              np.array(yedges[:-1] + ((yedges[1] - yedges[0])/2), dtype = np.float64),
                              np.array(h.T, dtype = np.float64),
                              levels = np.array(percentiles, dtype = np.float64),
                              colors = "k",
                              alpha = 0.5,
                              linewidths = 1,#0.7,
                              linestyles = ["solid", "dotted"])
        #non_density_percentiles = percentiles * total_contour_value
        #labels = ax.clabel(contours,
        #                   contours.levels,
        #                   inline = True,
        #                   fontsize = 6)

    Console.print_verbose_info("Saving to file.")
    fig.savefig(output_file_path)
    Console.print_verbose_info("File saved.")

    

def __main(data, output_file, colour, colour_unit, colour_name, fraction_colour, fraction_mean_colour, log_colour, colour_weight,
           contour, contour_unit, colour_min, colour_max, keep_outliers, limit_fields, limit_units, limits_min, limits_max, exclude_limits_from_contour, colour_map, **kwargs):
    box_region_object = BoxRegion(**BoxRegion.filter_command_params(**kwargs))

    Console.print_debug("Paramiters:\ndata: {}\noutput_file: {}\ncolour: {}\ncolour_unit: {}\ncolour_name: {}\nfraction_colour: {}\nfraction_mean_colour: {}\nlog_colour: {}\ncolour_weight: {}\ncontour: {}\ncontour_unit: {}\ncentre_x_position: {}\ncentre_y_position: {}\ncentre_z_position: {}\nside_length: {}\nx_min: {}\nx_max: {}\ny_min: {}\ny_max: {}\nz_min: {}\nz_max: {}\ncolour_min: {}\ncolour_max: {}\nkeep_outliers: {}".format(
         data, output_file, colour, colour_unit, colour_name, fraction_colour, fraction_mean_colour, log_colour, colour_weight,
         contour, contour_unit, *box_region_object.centre, box_region_object.side_length,
         box_region_object.x_min, box_region_object.x_max, box_region_object.y_min, box_region_object.y_max, box_region_object.z_min, box_region_object.z_max, colour_min, colour_max, keep_outliers))
    
    Console.print_verbose_info(f"Loading data file ({data}).")
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
    if exclude_limits_from_contour is not None: kwargs["exclude_limits_from_contour"] = exclude_limits_from_contour

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
                    *ParticleFilter.get_command_params(),
                   ["exclude-limits-from-contour", None, "Specified limits should NOT apply to the contoured data.",
                                                                                    False, True, None, None],
                   ["colour-map",           None, "Name of the colour map to use. Supports the avalible matplotlib colourmaps" + (", as well as those designed by Paul Tol (https://personal.sron.nl/~pault/).\nTo use a custom map, specify the colours in the format \"#RRGGBB\" as a semicolon seperated list (must have at least 2 values)." if TOL_AVAILABLE else ".\nTo add support for Paul Tol's colours, download the python file from https://personal.sron.nl/~pault/ and install using \"add-py tol_colors\".") + "\nDefaults to whatever is set by the stylesheet - usually \"viridis\".",
                                                                                    False, False, ScriptWrapper.make_list_converter(";"), None]
                  ]
    
    script = ScriptWrapper("temp_density_diagram.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["argparse", "BoxRegion.py  (local file)", "console_log_printing.py (local file)", "get_gas_crit_density.py (local file)", "matplotlib", "numpy", "os", "scipy", "swift_data_expression.py (local file)", "swiftsimio", "script_wrapper.py (local file)", "sys", "typing", "unyt"],
                           ["--pressure --data ~/datafile.hdf5 -o result.png", "--density --data ~/datafile.hdf5 -o result.png --node gas --colour mean_metal_weighted_redshifts", "--pressure --data ~/datafile.hdf5 -o result.png -x 5 -y 253 -w 20", "--density --data ~/datafile.hdf5 -o result.png --z-min 10 --z-max 20"],
                           args_info,
                           kwargs_info)

    script.run(__main)
    