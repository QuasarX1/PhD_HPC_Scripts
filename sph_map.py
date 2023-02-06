#AUTHOR = "Christopher Rowe"
#VERSION = "2.0.0"
#DATE = "06/02/2023"
#DESCRIPTION = "Renders SWIFT SPH data."
#
#from argparse import ArgumentError
#from matplotlib import pyplot as plt
#from matplotlib.colors import LogNorm
#import numpy as np
#import os
#import swiftsimio as sw
#from swiftsimio.visualisation.sphviewer import SPHViewerWrapper
#import sys
#from typing import List
#from unyt import Mpc, Unit, unyt_array as u_arr
#
#sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
#from box_region import BoxRegion
#import console_log_printing as clp
#from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug
#from script_wrapper import ScriptWrapper
#from swift_data_expression import seperate_terms, parse_string
#
#
#
## Value of 1K resolution
#RESOLUTION_BASE_MESUREMENT = 1080
#
#
#
#def __main(data: str, output_file: str,
#           gas: bool, star: bool, dark_matter: bool,
#           camera_x_position: float, camera_y_position: float, camera_z_position: float, projection: bool, perspective: bool, projection_width: float,
#           smoothing_attr: str, smoothing_unit: str, filter_unit: str, filter_min: float, filter_max: float,
#           contour: str, contour_percentiles: List[float],
#           title: str, no_density: bool, no_log: bool, image_size: int,
#           **kwargs):
#           
#    bok_region = BoxRegion(**kwargs)
#
#
#
#if __name__ == "__main__":
#    args_info = [
#                 ["data", "SWIFT snapshot file.", None],
#                 ["output_file", "Name (or relitive file path) to store the resulting image.", None]
#                ]
#    kwargs_info = [
#                   ["gas", None, "Gas map (gas, star and dark-matter flags are exclusive).\nThis is the defult of no map type is specified.", False, True, None, True, ["star", "dark-matter"]],
#                   ["star", None, "Star map (gas, star and dark-matter flags are exclusive).", False, True, None, None, ["gas", "dark-matter"]],
#                   ["dark-matter", None, "Dark Matter map (gas, star and dark-matter flags are exclusive).", False, True, None, None, ["gas", "star"]],
#
#                   ["camera-x-position", "x", "Position of the camera on the x-axis in Mpc.", True, False, float, None],
#                   ["camera-y-position", "y", "Position of the camera on the y-axis in Mpc.", True, False, float, None],
#                   ["camera-z-position", "z", "Position of the camera on the z-axis in Mpc.\nDefaults to 0.0 if not set.", False, False, float, 0.0],
#                   ["projection", None, "Image is rendered as a parallel projection.\nNot compatible with the --perspective flag.\nThis is the default render option.", False, True, None, True, ["perspective"]],
#                   ["perspective", None, "Image is rendered with perspective projection from the camera.\nNot compatible with the --projection flag.", False, True, None, True, ["projection"]],
#                   ["projection-width", "w", "Size of the projected region's width/height in Mpc.\nThis will default to 5 Mpc if unset.", False, False, float, 5.0],
#
#                   ["smoothing-attr", "s", "Smoothing variable or expression.\nTerms must start with the particle attribute, e.g. \"gas.masses*gas.metallicity\".\nThis will default to \"gas.masses\" and will produce a surface density map if the --no-density flag remains unset.", False, False, None, "gas.masses"],
#                   ["smoothing-unit", "u", "Smoothing variable unit (valid unyt string - use \"Mpc\" not \"mpc\").\n Defaults to \"Msun\".", False, False, None, "Msun"],
#                   ["filter-unit", None, "Filter variable unit (valid unyt string - use \"Mpc\" not \"mpc\").\nSpecifying this will indicate a particle filter based on the first term of the smoothing length variable argument.", False, False, None, None],
#                   ["filter-min", None, "Minimum (exclusive) value to filter away anything less than or equal.", False, False, float, None],
#                   ["filter-max", None, "Maximum (inclusive) value to filter away anything more than.", False, False, float, None],
#
#                   ["contour", "c", "Optionally draw contours for a specified variable.\nName (or expression) of the data set containing data to be used for colouring.\nPermits float constants.", False, False, None, None],
#                   ["contour-percentiles", None, "Comma seperated list of percentile values to place contours on.\nDefault is \"10.0,25.0,50.0,75.0,90.0\".", False, False, ScriptWrapper.make_list_converter(",", float), [10.0,25.0,50.0,75.0,90.0]],
#
#                   ["title", "t", "Title for the map (defaults to an empty string).", False, False, None, ""],
#                   ["no-density", "p", "Remove the surface density dependance on the colour units.", False, True, None, None],
#                   ["no-log", "l", "Do not log the pixel values before applying colours.", False, True, None, None],
#                   ["image-size", "r", "Size of the (square) image in pixels (defaults to 1080px).", False, False, int, "1080"],
#
#                   *BoxRegion.get_command_params(use_abbriviation = False)
#                  ]
#    
#    script = ScriptWrapper("sph_map.py",
#                           AUTHOR,
#                           VERSION,
#                           DATE,
#                           DESCRIPTION,
#                           [],
#                           ["snapshot_file.hdf5 test.png --gas -r 1080 -x 10 -y 200"],
#                           args_info,
#                           kwargs_info)
#
#    script.run(__main)

















































