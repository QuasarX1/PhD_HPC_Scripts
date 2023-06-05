AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "02/06/2023"
DESCRIPTION = "Plots the cumulitive sum of particle volume (as a fraction of the total) for particles in assending order of last halo mass."

import swiftsimio as sw
import numpy as np
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from matplotlib import pyplot as plt

def __main(data: str, filename: str, include_non_metals: bool):
    snap = sw.load(data)
    m200 = snap.gas.last_halo_masses.to("Msun")
    volume_residuals = snap.gas.smoothing_lengths.to("Mpc")**3# h_i**3 / sum(h_i**3) = (4/3 pi * h_i**3) / sum(4/3 pi * h_i**3)
    metallicity = snap.gas.metal_mass_fractions

    record_filter = m200 != -1.000003
    if not include_non_metals:
        record_filter = record_filter & (metallicity > 0)
    log_m200 = np.log10(m200[record_filter])
    filtered_volume_residuals = volume_residuals[record_filter]

    sorted_indexes = np.argsort(log_m200)

    cumulitive_volume_residuals = np.cumsum(filtered_volume_residuals[sorted_indexes])
    y_max = cumulitive_volume_residuals[-1]

    plotted_x_values = log_m200[sorted_indexes]
    plotted_y_values = cumulitive_volume_residuals / y_max

    plt.plot(plotted_x_values, plotted_y_values)
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
    ax.set_ylabel("Cumulitive Fraction")
        
    plt.savefig(filename)


if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the modified present day SWIFT data file.", None],
                 ["filename", "Output file name.", None]
                ]
    kwargs_info = [["include-non-metals", "m", "Include particals with no metallicity.", False, True, None, None]]
    
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
