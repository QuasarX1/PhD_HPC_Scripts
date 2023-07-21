AUTHOR = "Christopher Rowe"
VERSION = "3.0.0"
DATE = "07/07/2023"
DESCRIPTION = "Renders SWIFT SPH data."

from enum import Enum
from matplotlib import pyplot as plt
import numpy as np
import os
from sphviewer import Particles, Camera, Scene, Render
import swiftsimio as sw
from typing import List, Union
from unyt import Mpc

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



# Value of 1K resolution
RESOLUTION_BASE_MESUREMENT = 1080

# Enum for render type
class RenderType(Enum):
    projection = 0
    perspective = 1



def _render_pixels(particle_data: sw.SWIFTDataset, parttype: PartType, spatial_filter: np.ndarray, smooth_over: sw.SWIFTDataset, camera_settings: dict, return_camera = False):
    dataset = parttype.get_dataset(particle_data)

    length_units = dataset.coordinates.units
    smooth_units = smooth_over.units / (length_units**2)
    
    # TODO; this may fali for DM - no smothing lengths...?
    particles = Particles(pos = dataset.coordinates.value[spatial_filter], hsml = dataset.smoothing_lengths.value[spatial_filter], mass = smooth_over.value[spatial_filter])

    camera = Camera()
    camera.set_autocamera(particles)
    camera.set_params(**camera_settings)

    scene = Scene(particles, camera)

    render = Render(scene)

    image = render.get_image() * smooth_units
    #extent = render.get_extent() * length_units

    if return_camera:
        return image, camera
    else:
        return image

#def _render_pixels(particle_data: sw.SWIFTDataset, parttype: PartType, spatial_filter: np.ndarray, smooth_over: sw.SWIFTDataset, camera_settings: dict, return_camera = False):
#    Console.print_debug(f"Rendering map for {smooth_over}.")
#    Console.print_debug(f"Camera settings: {camera_settings}.")
#
#    wrapper = SPHViewerWrapper(parttype.get_dataset(particle_data), smooth_over = smooth_over)
#
#    camera = wrapper.get_autocamera()
#    camera.set_params(**camera_settings)
#
#    scene = wrapper.get_scene()
#    render = wrapper.get_render()
#
#    if return_camera:
#        return wrapper.image, camera
#    else:
#        return wrapper.image

def make_plot(particle_data: sw.SWIFTDataset, output_file: str,
              box_region: BoxRegion, parttype: PartType,
              x: float, y: float, z: float, render_type: RenderType, projection_width = 5,
              smoothing_attr: str = "gas.masses", smoothing_unit: str = "Msun",
#              filter_attr: str = None, filter_unit: str = None, filter_min: float = None, filter_max: float = None,
              limit_fields: Union[None, str, List[str]] = None, limit_units: Union[None, str, List[str]] = None, limits_min: Union[None, float, List[float]] = None, limits_max: Union[None, float, List[float]] = None,
              contour: str = None, contour_percentiles: List[float] = [10.0, 25.0, 50.0, 75.0, 90.0], exclude_limits_from_contour: bool = False,
              title: str = "", no_density: bool = False, no_log: bool = False, log_pre_intergration: bool = False, image_size: int = 1080,
              colour_map: List[str] = None):

    Console.print_debug(("Making plot. Params are:" + ("\n{}" * 23)).format(particle_data, output_file, box_region, parttype, x, y, z, render_type, projection_width, smoothing_attr, smoothing_unit, limit_fields, limit_units, limits_min, limits_max, contour, contour_percentiles, exclude_limits_from_contour, title, no_density, no_log, image_size, colour_map))
    
    # Needed as masking may have only been spatial and would not be exact
    Console.print_verbose_info("Making spatial array filter.")
    spatial_filter = box_region.make_array_filter(particle_data.gas.coordinates)