"""
File: sph_map.py

Author: Christopher Rowe
Vesion: 1.1.1
Date:   19/01/2023

Renders SWIFT SPH data.



Commandline arguments & flags (r = required paramiter, f = optional flag,
                               f+ = optional flag with a required argument):

    (f ) --help               || -h --> Display this docstring.

    (f ) --verbose            || -v --> Display progression infomation.

    (f ) --debug              || -d --> Display debug infomation.

    ( r) --output_file        || -o --> Name (or relitive file path) to store
                                            the resulting image.

    (f ) --gas                ||    --> Gas map (gas, star and dark-matter flags are exclusive).
                                            This is the defult of no map type is specified.

    (f ) --star               ||    --> Star map (gas, star and dark-matter flags are exclusive).

    (f ) --dark-matter        ||    --> Dark Matter map (gas, star and dark-matter flags are exclusive).

    (f+) --title              || -t --> Title for the map (defaults to an empty string).

    (f ) --no-density         || -p --> Remove the surface density dependance on the colour units.

    (f ) --no-log             || -l --> Do not log the pixel values before applying colours.

    (f+) --image_size         || -r --> Size of the (square) image in pixels (defaults to 1080px).

    ( r) --camera-x-position  || -x --> Position of the camera on the x-axis in Mpc.

    ( r) --camera-y-position  || -y --> Position of the camera on the y-axis in Mpc.

    (f+) --camera-z-position  || -z --> Position of the camera on the z-axis in Mpc.

    (f ) --projection         ||    --> Image is rendered as a parallel projection.

    (f+) --projection-width   || -w --> Size of the projected region's width/height in Mpc.

    (f ) --perspective        ||    --> Gas map (gas, star and dark-matter flags are exclusive).

    (f+) --smoothing-attr     || -s --> Smoothing variable or expression with no spaces.
                                            Only supports * and / operators and terms must start with the
                                            particle attribute, e.g. "gas.masses*gas.metallicity".

    (f+) --smoothing-unit     || -u --> Smoothing variable unit (valid unyt string - use "Mpc" not "mpc").

    (f+) --filter-unit        ||    --> Filter variable unit (valid unyt string - use "Mpc" not "mpc").
                                            Specifying this will indicate a particle filter based on the
                                            first term of the smoothing length variable argument.

    (f+) --filter-min         ||    --> Minimum (exclusive) value to filter away anything less than or equal.

    (f+) --filter-max         ||    --> Maximum (inclusive) value to filter away anything more than.

    (f+) --contour            || -c --> Optionally draw contours for a specified variable.
                                            Name (or expression with no spaces) of the data set containing
                                            data to be used for colouring. Only supports * and / operators,
                                            and permits int and float constants.

    (f+) --contour-percentiles||    --> Comma seperated list of percentile values to place contours on.
                                            Default is "10,25,50,75,90"



Dependancies:

    argparse
    console_log_printing.py (local file)
    matplotlib
    numpy
    os
    swift_data_expression.py (local file)
    swiftsimio
    sys
    unyt



Example Usage:

    python sph_map.py snapshot_file.hdf5 -o test.png --gas -r 1080 -x 10 -y 200
"""

from argparse import ArgumentError
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import os
from swift_data_expression import seperate_terms, parse_string
import swiftsimio as sw
from swiftsimio.visualisation.sphviewer import SPHViewerWrapper
import sys
from unyt import Mpc, Unit, unyt_array as u_arr

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
import console_log_printing as clp
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug

