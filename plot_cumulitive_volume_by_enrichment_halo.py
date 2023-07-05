AUTHOR = "Christopher Rowe"
VERSION = "1.1.0"
DATE = "26/06/2023"
DESCRIPTION = "Plots the cumulitive sum of particle volume (as a fraction of the total) for particles in assending order of last halo mass."

import swiftsimio as sw
import numpy as np
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from matplotlib import pyplot as plt

source_file_relitive_add_to_path(__file__)
from get_gas_crit_density import critical_gas_density

def __main(data: str, filename: str, include_non_metals: bool, self_normalise_comparisons: bool):
    # Read data
    snap = sw.load(data)
    m200 = snap.gas.last_halo_masses.to("Msun")
    volume_residuals = snap.gas.smoothing_lengths.to("Mpc")**3# h_i**3 / sum(h_i**3) = (4/3 pi * h_i**3) / sum(4/3 pi * h_i**3)
    metalicities = snap.gas.metal_mass_fractions
    densities = np.log10(snap.gas.densities.to("Msun/Mpc**3") / critical_gas_density(snap, "Msun/Mpc**3"))
    metal_masses = snap.gas.masses.to("Msun") * metalicities

    ## Set minimum halo values for untracked data
    #m200[m200 <= 0] = 10E5 + np.linspace(0, 100, (m200 <= 0).sum())
    # Remove untracked particles
    tracked_filter = m200 >= 0
    m200 = m200[tracked_filter]
    volume_residuals = volume_residuals[tracked_filter]
    metalicities = metalicities[tracked_filter]
    densities = densities[tracked_filter]
    metal_masses = metal_masses[tracked_filter]

    log_m200 = np.log10(m200)
    if not include_non_metals:
        record_filter = metalicities > 0

        log_m200 = log_m200[record_filter]
        volume_residuals = volume_residuals[record_filter]
        metalicities = metalicities[record_filter]
        densities = densities[record_filter]
        metal_masses = metal_masses[record_filter]

    # Compute halo mass order of particles
    sorted_indexes = np.argsort(log_m200)

    cumulitive_volume_residuals = np.cumsum(volume_residuals[sorted_indexes])
    y_max = cumulitive_volume_residuals[-1]

    particle_densities_sorted = densities[sorted_indexes]
    density_cuttoffs = (0, 2.5, 7.5)
    density_filters = [particle_densities_sorted >= cuttof for cuttof in density_cuttoffs]

    particle_metalicities_sorted = metalicities[sorted_indexes]
    metalicity_cuttoffs = (0.001, 0.0134, 0.1, 0.3)# Z_sun = ~0.0134
    metalicity_cuttoff_label_values = (0.001, "Z_\\odot", 0.1, 0.3)# Z_sun = ~0.0134
    metalicity_filters = [particle_metalicities_sorted >= cuttof for cuttof in metalicity_cuttoffs]

    plotted_x_values = log_m200[sorted_indexes]
    plotted_y_values = cumulitive_volume_residuals / y_max

    plt.plot(plotted_x_values, plotted_y_values, label = "All Data")

    for i, density_filter in enumerate(density_filters):
        filtered_cululitive_sum = np.cumsum(volume_residuals[sorted_indexes][density_filter])
        if filtered_cululitive_sum.shape[0] > 0:
            plt.plot(plotted_x_values[density_filter], filtered_cululitive_sum / (filtered_cululitive_sum[-1] if self_normalise_comparisons else y_max), label = f"$\\rho >= {density_cuttoffs[i]}$")
    for i, metalicity_filter in enumerate(metalicity_filters):
        filtered_cululitive_sum = np.cumsum(volume_residuals[sorted_indexes][metalicity_filter])
        if filtered_cululitive_sum.shape[0] > 0:
            plt.plot(plotted_x_values[metalicity_filter], filtered_cululitive_sum / (filtered_cululitive_sum[-1] if self_normalise_comparisons else y_max), label = f"$Z >= {metalicity_cuttoff_label_values[i]}$")
    plt.legend()

    plt.title("Cumulitive Partical Volume Fraction\n(for particles with an identified last halo{})".format("" if include_non_metals else " & a metal component"))

    ax = plt.gca()
    
    x_limits = (plotted_x_values[0], plotted_x_values[-1])


    #def sigmoid(x, centre_x = 0, height_scale = 1):
    #    return 1 / (1 + np.exp(-(x - centre_x) * height_scale))
    #curve_x = np.linspace(*x_limits, 1000)
    #curve_halfway_point = plotted_x_values[cumulitive_volume_residuals >= y_max * 0.5][0]
    #plt.plot(curve_x, sigmoid(curve_x, curve_halfway_point, 4), label = "Sigmoid")
    #plt.legend()


    def plot_division_line(v):
        x = log_m200[sorted_indexes][cumulitive_volume_residuals >= v][0]
        y = v / y_max
        ax.plot(x_limits, (y, y), color = "red", alpha = 0.3, linestyle = "--")
        ax.plot((x, x), (0, y), color = "red", alpha = 0.3, linestyle = "--")
    plot_division_line(y_max * 0.25)
    plot_division_line(y_max * 0.5)
    plot_division_line(y_max * 0.75)
    ax.set_xlim(x_limits)
    ax.set_xlabel("$\\rm log_{10}$ $M_{200}$ of last halo ($\\rm M_\\odot$)")
    
    ax.set_ylim((0, 1))
    ax.set_ylabel("Cumulitive Volume Fraction")
    
    plt.savefig(filename)


if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the modified present day SWIFT data file.", None],
                 ["filename", "Output file name.", None]
                ]
    kwargs_info = [["include-non-metals", "m", "Include particals with no metallicity.", False, True, None, None],
                   ["self-normalise-comparisons", "n", "Normalise the comparison lines by their own total sum\nas opposed to by the total of the whole dataset.", False, True, None, None]]
    
    script = ScriptWrapper("plot_cumulitive_volume_by_enrichment_halo.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           [],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
