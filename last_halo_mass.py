AUTHOR = "Christopher Rowe"
VERSION = "3.0.0"
DATE = "21/03/2023"
DESCRIPTION = "Creates a gas temperature-density diagram coloured by the mass of the last encountered halo."



import os
import pickle
import swiftsimio as sw
import sys
from typing import List
import unyt

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from box_region import BoxRegion
from console_log_printing import print_info, print_debug
from gas_particle_line_graph import make_graph as gas_line_graph
from get_gas_crit_density import critical_gas_density
from script_wrapper import ScriptWrapper
from temp_density_diagram import make_diagram
from sph_map import make_plot, RenderType, PartType

def __main(directory: List[str], output_file, data: List[str], labels: List[str], colour_map, **kwargs):
    make_comparison_graphs = not isinstance(data, str) and len([data_file for data_file in data if data_file != ""]) > 1
    if isinstance(data, str):
        data = [data]
    data = [data_file for data_file in data if data_file != ""]
    if isinstance(directory, str):
        directory = [directory]
    if isinstance(labels, str):
        labels = [labels]
    if labels is None:
        labels = ["Data"]
    
    halo_masses_files = []
    for i in range(len(data)):
        halo_masses_files.append(os.path.join(directory[i], "gas_particle_ejection_tracking__halo_masses.pickle"))

    halo_mass_data_sets = []
    for i in range(len(data)):
        with open(halo_masses_files[i], "rb") as file:
            halo_mass_data_sets.append(pickle.load(file))

    snap_data = sw.load(data[0])
    snap_data.gas.last_halo_mass = unyt.array.unyt_array(halo_mass_data_sets[0], "Msun")
    box = BoxRegion(**BoxRegion.filter_command_params(**kwargs))
    box.complete_bounds_from_coords(snap_data.gas.coordinates)

    #make_diagram(particle_data = snap_data,
    #             output_file_path = output_file,
    #             colour_variable_name = "gas.last_halo_mass",
    #             colour_unit = "Msun",
    #             colour_name = "Halo Mass",
    #             log_colour = True,
    #             colour_weight = "gas.masses*gas.metal_mass_fractions",
    #             box_region = box,
    #             min_colour_value = 0,
    #             colour_map = colour_map)
    


    ##print_debug(box.side_length)
    ##snap_data.gas.last_halo_mass__zero_min = snap_data.gas.last_halo_mass
    ##snap_data.gas.last_halo_mass__zero_min[snap_data.gas.last_halo_mass__zero_min < 0.0] = 0.0
    #sw.Writer
    #sw.subset_writer
    #make_plot(particle_data = snap_data,
    #          output_file = "map_last_enrichment_halo_mass.png",
    #          box_region = box,
    #          parttype = PartType.gas,
    #          x = box.centre[0],
    #          y = box.centre[1],
    #          z = box.centre[2],
    #          render_type = RenderType.projection,
    #          projection_width = (box.side_length[0] if isinstance(box.side_length, list) else box.side_length) / 2,
    #          smoothing_attr = "gas.last_halo_mass",
    #          smoothing_unit = "Msun",
    #          filter_attr = "gas.last_halo_mass",
    #          filter_unit = "Msun",
    #          filter_min = 0.000000001,
    #          contour = "gas.masses",
    #          exclude_filter_from_contour = True,
    #          no_density = True)
    


    

    snap_data_objects = [snap_data]
    critical_g_rho_values = [str(critical_gas_density(snap_data, unit = "Msun/Mpc**3"))]
    for i in range(1, len(data)):
        snap_data_objects.append(sw.load(data[i]))
        snap_data_objects[-1].gas.last_halo_mass = unyt.array.unyt_array(halo_mass_data_sets[i], "Msun")
        critical_g_rho_values.append(str(critical_gas_density(snap_data_objects[-1], unit = "Msun/Mpc**3")))
    


    # Metal Mass Fraction

    #    make_diagram(particle_data = snap_data,
