AUTHOR = "Christopher Rowe"
VERSION = "1.1.0"
DATE = "26/06/2023"
DESCRIPTION = "Plots the cumulitive sum of metal masses for particles in assending order of last halo mass."

import swiftsimio as sw
import numpy as np
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from matplotlib import pyplot as plt

source_file_relitive_add_to_path(__file__)
from get_gas_crit_density import critical_gas_density

def __main(data: str, filename: str, include_non_metals: bool, include_non_metal_mass: bool, self_normalise_comparisons: bool):
    # Read data
    snap = sw.load(data)
    m200 = snap.gas.last_halo_masses.to("Msun")
    masses = snap.gas.masses.to("Msun")
    metalicities = snap.gas.metal_mass_fractions
    densities = np.log10(snap.gas.densities.to("Msun/Mpc**3") / critical_gas_density(snap, "Msun/Mpc**3"))
#    metal_masses = masses * metalicities

    if not include_non_metals:
        metal_filter = metalicities > 0
        m200 = m200[metal_filter]
        masses = masses[metal_filter]
        metalicities = metalicities[metal_filter]
        densities = densities[metal_filter]

    first_reliable_data_index = m200[m200 > 0].argmin()

    # Set minimum halo values for untracked data
    #m200[m200 <= 0] = 10**np.array(np.log10(m200[m200 > 0].min())) + np.linspace(0, 100, (m200 <= 0).sum(), dtype = int)
    m200[m200 <= 0] = m200[m200 > 0].min() / 10

    log_m200 = np.log10(m200)

    # Compute halo mass order of particles
    sorted_indexes = np.argsort(log_m200)
    first_reliable_data_sorted_index = np.linspace(0, sorted_indexes.shape[0] - 1, sorted_indexes.shape[0], dtype = int)[sorted_indexes == first_reliable_data_index][0]
    #TODO: print and check this!!!
    
    # Calculate the cumulitive sum for all particles
    target_masses = masses if include_non_metal_mass else masses * metalicities
    cumulitive_target_masses = np.cumsum(target_masses[sorted_indexes])
    y_max = cumulitive_target_masses[-1]

    particle_densities_sorted = densities[sorted_indexes]
    density_cuttoffs = (0, 2.5, 7.5)
    density_filters = [particle_densities_sorted >= cuttof for cuttof in density_cuttoffs]

    particle_metalicities_sorted = metalicities[sorted_indexes]
    metalicity_cuttoffs = (0.001, 0.0134, 0.1, 0.3)# Z_sun = ~0.0134
    metalicity_cuttoff_label_values = (0.001, "Z_\\odot", 0.1, 0.3)# Z_sun = ~0.0134
    metalicity_filters = [particle_metalicities_sorted >= cuttof for cuttof in metalicity_cuttoffs]

    plotted_x_values = log_m200[sorted_indexes]
    plotted_y_values = cumulitive_target_masses / y_max

    plt.plot(plotted_x_values, plotted_y_values, label = "All Data")

    for i, density_filter in enumerate(density_filters):
        filtered_cululitive_sum = np.cumsum(target_masses[sorted_indexes][density_filter])
        if filtered_cululitive_sum.shape[0] > 0:
            plt.plot(plotted_x_values[density_filter], filtered_cululitive_sum / (filtered_cululitive_sum[-1] if self_normalise_comparisons else y_max), label = f"$\\rho >= {density_cuttoffs[i]}$")
    for i, metalicity_filter in enumerate(metalicity_filters):
        filtered_cululitive_sum = np.cumsum(target_masses[sorted_indexes][metalicity_filter])
        if filtered_cululitive_sum.shape[0] > 0:
            plt.plot(plotted_x_values[metalicity_filter], filtered_cululitive_sum / (filtered_cululitive_sum[-1] if self_normalise_comparisons else y_max), label = f"$Z >= {metalicity_cuttoff_label_values[i]}$")
    plt.legend()

    plt.title("Cumulitive Partical {}Mass Fraction\n(for particles with an identified last halo)".format("" if include_non_metal_mass else "Metal-"))
    
    ax = plt.gca()

    x_limits = (plotted_x_values[0], plotted_x_values[-1])

    def plot_division_line(m):
        x = log_m200[sorted_indexes][cumulitive_target_masses >= m][0]
        y = m / y_max
        ax.plot(x_limits, (y, y), color = "red", alpha = 0.3, linestyle = "--")
        ax.plot((x, x), (0, y), color = "red", alpha = 0.3, linestyle = "--")
    plot_division_line(y_max * 0.25)
    plot_division_line(y_max * 0.5)
    plot_division_line(y_max * 0.75)
    ax.set_xlim(x_limits)

    ax.set_xlabel("$\\rm log_{10}$ $M_{200}$ of last halo ($\\rm M_\\odot$)")
    ax.set_ylabel("Cumulitive Mass Fraction")
    ax.set_ylim((0, 1))

    plt.savefig(filename)

