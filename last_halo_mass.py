AUTHOR = "Christopher Rowe"
VERSION = "1.2.0"
DATE = "02/02/2023"
DESCRIPTION = "Creates a gas temperature-density diagram coloured by the mass of the last encountered halo."

import os
import pickle
import swiftsimio as sw
import sys
import unyt

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from box_region import BoxRegion
from script_wrapper import ScriptWrapper
from temp_density_diagram import make_diagram

def __main(directory, output_file, data, colour_map, **kwargs):
    halo_masses_file = os.path.join(directory, "gas_particle_ejection_tracking__halo_masses.pickle")

    halo_mass_data = None
    with open(halo_masses_file, "rb") as file:
        halo_mass_data = pickle.load(file)

    snap_data = sw.load(data)
    snap_data.gas.last_halo_mass = unyt.array.unyt_array(halo_mass_data, "Msun")
    box = BoxRegion(**BoxRegion.filter_command_params(**kwargs))

    make_diagram(particle_data = snap_data,
                 output_file_path = output_file,
                 colour_variable_name = "gas.last_halo_mass",
                 colour_unit = "Msun",
                 colour_name = "Halo Mass",
                 log_colour = True,
                 colour_weight = "gas.masses*gas.metal_mass_fractions",
                 box_region = box,
                 min_colour_value = 0,
                 colour_map = colour_map)

if __name__ == "__main__":
    args_info = [
                 ["directory", "Path to the directory containing the tracked halo masses file.", None],
                 ["output_file", "Name (or relitive file path) to store the resulting image.", None],
                 ["data", "Path to the SWIFT data file.", None]
                ]

    kwargs_info = [
                   *BoxRegion.get_command_params(),
                   ["colour-map", None, "Name of the colour map to use.\nSee the help info for the density temp map for further info.", False, False, str, None]
                  ]
    
    script = ScriptWrapper("find_gas_last_halo_masses.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["box_region.py (local file)", "os", "pickle", "script_wrapper.py (local file)", "swiftsimio", "sys", "temp_diagram.py (local file)", "unyt"],
                           ["./ out.png /path/to/data.hdf5 -x 100 -y 50 -w 10 --z_side_length inf"],
                           args_info,
                           kwargs_info)

    script.run(__main)
