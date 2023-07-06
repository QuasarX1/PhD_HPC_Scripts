AUTHOR = "Christopher Rowe"
VERSION = "2.0.0"
DATE = "06/07/2023"
DESCRIPTION = "Creates a histogram for the desnities of gas particles from a SWIFT snapshot."

from matplotlib import pyplot as plt
import numpy as np
import swiftsimio as sw
from typing import List, Union

from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.filters import BoxRegion
from contra.calculations import get_critical_gas_density as critical_gas_density
from contra.io.swift_data_expression import parse_string as make_attribute

def __main(data, output_file, log_y_axis: bool, limit_fields: List[str], limit_units: List[str], limits_min: List[float], limits_max: List[float], hist_metals: bool, sum_mass: bool, sum_metal_mass: bool, sum_volume: bool, sum_metal_volume: bool, use_line: bool, plot_unfiltered: bool, max_y: Union[float, None], **kwargs):
    nBins = 40

    plot_unfiltered = plot_unfiltered and use_line and limit_fields is not None

    box_region_object = BoxRegion(**kwargs)

    snap_data = sw.load(data)



    # Calculate spatial and specified filters
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
            field_value = make_attribute(field, snap_data.gas).to(limit_units[j])
            if limits_min is not None and limits_min[j] != "":
                manual_filter &= field_value >= limits_min[j]
            if limits_max is not None and limits_max[j] != "":
                manual_filter &= field_value <= limits_max[j]

    combined_data_filter = (array_filter & manual_filter)

    

    # Calculate weights and set nessessary labels
    unfiltered_weights = None
    weights = None
    weighting_data = None
    plot_title_insert = "Histogram"
    y_label = "Frequency"

    if hist_metals:
        metal_filter = snap_data.gas.metal_mass_fractions > 0
        plot_title_insert = "Histogram of Metals"

    elif sum_mass:
        if plot_unfiltered:
            unfiltered_weighting_data = snap_data.gas.masses.to("Msun")
            unfiltered_weights = unfiltered_weighting_data / unfiltered_weighting_data.sum()
        weighting_data = snap_data.gas.masses.to("Msun")[combined_data_filter]
        weights = weighting_data / (weighting_data.sum() if not plot_unfiltered else unfiltered_weighting_data.sum())
        plot_title_insert = "Normalised Mass Histogram"
        y_label = "Fraction of Total Mass" if not plot_unfiltered else "Fraction of Total Unfiltered Mass"

    elif sum_metal_mass:
        if plot_unfiltered:
            unfiltered_weighting_data = snap_data.gas.masses.to("Msun") * snap_data.gas.metal_mass_fractions
            unfiltered_weights = unfiltered_weighting_data / unfiltered_weighting_data.sum()
        weighting_data = snap_data.gas.masses.to("Msun")[combined_data_filter] * snap_data.gas.metal_mass_fractions[combined_data_filter]
        weights = weighting_data / (weighting_data.sum() if not plot_unfiltered else unfiltered_weighting_data.sum())
        plot_title_insert = "Normalised Metal Mass Histogram"
        y_label = "Fraction of Total Metal Mass" if not plot_unfiltered else "Fraction of Total Unfiltered Metal Mass"

    elif sum_volume:
        if plot_unfiltered:
            unfiltered_weighting_data = snap_data.gas.smoothing_lengths.to("Mpc")**3
            unfiltered_weights = unfiltered_weighting_data / unfiltered_weighting_data.sum()
        weighting_data = snap_data.gas.smoothing_lengths.to("Mpc")[combined_data_filter]**3
        weights = weighting_data / (weighting_data.sum() if not plot_unfiltered else unfiltered_weighting_data.sum())
        plot_title_insert = "Normalised Volume Histogram"
        y_label = "Fraction of Total Volume" if not plot_unfiltered else "Fraction of Total Unfiltered Volume"

    elif sum_metal_volume:
        metal_filter = snap_data.gas.metal_mass_fractions > 0
        if plot_unfiltered:
            unfiltered_weighting_data = snap_data.gas.smoothing_lengths.to("Mpc")[metal_filter]**3
            unfiltered_weights = unfiltered_weighting_data / unfiltered_weighting_data.sum()
        weighting_data = snap_data.gas.smoothing_lengths.to("Mpc")[metal_filter & combined_data_filter]**3
        weights = weighting_data / (weighting_data.sum() if not plot_unfiltered else unfiltered_weighting_data.sum())
        plot_title_insert = "Normalised Volume Histogram"
        y_label = "Fraction of Total Metal Enriched Volume" if not plot_unfiltered else "Fraction of Total Unfiltered Metal Enriched Volume"

    

    # Retrive density data
    critical_baryon_density = critical_gas_density(snap_data, unit = "Msun/Mpc**3")
    if plot_unfiltered:
        unfiltered_density_data = np.log10(snap_data.gas.densities.to("Msun/Mpc**3") / critical_baryon_density)
        if hist_metals or sum_metal_volume:
            unfiltered_density_data = unfiltered_density_data[metal_filter]
    density_data = np.log10(snap_data.gas.densities.to("Msun/Mpc**3")[combined_data_filter & metal_filter if hist_metals or sum_metal_volume else combined_data_filter] / critical_baryon_density)



    # Plot

    #stylesheet_directory = DirectoryTools.get_source_file_directory(__file__)
    #normal_stylesheet = os.path.join(stylesheet_directory, "temp_diagram_stylesheet.mplstyle")
    #plt.style.use(normal_stylesheet)

    if use_line:
        if plot_unfiltered and limit_fields is not None:
            counts, bin_edges = np.histogram(unfiltered_density_data, bins = nBins, weights = unfiltered_weights)
            bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2
            plt.plot(bin_centres, counts, label = "Unfiltered Data" if not sum_metal_volume else "All Metals")

        counts, bin_edges = np.histogram(density_data, bins = nBins, weights = weights)
        bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2
        plt.plot(bin_centres, counts, label = "Filtered Data" if plot_unfiltered and limit_fields is not None else None)

        if log_y_axis:
            plt.semilogy()
    else:
        plt.hist(density_data,
                bins = nBins,
                weights = weights,
                log = log_y_axis)

    if max_y is not None:
        plt.ylim((plt.ylim()[0], max_y))

    plt.xlabel("$\\rm log_{10}$ $\\rho$/<$\\rho$>")
    #plt.ylabel("$\\rm log_{10}$ Frequency" if log_y_axis else "Frequency")
    plt.ylabel(y_label)
    plt.title(f"Gas Particle {plot_title_insert} by Particle Density" + ("\nFiltered by field{}: {}".format("s" if len(limit_fields) > 1 else "", " ".join(limit_fields)) if limit_fields is not None else ""))
    if plot_unfiltered and limit_fields is not None:
        plt.legend()
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
                   ["hist-metals", None, "Histogram only the particles with metals.", False, True, None, None, ["sum-mass", "sum-metal-mass", "sum-volume", "sum-metal-volume"]],
                   ["sum-mass", "m", "Sum the particle mass instead of particle number. Produces a density histogram.", False, True, None, None, ["hist-metals", "sum-metal-mass", "sum-volume", "sum-metal-volume"]],
                   ["sum-metal-mass", "e", "Sum the metal mass instead of particle number. Produces a density histogram.", False, True, None, None, ["hist-metals", "sum-mass", "sum-volume", "sum-metal-volume"]],
                   ["sum-volume", "s", "Sum the particle volume instead of particle number. Produces a density histogram.", False, True, None, None, ["hist-metals", "sum-mass", "sum-metal-mass", "sum-metal-volume"]],
                   ["sum-metal-volume", "a", "Sum the particle volume associated with metal particles instead of particle number. Produces a density histogram.", False, True, None, None, ["hist-metals", "sum-mass", "sum-metal-mass", "sum-volume"]],
                   ["use-line", "l", "Use a line plot instead of bars.", False, True, None, None],
                   ["plot-unfiltered", None, "Plot a line for the unfiltered data.\nRequires the --use-line flag to be set and\nfor at least one filter to be specified.", False, True, None, None],
                   ["max-y", None, "Set the upper limit of the Y-axis.", False, False, float, None],
                   *BoxRegion.get_command_params()
                  ]
    
    script = ScriptWrapper("density_histogram.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["matplotlib", "numpy", "os", "QuasarCode", "swiftsimio", "typing"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
    