#    combined_filter = spatial_filter.copy()
#    if filter_attr is not None:
#        filter_dataset = parse_string(filter_attr, particle_data).to(filter_unit)
#        lower_bound_filter = True
#        if filter_min is not None:
#            lower_bound_filter = filter_dataset >= unyt_quantity(filter_min, filter_unit)
#        upper_bound_filter = True
#        if filter_max is not None:
#            upper_bound_filter = filter_dataset <= unyt_quantity(filter_max, filter_unit)
#        other_filter = lower_bound_filter & upper_bound_filter
#
#        combined_filter = combined_filter & other_filter

    particle_filter = ParticleFilter(particle_data, limit_fields, limit_units, limits_min, limits_max) if ParticleFilter.check_limits_present(limit_fields) else ParticleFilter.passthrough_filter(particle_data, parttype)
    particle_filter.update(spatial_filter)
    
    # Set the units for coordinates and smothing lengths (this shouldn't actualy read the file so easier to do this for all 3 possible part types)
    Console.print_verbose_info("Converting units of spatial fields.")
    coordinate_units = "Mpc"

    particle_data.gas.coordinates.convert_to_units(coordinate_units)
    particle_data.dark_matter.coordinates.convert_to_units(coordinate_units)
    particle_data.stars.coordinates.convert_to_units(coordinate_units)

    particle_data.gas.smoothing_lengths.convert_to_units(coordinate_units)
    #particle_data.dark_matter.smoothing_lengths.convert_to_units(coordinate_units)#TODO: handle
    particle_data.stars.smoothing_lengths.convert_to_units(coordinate_units)

    # Create the camera settings
    Console.print_verbose_info("Assembling camera settings.")
    if render_type == RenderType.projection:
        camera_settings = { "r": "infinity", "extent": [-projection_width * Mpc / 2, projection_width * Mpc / 2, -projection_width * Mpc / 2, projection_width * Mpc / 2] }
    else:
        raise NotImplementedError()

    camera_settings["xsize"] = image_size
    camera_settings["ysize"] = image_size
    camera_settings["x"] = x
    camera_settings["y"] = y
    if z is not None:#TODO: does this approach need altering?
        camera_settings["z"] = z

    # Identify the particle node for the selected parttype
    selected_dataset = parttype.get_dataset(particle_data)

    # Parsing the smothing attribute expression
    Console.print_verbose_info("Parsing smothing expression.")
    selected_dataset.smothing_attribute = parse_string(smoothing_attr, particle_data)

    Console.print_debug("Raw smoothing attr min value: {}".format(np.array(selected_dataset.smothing_attribute[:][particle_filter.numpy_filter]).min()))
    Console.print_debug("Raw smoothing attr max value: {}".format(np.array(selected_dataset.smothing_attribute[:][particle_filter.numpy_filter]).max()))
    Console.print_debug("Raw smoothing attr mean value: {}".format(np.array(selected_dataset.smothing_attribute[:][particle_filter.numpy_filter]).mean()))

    # Set the units as requested
    selected_dataset.smothing_attribute.convert_to_units(smoothing_unit)

    Console.print_debug("Unit converted smoothing attr min value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].min()))
    Console.print_debug("Unit converted smoothing attr max value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].max()))
    Console.print_debug("Unit converted smoothing attr mean value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].mean()))
    
    if log_pre_intergration and not no_log:
        Console.print_verbose_info("Logging the data values.")
        selected_dataset.smothing_attribute[selected_dataset.smothing_attribute != 0] = np.log10(selected_dataset.smothing_attribute[selected_dataset.smothing_attribute != 0])
        Console.print_debug("Logged smoothing attr min value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].min()))
        Console.print_debug("Logged smoothing attr max value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].max()))
        Console.print_debug("Logged smoothing attr mean value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].mean()))

    # Make modifications to remove the surface density term from the result
    if no_density:
        Console.print_verbose_info("Preparing to account for surface density.")
        # Add a mass unit to the smothing unit to account for the mass weighting of the data
#        smoothing_unit += ("*" if smoothing_unit != "" else "") + "Msun"
        selected_dataset.masses.convert_to_units("Msun")
        Console.print_debug("Masses min value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].min()))
        Console.print_debug("Masses max value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].max()))
        Console.print_debug("Masses mean value: {}".format(selected_dataset.smothing_attribute[particle_filter.numpy_filter].mean()))
        selected_dataset.smothing_attribute = selected_dataset.smothing_attribute * selected_dataset.masses
        Console.print_verbose_info("New units of initial map are {}.".format(smoothing_unit))

    # Generate the mapp of the data (or mass weighted data)
    Console.print_verbose_info("Generating initial map.")
    data_image, camera = _render_pixels(particle_data, parttype, particle_filter.numpy_filter, selected_dataset.smothing_attribute, camera_settings, return_camera = True)

    if no_density:
        # Remove the surface density dependance and make each pixel a mass weighted mean
        Console.print_verbose_info("Generating and dividing map by surface density map.")
        data_image /= _render_pixels(particle_data, parttype, particle_filter.numpy_filter, selected_dataset.masses, camera_settings)

    # Log the pixel values for image-like maps (unless specified otherwise)
    if not log_pre_intergration and not no_log:
        Console.print_verbose_info("Logging the pixel values.")
        data_image[:, :] = np.log10(data_image)

    Console.print_debug("Final pixel min value: {}".format(data_image.min()))
    Console.print_debug("Final pixel max value: {}".format(data_image.max()))
    Console.print_debug("Final pixel mean value: {}".format(data_image.mean()))

    # If contours are requested, plot them, but only one a projection map
    #TODO: surely contours should be ok on a perspective map???
    draw_contours = False
    if (contour is not None) and render_type == RenderType.projection:
        Console.print_verbose_info("Generating contours.")
        draw_contours = True
            
        selected_dataset.contour_attribute = parse_string(contour, particle_data)
        contour_map_image = _render_pixels(particle_data, parttype, spatial_filter if exclude_limits_from_contour else particle_filter.numpy_filter, selected_dataset.contour_attribute, camera_settings)

        contour_pixels_1D = contour_map_image.reshape((image_size**2,))

        image_pixel_axis_positions = np.linspace(0, image_size - 1, image_size)

        a = [image_pixel_axis_positions[i % image_size] for i in range(image_size**2)]
        b = [image_pixel_axis_positions[i // image_size] for i in range(image_size**2)]

        nBins = 50
        h, xedges, yedges = np.histogram2d(a, b, nBins, weights = contour_pixels_1D)
        total_contour_value = np.sum(contour_pixels_1D)
        h /= total_contour_value
        check_values = h.reshape(((len(xedges) - 1) * (len(yedges) - 1),))
        percentiles = np.percentile(check_values[check_values != 0], contour_percentiles)
        
    # Get the stylesheets
    Console.print_verbose_info("Fetching stylesheets.")
    stylesheet_directory = os.path.join(__file__.rsplit(os.path.sep, 1)[0], "..", "stylesheets")
    normal_stylesheet = os.path.join(stylesheet_directory, "sph_map_stylesheet.mplstyle")
    smalltext_stylesheet = os.path.join(stylesheet_directory, "sph_map_smalltext_stylesheet.mplstyle")

    # Start using the base stylesheet
    plt.style.use(normal_stylesheet)

    # Set extra params and create figure object
    inches = plt.rcParams["figure.figsize"][0]
    dpi = image_size / inches
    plt.figure(dpi = dpi)
    plt.axis("off")

    Console.print_verbose_info("Rendering final map.")
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
    # Render the map
    #plt.imshow(data_image, cmap = tol_colors.LinearSegmentedColormap.from_list("test", ["#125A56", "#FD9A44", "#A01813"]))
    plt.imshow(data_image, cmap = (tol_colors.tol_cmap(colour_map[0]) if len(colour_map) == 1 else tol_colors.LinearSegmentedColormap.from_list("custom-map", colour_map)) if TOL_AVAILABLE and (len(colour_map) > 1 or colour_map[0] in tol_colors.tol_cmap()) else colour_map[0])
    #plt.imshow(data_image, cmap = tol_colors.tol_cmap("rainbow_discrete"))
    #plt.imshow(data_image, cmap = tol_colors.tol_cmap("nightfall"))
    #plt.imshow(data_image, cmap = tol_colors.LinearSegmentedColormap.from_list("test", ["#FF0000", "#FFFF00", "#0000FF"]))
    

    # Add a colourbar using the alt stylesheet
    Console.print_verbose_info("Adding colourbar.")
    with plt.style.context(smalltext_stylesheet):
#        colourbar = plt.colorbar(shrink = 0.7, location = "left", pad = -1.0)
        colourbar = plt.colorbar(shrink = 0.7, location = "left", pad = -0.98)
        colourbar.set_label(("${\\rm log_{10}}$ " if not no_log else "") + title + " " + (("${\\rm " + str(data_image[0][0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + "}$") if str(data_image[0][0].units.expr) != "1" else ""), backgroundcolor = "#00000066")
        colourbar.ax.tick_params(direction = "in")#, pad = -20)

    if draw_contours:
        # If they were created earlier, plot the contours
        Console.print_verbose_info("Drawing contours.")
        # Data converted to arrays due to issues with the countour function and unyt arrays
        contours = plt.contour(np.array((xedges[:-1] + ((xedges[1] - xedges[0])/2)) * Mpc, dtype = np.float64),
                               np.array((yedges[:-1] + ((yedges[1] - yedges[0])/2)) * Mpc, dtype = np.float64),
                               np.array(h.T, dtype = np.float64),
                               levels = np.array(percentiles, dtype = np.float64),
                               colors = "k",
                               alpha = 0.5,
                               linewidths = 1,#0.7,
                               linestyles = ["dashed", "solid", "dotted"])
        #non_density_percentiles = percentiles * total_contour_value
        #labels = ax.clabel(contours,
        #                   contours.levels,
        #                   inline = True,
        #                   fontsize = 6)

    # Add text with the camera info

    # Position
    Console.print_verbose_info("Adding camera position.")
    camera_params = camera.get_params()
    plt.text(0, image_size * (1 - 0.040),
             "(${0:.3f}$, ${1:.3f}$, ${2:.3f}$) ${{\\rm {3}}}$".format(camera_params["x"], camera_params["y"], camera_params["z"], coordinate_units),
             #usetex = False,#True,
             bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))

    if render_type == RenderType.projection:
        # Viewport
        Console.print_verbose_info("Adding projection viewport.")
        viewport = camera_settings["extent"][1] - camera_settings["extent"][0]
        #plt.text(0, image_size * (1 - 0.093),
        plt.text(0, image_size * (1 - 0.102),# dh = 0.009 for adding ^
                 f"${float(viewport):.1f}^2$ ${{\\rm Mpc^2}}$",
                 #usetex = False,#True,
                 bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))

        # Slice Depth
        Console.print_verbose_info("Adding depth.")
        box_side_length = box_region.side_length
        if isinstance(box_side_length, list):
            box_side_length = box_side_length[2]
        plt.text(0, image_size * (1 - 0.158),
                 f"${float(box_side_length):.1f}$ ${{\\rm Mpc}}$",
                 #usetex = False,#True,
                 bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))

    else:
        pass#TODO: perspective log text
    
    #plt.text(image_size * 0.999, image_size * 0.02,
    #         ("$log_{10}\\left(" if not no_log else "$") + str(data_image[0][0].units.expr).replace("**", "^").replace("sun", "_{\odot}") + ("\\right)$" if not no_log else "$"),
    #         usetex = True,
    #         horizontalalignment = "right",
    #         bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))
    #
    #if title is not None and title != "":
    #    plt.text(0, image_size * 0.01,
    #             title,
    #             usetex = True,
    #             bbox = dict(facecolor = "black", alpha = 0.4, edgecolor = "black"))

    #plt.rcParams["figure.figsize"] = (inches, inches)
    cameraSettingsInsert = f"{float(viewport):.1f}Mpc2_{box_side_length:.1f}Mpc" if render_type == RenderType.projection else f""#TODO: perspective log text
    filepath_sections = output_file.rsplit(".", 1)
    target_file = f"{filepath_sections[0]}__{cameraSettingsInsert}_{image_size / RESOLUTION_BASE_MESUREMENT}K_py-sphviewer.{filepath_sections[1]}"
    Console.print_verbose_info(f"Saving image to {target_file}")
    plt.savefig(target_file, dpi = dpi)



def __main(data: str, output_file: str,
           gas: bool, star: bool, dark_matter: bool,
           camera_x_position: float, camera_y_position: float, camera_z_position: float, projection: bool, perspective: bool, projection_width: float,
           smoothing_attr: str, smoothing_unit: str,
           limit_fields: Union[None, str, List[str]], limit_units: Union[None, str, List[str]], limits_min: Union[None, float, List[float]], limits_max: Union[None, float, List[float]],
           contour: str, contour_percentiles: List[float], exclude_limits_from_contour: bool,
           title: str, no_density: bool, no_log: bool, log_pre_intergration: bool, image_size: int,
           colour_map: List[str],
           **kwargs):

    parttype = PartType.gas if gas else PartType.dark_matter if dark_matter else PartType.star
           
    box_region = BoxRegion(**kwargs)

    particle_data: sw.SWIFTDataset = sw.load(data)
    box_region.complete_bounds_from_coords(particle_data.gas.coordinates)

    mask = sw.mask(data, spatial_only = True)
    box_region.constrain_mask(mask)

    particle_data: sw.SWIFTDataset = sw.load(data, mask)

    render_type = RenderType.projection if projection else RenderType.perspective

    make_plot(particle_data, output_file,
              box_region, parttype,
              camera_x_position, camera_y_position, camera_z_position, render_type, projection_width,
              smoothing_attr, smoothing_unit,
              limit_fields, limit_units, limits_min, limits_max,
              contour, contour_percentiles, exclude_limits_from_contour,
              title, no_density, no_log, log_pre_intergration, image_size,
              colour_map)



if __name__ == "__main__":
    args_info = [
                 ["data", "SWIFT snapshot file.", None],
                 ["output_file", "Name (or relitive file path) to store the resulting image.", None]
                ]
    kwargs_info = [
                   ["gas", None, "Gas map (gas, star and dark-matter flags are exclusive).\nThis is the defult of no map type is specified.", False, True, None, True, ["star", "dark-matter"]],
                   ["star", None, "Star map (gas, star and dark-matter flags are exclusive).", False, True, None, None, ["gas", "dark-matter"]],
                   ["dark-matter", None, "Dark Matter map (gas, star and dark-matter flags are exclusive).", False, True, None, None, ["gas", "star"]],

                   ["camera-x-position", "x", "Position of the camera on the x-axis in Mpc.", True, False, float, None],
                   ["camera-y-position", "y", "Position of the camera on the y-axis in Mpc.", True, False, float, None],
                   ["camera-z-position", "z", "Position of the camera on the z-axis in Mpc.\nDefaults to 0.0 if not set.", False, False, float, 0.0],
                   ["projection", None, "Image is rendered as a parallel projection.\nNot compatible with the --perspective flag.\nThis is the default render option.", False, True, None, True, ["perspective"]],
                   ["perspective", None, "Image is rendered with perspective projection from the camera.\nNot compatible with the --projection flag.", False, True, None, True, ["projection"]],
                   ["projection-width", "w", "Size of the projected region's width/height in Mpc.\nThis will default to 5 Mpc if unset.", False, False, float, 5.0],

                   ["smoothing-attr", "s", "Smoothing variable or expression.\nTerms must start with the particle attribute, e.g. \"gas.masses*gas.metallicity\".\nThis will default to \"gas.masses\" and will produce a surface density map if the --no-density flag remains unset.", False, False, None, "gas.masses"],
                   ["smoothing-unit", "u", "Smoothing variable unit (valid unyt string - use \"Mpc\" not \"mpc\").\n Defaults to \"Msun\".", False, False, None, "Msun"],
                   
                   #["filter-attr", None, "Filter field in the particle dataset, e.g. \"metallicity\" with a gas map.", False, False, None, None],
                   #["filter-unit", None, "Filter variable unit (valid unyt string - use \"Mpc\" not \"mpc\").", False, False, None, None],
                   #["filter-min", None, "Minimum (exclusive) value to filter away anything less than or equal.", False, False, float, None],
                   #["filter-max", None, "Maximum (inclusive) value to filter away anything more than.", False, False, float, None],
                    *ParticleFilter.get_command_params(),
                   ["contour", "c", "Optionally draw contours for a specified variable.\nName (or expression) of the data set containing data to be used for colouring.\nPermits float constants.", False, False, None, None],
                   ["contour-percentiles", None, "Comma seperated list of percentile values to place contours on.\nDefault is \"10.0,25.0,50.0,75.0,90.0\".", False, False, ScriptWrapper.make_list_converter(",", float), [10.0,25.0,50.0,75.0,90.0]],
                   ["exclude-limits-from-contour", None, "Specified limits should NOT apply to the contoured data.", False, True, None, None],

                   ["title", "t", "Title for the map (defaults to an empty string).", False, False, None, ""],
                   ["no-density", "p", "Remove the surface density dependance on the colour units.", False, True, None, None],
                   ["no-log", "l", "Do not log the pixel values before applying colours.", False, True, None, None],
                   ["log-pre-intergration", None, "Do not log the pixel values before applying colours.", False, True, None, None],
                   ["image-size", "r", "Size of the (square) image in pixels (defaults to 1080px).", False, False, int, 1080],

                   ["colour-map", None, "Name of the colour map to use. Supports the avalible matplotlib colourmaps" + (", as well as those designed by Paul Tol (https://personal.sron.nl/~pault/).\nTo use a custom map, specify the colours in the format \"#RRGGBB\" as a semicolon seperated list (must have at least 2 values)." if TOL_AVAILABLE else ".\nTo add support for Paul Tol's colours, download the python file from https://personal.sron.nl/~pault/ and install using \"add-py tol_colors\".") + "\nDefaults to whatever is set by the stylesheet - usually \"twilight_shifted\".", False, False, ScriptWrapper.make_list_converter(";"), None],

                   *BoxRegion.get_command_params(use_abbriviation = False)
                  ]
    
    script = ScriptWrapper("sph_map.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["box_region.py (local file)", "console_log_printing.py (local file)", "enum", "matplotlib", "numpy", "os", "py-sphviewer", "script_wrapper.py (local file)", "swift_data_expression.py (local file)", "swiftsimio", "sys", "typing", "unyt"],
                           ["snapshot_file.hdf5 test.png --gas -r 1080 -x 10 -y 200"],
                           args_info,
                           kwargs_info)

    script.run(__main)