# Value of 1K resolution
RESOLUTION_BASE_MESUREMENT = 1080

def sph_gas_map_projection(filepath: str, data_file: str, camera_x: float, camera_y: float, camera_z: float = None, title: str = "", desnsity_map: bool = True, log_colours: bool = True, resolution: int = 1080, viewport: float = None, smoothing_variable: str = "gas.masses", smoothing_variable_unit = "Msun", filter_unit: bool = None, filter_min: float = None, filter_max: float = None, contour_expression = None, contour_percentiles = [10,25,50,75,90]):
    if viewport is None:
        pass#TODO:
    camera_settings = { "xsize": resolution, "ysize": resolution, "r": "infinity", "extent": [-viewport * Mpc / 2, viewport * Mpc / 2, -viewport * Mpc / 2, viewport * Mpc / 2] }
    _sph_gas_map(True, False, filepath, data_file, camera_x, camera_y, camera_z, title, desnsity_map, log_colours, resolution, camera_settings, smoothing_variable, smoothing_variable_unit, filter_unit, filter_min, filter_max, contour_expression, contour_percentiles)

#def sph_gas_map_perspective(filepath: str, data_file: str, camera_x: float, camera_y: float, camera_z: float = None, title: str = "", desnsity_map: bool = True, log_colours: bool = True, resolution: int = 1080, smoothing_variable: str = "gas.masses", smoothing_variable_unit = "Msun/kpc**2", filter_unit: bool = None, filter_min: float = None, filter_max: float = None, contour_expression = None, contour_percentiles = [10,25,50,75,90], ):
#    #TODO: {'x': x, 'y': y, 'z': z, 'r': r, 't': t, 'p': p, 'zoom': zoom, 'roll': roll, 'xsize': xsize, 'ysize': ysize, 'extent': extent}
#    camera_settings = { "x": camera_x, "y": camera_y, "xsize": resolution, "ysize": resolution }
#    _sph_gas_map(False, True, filepath, data_file, camera_x, camera_y, camera_z, title, desnsity_map, log_colours, resolution, camera_settings, smoothing_variable, smoothing_variable_unit, filter_unit, filter_min, filter_max, contour_expression, contour_percentiles)