#    initial_lower_ylim = ax.get_ylim()[0]
#    print(float(plotted_x_values[first_reliable_data_sorted_index]), float(plotted_y_values[first_reliable_data_sorted_index]) + float(plotted_y_values[first_reliable_data_sorted_index]), 0.0, -float(plotted_y_values[first_reliable_data_sorted_index]))
#    plt.arrow(float(plotted_x_values[first_reliable_data_sorted_index]), float(plotted_y_values[first_reliable_data_sorted_index]) + float(plotted_y_values[first_reliable_data_sorted_index]), 0.0, -float(plotted_y_values[first_reliable_data_sorted_index]))
#    
#    def plot_division_line(m):
#        x = log_m200[sorted_indexes][cumulitive_metal_masses >= m][0]
#        y = np.log10(m) if log_y else m
#        ax.plot(x_limits, (y, y), color = "red", alpha = 0.3, linestyle = "--")
#        ax.plot((x, x), (0 if not log_y else initial_lower_ylim, y), color = "red", alpha = 0.3, linestyle = "--")
#    plot_division_line(cumulitive_metal_masses[-1] * 0.25)
#    plot_division_line(cumulitive_metal_masses[-1] * 0.5)
#    plot_division_line(cumulitive_metal_masses[-1] * 0.75)
#    ax.set_xlim(x_limits)
#    ax.set_xlabel("$\\rm log_{10}$ $M_{200}$ of last halo ($\\rm M_\\odot$)")
#    axis_scale_insert = "$\\rm log_{10}$ " if log_y else ""
#    ax.set_ylabel(f"{axis_scale_insert}$M_{{\\rm Z}}$ ($\\rm M_\\odot$)")
#    ax.set_ylim((0, y_max) if not log_y else (initial_lower_ylim, np.log10(y_max)))
#    ax.tick_params(axis = "y")
#
#    
#    ax_normalised = ax.twinx()# Set the limits and ticks for the second y-axis
#    if log_y:
#        ax_tick_positions = ax.get_yticks()
#        actual_y_lims = ax.get_ylim()
#        ax_tick_positions = ax_tick_positions[(ax_tick_positions >= actual_y_lims[0]) & (ax_tick_positions <= actual_y_lims[1])]
#        ax_relitive_tick_positions = (ax_tick_positions - actual_y_lims[0]) / (actual_y_lims[1] - actual_y_lims[0])
#        ax_normalised.set_yticks(ax_relitive_tick_positions)
#        ax_normalised.set_yticklabels([f"{value:.1e}" for value in 10**ax_tick_positions / y_max])
#        print(ax_relitive_tick_positions)
#        print([f"{value:.1e}" for value in 10**ax_tick_positions / y_max])
#    ax_normalised.set_ylim((0 if not log_y else (10**ax.get_ylim()[0] / y_max), 1))
#    ax_normalised.set_ylabel("Cumulitive Fraction")
#    ax_normalised.tick_params(axis = "y")
#        
#    plt.savefig(filename)


if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the modified present day SWIFT data file.", None],
                 ["filename", "Output file name.", None]
                ]
    kwargs_info = [["include_non_metal_mass", "e", "", False, True, None, None],
                   ["include-non-metals", "m", "Include particals with no metallicity.", False, True, None, None],
                   ["self-normalise-comparisons", "n", "Normalise the comparison lines by their own total sum\nas opposed to by the total of the whole dataset.", False, True, None, None]]
    
    script = ScriptWrapper("plot_cumulitive_metal_contribution_mass.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           [],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