#                 output_file_path = "plot_temp_dens_metal_mass_fraction.png",
#                 colour_variable_name = "gas.metal_mass_fractions",
#                 colour_unit = "",
#                 colour_name = "$M_Z/M$",
#                 min_colour_value = 0,
#                 log_colour = True,
#                 box_region = box,
#                 colour_map = colour_map)
    
    #print()
    #print_info("Metal Mass Fraction vs. Density")
    #gas_line_graph(particle_data_list = [snap_data],
    #               data_name_list = ["Data"],
    #               output_file_path = "plot_dens_metal_mass_fraction.png",
    #               x_axis_field = f"densities/#<{critical_g_rho_values[0]}>#",
    #               x_axis_unit = "",
    #               x_axis_name = "$\\rho$/<$\\rho$>",
    #               log_x_axis = True,
    #               y_axis_field = "metal_mass_fractions",
    #               y_axis_unit = "",
    #               y_axis_name = "$M_Z/M$",
    #               min_y_field_value = 0,
    #               log_y_axis = True,
    #               box_region = box,
    #               show_errors = True)
    
    #if make_comparison_graphs:
    #    print()
    #    print_info("Metal Mass Fraction vs. Density (Comparison)")
    #    gas_line_graph(particle_data_list = snap_data_objects,
    #                   data_name_list = labels,
    #                   output_file_path = "plot_dens_metal_mass_fraction_comparison.png",
    #                   x_axis_field = [f"densities/#<{critical_g_rho_values[i]}>#" for i in range(len(data))],
    #                   x_axis_unit = "",
    #                   x_axis_name = "$\\rho$/<$\\rho$>",
    #                   log_x_axis = True,
    #                   y_axis_field = "metal_mass_fractions",
    #                   y_axis_unit = "",
    #                   y_axis_name = "$M_Z/M$",
    #                   min_y_field_value = 0,
    #                   log_y_axis = True,
    #                   box_region = box,
    #                   show_errors = True)
    
    #print()
    #print_info("Metal Mass Fraction T-rho (Only for particles found in halos)")
    #make_diagram(particle_data = snap_data,
    #             output_file_path = "plot_temp_dens_metal_mass_fraction_only_halo_matches.png",
    #             colour_variable_name = "gas.metal_mass_fractions",
    #             colour_unit = "",
    #             colour_name = "$M_Z/M$",
    #             min_colour_value = 0,
    #             log_colour = True,
    #             box_region = box,
    #             limit_fields = ["gas.last_halo_mass"],
    #             limit_units = ["Msun"],
    #             limits_min = [0],
    #             colour_map = colour_map)
    
    #print()
    #print_info("Metal Mass Fraction vs. Density (Only for particles found in halos)")
    #gas_line_graph(particle_data_list = [snap_data],
    #               data_name_list = ["Data"],
    #               output_file_path = "plot_dens_metal_mass_fraction_only_halo_matches.png",
    #               x_axis_field = f"densities/#<{critical_g_rho_values[0]}>#",
    #               x_axis_unit = "",
    #               x_axis_name = "$\\rho$/<$\\rho$>",
    #               log_x_axis = True,
    #               y_axis_field = "metal_mass_fractions",
    #               y_axis_unit = "",
    #               y_axis_name = "$M_Z/M$",
    #               min_y_field_value = 0,
    #               log_y_axis = True,
    #               box_region = box,
    #               limit_fields = ["last_halo_mass"],
    #               limit_units = ["Msun"],
    #               limits_min = [0],
    #               show_errors = True)
    
    #if make_comparison_graphs:
    #    print()
    #    print_info("Metal Mass Fraction vs. Density (Only for particles found in halos - Comparison)")
    #    gas_line_graph(particle_data_list = snap_data_objects,
    #                   data_name_list = labels,
    #                   output_file_path = "plot_dens_metal_mass_fraction_only_halo_matches_comparison.png",
    #                   x_axis_field = [f"densities/#<{critical_g_rho_values[i]}>#" for i in range(len(data))],
    #                   x_axis_unit = "",
    #                   x_axis_name = "$\\rho$/<$\\rho$>",
    #                   log_x_axis = True,
    #                   y_axis_field = "metal_mass_fractions",
    #                   y_axis_unit = "",
    #                   y_axis_name = "$M_Z/M$",
    #                   min_y_field_value = 0,
    #                   log_y_axis = True,
    #                   box_region = box,
    #                   limit_fields = ["last_halo_mass"],
    #                   limit_units = ["Msun"],
    #                   limits_min = [0],
    #                   show_errors = True)
    
    #print()
    #print_info("Metal Mass Fraction T-rho (Only for halos > 10**10)")
    #make_diagram(particle_data = snap_data,
    #             output_file_path = "plot_temp_dens_metal_mass_fraction_no_dwarfs.png",
    #             colour_variable_name = "gas.metal_mass_fractions",
    #             colour_unit = "",
    #             colour_name = "$M_Z/M$",
    #             min_colour_value = 0,
    #             log_colour = True,
    #             box_region = box,
    #             limit_fields = ["gas.last_halo_mass"],
    #             limit_units = ["Msun"],
    #             limits_min = [10**10],
    #             colour_map = colour_map)
    
    #print()
    #print_info("Metal Mass Fraction vs. Density (Only for halos > 10**10)")
    #gas_line_graph(particle_data_list = [snap_data],
    #               data_name_list = ["Data"],
    #               output_file_path = "plot_dens_metal_mass_fraction_no_dwarfs.png",
    #               x_axis_field = f"densities/#<{critical_g_rho_values[0]}>#",
    #               x_axis_unit = "",
    #               x_axis_name = "$\\rho$/<$\\rho$>",
    #               log_x_axis = True,
    #               y_axis_field = "metal_mass_fractions",
    #               y_axis_unit = "",
    #               y_axis_name = "$M_Z/M$",
    #               min_y_field_value = 0,
    #               log_y_axis = True,
    #               box_region = box,
    #               limit_fields = ["last_halo_mass"],
    #               limit_units = ["Msun"],
    #               limits_min = [10**10],
    #               show_errors = True)
    
    #if make_comparison_graphs:
    #    print()
    #    print_info("Metal Mass Fraction vs. Density (Only for halos > 10**10 - Comparison)")
    #    gas_line_graph(particle_data_list = snap_data_objects,
    #                   data_name_list = labels,
    #                   output_file_path = "plot_dens_metal_mass_fraction_no_dwarfs_comparison.png",
    #                   x_axis_field = [f"densities/#<{critical_g_rho_values[i]}>#" for i in range(len(data))],
    #                   x_axis_unit = "",
    #                   x_axis_name = "$\\rho$/<$\\rho$>",
    #                   log_x_axis = True,
    #                   y_axis_field = "metal_mass_fractions",
    #                   y_axis_unit = "",
    #                   y_axis_name = "$M_Z/M$",
    #                   min_y_field_value = 0,
    #                   log_y_axis = True,
    #                   box_region = box,
    #                   limit_fields = ["last_halo_mass"],
    #                   limit_units = ["Msun"],
    #                   limits_min = [10**10],
    #                   show_errors = True)
        


if __name__ == "__main__":
    args_info = [
                 ["directory", "Path to the directory containing the tracked halo masses file.", ScriptWrapper.make_list_converter(";")],
                 ["output_file", "Name (or relitive file path) to store the resulting image.", None],
                 ["data", "Path to the SWIFT data file.", ScriptWrapper.make_list_converter(";")]
                ]

    kwargs_info = [
                   ["labels", None, "Labels for line graphs when comparason snapshots are provided.", False, False, ScriptWrapper.make_list_converter(";"), None],
                   *BoxRegion.get_command_params(),
                   ["colour-map", None, "Name of the colour map to use.\nSee the help info for the density temp map for further info.", False, False, ScriptWrapper.make_list_converter(";"), None]
                  ]
    
    script = ScriptWrapper("find_gas_last_halo_masses.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["box_region.py (local file)", "console_log_printing.py (local file)", "os", "pickle", "script_wrapper.py (local file)", "swiftsimio", "sys", "temp_diagram.py (local file)", "unyt"],
                           ["./ out.png /path/to/data.hdf5 -x 100 -y 50 -w 10 --z_side_length inf"],
                           args_info,
                           kwargs_info)

    script.run(__main)