def _sph_gas_map(projection: bool, perspective: bool, filepath: str, data_file: str, camera_x: float, camera_y: float, camera_z: float = None, title: str = "", desnsity_map: bool = True, log_colours: bool = True, resolution: int = 1080, camera_settings: dict = {}, smoothing_variable: str = "gas.masses", smoothing_variable_unit = "Msun", filter_unit: bool = None, filter_min: float = None, filter_max: float = None, contour_expression = None, contour_percentiles = [10,25,50,75,90]):
    coordinate_units = "Mpc"

    particle_data = None
    if filter_unit:
        min_val = filter_min if filter_min is not None else -np.inf
        max_val = filter_max if filter_max is not None else np.inf

        mask = sw.mask(data_file, spatial_only = False)

        #TODO: DOES THIS STILL WORK!!!
        #u.Msun.units.dimensions
        #dim_string = str(parse_string(smoothing_variable.replace("**", "¬").replace("*", "¬").replace("/", "¬").replace("+", "¬").replace("-", "¬").split("¬")[0], sw.load(data_file))[0].units.dimensions).replace("(", "").replace(")", "")
        dim_string = str(parse_string(seperate_terms(smoothing_variable)[0][0], sw.load(data_file))[0].units.dimensions).replace("(", "").replace(")", "")
        
        if dim_string != "1":
            dims = dim_string.replace("**", "¬").replace("*", "¬").replace("/", "¬").split("¬")
            ops_string = dim_string
            for i in range(len(dims)):
                ops_string = ops_string.replace(dims[i], "|")
            ops = ops_string.strip("|").split("|")
            
            dimension_unit = None
            first_pass = True
            i = 0
            while i < len(dims):
                dim = None
                try:
                    dim = float(dims[i])
                except:
                    dim = mask.units.__getattribute__(dims[i])
                    

                if i < len(ops) and ops[i] == "**":
                    dim2 = None
                    try:
                        dim2 = float(dims[i + 1])
                    except:
                        dim2 = mask.units.__getattribute__(dims[i + 1])
                    dim = dim ** dim2
                    i += 1

                if first_pass:
                    first_pass = False
                    dimension_unit = dim
                    i += 1
                    continue

                else:
                    op = ops[i - 1]
                    reverse_counter = 1
                    while op == "**":
                        reverse_counter += 1
                        op = ops[i - reverse_counter]

                    if op == "*":
                        dimension_unit *= dim
                    elif op == "/":
                        dimension_unit /= dim

                i += 1

            dimension_unit = dimension_unit.units
            min_val_converted = (min_val * Unit(filter_unit)).to(dimension_unit)
            max_val_converted = (max_val * Unit(filter_unit)).to(dimension_unit)
            
        else:
            min_val_converted = min_val
            max_val_converted = max_val

        mask.constrain_mask("gas", smoothing_variable.replace("*", "/").replace("+", "/").replace("-", "/").split("/")[0].split(".", 1)[1], min_val_converted, max_val_converted)

        print_verbose_info(f"Loading data file ({data_file}).")
        particle_data: sw.SWIFTDataset = sw.load(data_file, mask)
        print_debug("Loaded data.")

    else:
        particle_data: sw.SWIFTDataset = sw.load(data_file)

    print_debug("HERE 1")
    print_debug(coordinate_units)
    print_debug(particle_data.gas.coordinates)

    particle_data.gas.coordinates.convert_to_units(coordinate_units)
    print_debug("HERE 2")
    particle_data.gas.smoothing_lengths.convert_to_units(coordinate_units)

    print_debug("HERE 3")

    if not desnsity_map:
        smoothing_variable_unit += ("*" if smoothing_variable_unit != "" else "") + "Msun"

    gas = None
    print_debug(smoothing_variable)
    if smoothing_variable == "gas.masses":
        particle_data.gas.masses.convert_to_units(smoothing_variable_unit)
        gas = SPHViewerWrapper(particle_data.gas, smooth_over = "masses")
    else:
        particle_data.smoothing_attribute = parse_string(smoothing_variable, particle_data)
        if not desnsity_map:
            particle_data.smoothing_attribute *= particle_data.gas.masses
        particle_data.smoothing_attribute.convert_to_units(smoothing_variable_unit)
        gas = SPHViewerWrapper(particle_data.gas, smooth_over = particle_data.smoothing_attribute)

    gas_camera = gas.get_autocamera()
    camera_settings["x"] = camera_x
    camera_settings["y"] = camera_y
    if camera_z is not None:
        camera_settings["z"] = camera_z
    gas_camera.set_params(**camera_settings)

    gas_scene = gas.get_scene()
    gas_render = gas.get_render()
    gas_image = gas.image

    if not desnsity_map:
        mass_map = SPHViewerWrapper(particle_data.gas, smooth_over = "masses")
        mass_map_camera = mass_map.get_autocamera()
        mass_map_camera.set_params(**camera_settings)
        
        mass_map_scene = mass_map.get_scene()
        mass_map_render = mass_map.get_render()
        mass_map_image = mass_map.image
        
        gas_image = gas_image / mass_map_image

    if log_colours:
        gas_image[:, :] = np.log10(gas_image)

    if (contour_expression is not None) and projection:
        contour_particle_data: sw.SWIFTDataset = particle_data

        contour_terms = seperate_terms(contour_expression)[0]
        smoothing_terms = [item.split(".")[-1] for item in seperate_terms(smoothing_variable)[0]]
        if len(contour_terms) != len(smoothing_terms) or sum([contour_terms[i] == smoothing_terms[i] for i in range(len(contour_terms))]):
            contour_particle_data = sw.load(data_file)
            contour_particle_data.gas.coordinates.convert_to_units(coordinate_units)
            contour_particle_data.gas.smoothing_lengths.convert_to_units(coordinate_units)
            
        contour_particle_data.contour_attribute = parse_string(contour_expression, contour_particle_data.gas)
        
        contour_map = SPHViewerWrapper(contour_particle_data.gas, smooth_over = contour_particle_data.contour_attribute)
        contour_map_camera = contour_map.get_autocamera()
        contour_map_camera.set_params(**camera_settings)
        
        contour_map_scene = contour_map.get_scene()
        contour_map_render = contour_map.get_render()
        contour_map_image = contour_map.image

        contour_pixels_1D = contour_map_image.reshape((resolution**2,))

        image_pixel_axis_positions = np.linspace(0, resolution - 1, resolution)

        a = [image_pixel_axis_positions[i % resolution] for i in range(resolution**2)]
        b = [image_pixel_axis_positions[i // resolution] for i in range(resolution**2)]

        nBins = 50
        h, xedges, yedges = np.histogram2d(a, b, nBins, weights = contour_pixels_1D)
        total_contour_value = np.sum(contour_pixels_1D)
        h /= total_contour_value
        check_values = h.reshape(((len(xedges) - 1) * (len(yedges) - 1),))
        percentiles = np.percentile(check_values[check_values != 0], contour_percentiles)

    stylesheet_directory = __file__.rsplit(os.path.sep, 1)[0]
    normal_stylesheet = os.path.join(stylesheet_directory, "sph_map_stylesheet.mplstyle")
    smalltext_stylesheet = os.path.join(stylesheet_directory, "sph_map_smalltext_stylesheet.mplstyle")
    plt.style.use(normal_stylesheet)
    inches = plt.rcParams["figure.figsize"][0]
    dpi = resolution / inches
    plt.figure(dpi = dpi)
    plt.axis("off")
    plt.imshow(gas_image)
    with plt.style.context(smalltext_stylesheet):
        colourbar = plt.colorbar(shrink = 0.7, location = "left", pad = -1.0)
        colourbar.set_label(("${\\rm log_{10}}$ " if log_colours else "") + title + " " + (("${\\rm " + str(gas_image[0][0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + "}$") if str(gas_image[0][0].units.expr) != "1" else ""))

    if (contour_expression is not None) and projection:
        contours = plt.contour((xedges[:-1] + ((xedges[1] - xedges[0])/2)) * Mpc,
                               (yedges[:-1] + ((yedges[1] - yedges[0])/2)) * Mpc,
                               h.T,
                               levels = percentiles,
                               colors = "k",
                               alpha = 0.5,
                               linewidths = 1,#0.7,
                               linestyles = ["dashed", "solid", "dotted"])
        #non_density_percentiles = percentiles * total_contour_value
        #labels = ax.clabel(contours,
        #                   contours.levels,
        #                   inline = True,
        #                   fontsize = 6)

    _stringValues = [gas_camera.get_params()["x"], gas_camera.get_params()["y"], gas_camera.get_params()["z"]]
    testVar1 = "({0:.3f}, {1:.3f}, {2:.3f}) ${{\\rm {3}}}$".format(*_stringValues, coordinate_units)
    print()
    print(testVar1)
    plt.text(0, resolution * (1 - 0.04),
             testVar1,#"({0:.3f}, {1:.3f}, {2:.3f}) ${{\\rm {3}}}$".format(*_stringValues, coordinate_units),
             usetex = False,#True,
             bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))

    if projection:
        viewport = camera_settings["extent"][1] - camera_settings["extent"][0]
        testVar2 = f"{float(viewport)} ${{\\rm Mpc}}$"
        print(testVar2)
        print()
        plt.text(0, resolution * (1 - 0.093),
                 testVar2,#f"{float(viewport)} ${{\\rm Mpc}}$",
                 usetex = False,#True,
                 bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))
    else:
        pass#TODO: perspective log text

    #plt.text(resolution * 0.999, resolution * 0.02,
    #         ("$log_{10}\\left(" if log_colours else "$") + str(gas_image[0][0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + ("\\right)$" if log_colours else "$"),
    #         usetex = True,
    #         horizontalalignment = "right",
    #         bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))
    #
    #if title is not None and title != "":
    #    plt.text(0, resolution * 0.01,
    #             title,
    #             usetex = True,
    #             bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))

    #plt.rcParams["figure.figsize"] = (inches, inches)
    cameraSettingsInsert = f"{float(viewport)}Mpc" if projection else f""#TODO: perspective log text
    filepath_sections = filepath.rsplit(".", 1)
    plt.savefig(f"{filepath_sections[0]}__{cameraSettingsInsert}_{resolution / RESOLUTION_BASE_MESUREMENT}K_py-sphviewer.{filepath_sections[1]}", dpi = dpi)

def sph_map_projection():
    pass#TODO:

def sph_map_perspective():
    pass#TODO:

def __main():
    print_verbose_info("Loading arguments.")
    args = sys.argv[1:]
    print_debug(f"Arguments are: {args}")
    if len(args) == 0 or args[0][0] == "-" and args[0].lower() not in ("-h", "--help"):
        raise ArgumentError(None, "No data is provided. Data must be the first argument (other than the '-h' flag).")

    output_file_name = None
    map_type = "gas"
    title = ""
    density_map = True
    log_colours = True
    image_size = 1080
    camera_location = [0, 0, None]
    projection_mode = "projection"
    projection_width = None
    smoothing_function = "gas.masses"
    smoothing_function_unit = "Msun"
    filter_unit = None
    filter_min = None
    filter_max = None
    contour_expression = None
    contour_percentiles = [10,25,50,75,90]

    print_verbose_info("Parsing arguments.")
    arg_index = 0
    while arg_index < len(args):
        if args[arg_index].lower() in ("-h", "--help"):
            print_verbose_info("Handling help flag.")
            print(__doc__)
            sys.exit()
        elif args[arg_index].lower() in ("-d", "--debug", "-v", "--verbose"):
            print_verbose_info(f"Skipping pre-parsed {args[arg_index]} flag.")
        elif args[arg_index].lower() in ("-o", "--output_file"):
            output_file_name = args[arg_index + 1]
            arg_index += 1
        elif args[arg_index].lower() == "--gas":
            map_type = "gas"
        elif args[arg_index].lower() == "--star":
            map_type = "star"
        elif args[arg_index].lower() == "--dark-matter":
            map_type = "DM"
        elif args[arg_index].lower() in ("-t", "--title"):
            title = args[arg_index + 1]
            arg_index += 1
        elif args[arg_index].lower() in ("-p", "--no-density"):
            density_map = False
        elif args[arg_index].lower() in ("-l", "--no-log"):
            log_colours = False
        elif args[arg_index].lower() in ("-r", "--image_size"):
            image_size = int(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() in ("-x", "--camera-x-position"):
            camera_location[0] = float(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() in ("-y", "--camera-y-position"):
            camera_location[1] = float(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() in ("-z", "--camera-z-position"):
            camera_location[2] = float(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() == "--projection":
            projection_mode = "projection"
        elif args[arg_index].lower() == "--perspective":
            projection_mode = "perspective"
        elif args[arg_index].lower() in ("-w", "--projection-width"):
            projection_width = float(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() in ("-s", "--smoothing-attr"):
            smoothing_function = args[arg_index + 1]
            arg_index += 1
        elif args[arg_index].lower() in ("-u", "--smoothing-unit"):
            smoothing_function_unit = args[arg_index + 1]
            arg_index += 1
        elif args[arg_index].lower() == "--filter-unit":
            filter_unit = args[arg_index + 1]
            arg_index += 1
        elif args[arg_index].lower() == "--filter-min":
            filter_min = float(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() == "--filter-max":
            filter_max = float(args[arg_index + 1])
            arg_index += 1
        elif args[arg_index].lower() in ("-c", "--contour"):
            contour_expression = args[arg_index + 1]
            arg_index += 1
        elif args[arg_index].lower() == "--contour-percentiles":
            contour_percentiles = [float(v) for v in args[arg_index + 1].replace("(", "").replace(")", "").replace("[", "").replace("]", "").split(",")]
            arg_index += 1

        arg_index += 1

    data_file = args[0]

    if map_type == "gas":
        if projection_mode == "projection":
            sph_gas_map_projection(output_file_name, data_file, *camera_location, title, density_map, log_colours, image_size, projection_width, smoothing_function, smoothing_function_unit, filter_unit, filter_min, filter_max, contour_expression, contour_percentiles)
        elif projection_mode == "perspective":
            pass#sph_gas_map_perspective(output_file_name, data_file, *camera_location, title, density_map, log_colours, image_size, smoothing_function smoothing_function_unit, filter_unit, filter_min, filter_max, contour_expression, contour_percentiles)
    else:
        if projection_mode == "projection":
            sph_map_projection(data_file, output_file_name, map_type, title, density_map, log_colours, image_size, projection_width, smoothing_function, smoothing_function_unit, filter_unit, filter_min, filter_max, contour_expression, contour_percentiles)
        elif projection_mode == "perspective":
            sph_map_perspective(data_file, output_file_name, map_type, title, density_map, log_colours, image_size, smoothing_function, smoothing_function_unit, filter_unit, filter_min, filter_max, contour_expression, contour_percentiles)

if __name__ == "__main__":
    lowercase_args = [arg.lower() for arg in sys.argv]
    if "-d" in lowercase_args or "--debug" in lowercase_args:
        clp.enable_debug()
    if "-v" in lowercase_args or "--verbose" in lowercase_args:
        clp.enable_verbose()

    __main()
