AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "22/05/2023"
DESCRIPTION = "Plots the cumulitive sum of metal masses for particles in assending order of last halo mass."

import swiftsimio as sw
import numpy as np
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from matplotlib import pyplot as plt

def __main(data: str, filename: str, log_y: bool):
    snap = sw.load(data)
    m200 = snap.gas.last_halo_masses.to("Msun")
    masses = snap.gas.masses.to("Msun")
    metalicities = snap.gas.metal_mass_fractions

    halo_filter = m200 != -1.000003
    log_m200 = np.log10(m200[halo_filter])

    sorted_indexes = np.argsort(log_m200)

    metal_masses = masses[halo_filter] * metalicities[halo_filter]
    cumulitive_metal_masses = np.cumsum(metal_masses[sorted_indexes])
    y_max = cumulitive_metal_masses[-1]

    plotted_x_values = log_m200[sorted_indexes]
    plotted_y_values = np.log10(cumulitive_metal_masses) if log_y else cumulitive_metal_masses

    plt.plot(plotted_x_values, plotted_y_values)
    plt.title("Cumulitive Partical Metal Mass\n(for particles with an identified last halo)")

    ax = plt.gca()
    x_limits = (plotted_x_values[0], plotted_x_values[-1])
    initial_lower_ylim = ax.get_ylim()[0]
    def plot_division_line(m):
        x = log_m200[sorted_indexes][cumulitive_metal_masses >= m][0]
        y = np.log10(m) if log_y else m
        ax.plot(x_limits, (y, y), color = "red", alpha = 0.3, linestyle = "--")
        ax.plot((x, x), (0 if not log_y else initial_lower_ylim, y), color = "red", alpha = 0.3, linestyle = "--")
    plot_division_line(cumulitive_metal_masses[-1] * 0.25)
    plot_division_line(cumulitive_metal_masses[-1] * 0.5)
    plot_division_line(cumulitive_metal_masses[-1] * 0.75)
    ax.set_xlim(x_limits)
    ax.set_xlabel("$\\rm log_{10}$ $M_{200}$ of last halo ($\\rm M_\\odot$)")
    axis_scale_insert = "$\\rm log_{10}$ " if log_y else ""
    ax.set_ylabel(f"{axis_scale_insert}$M_{{\\rm Z}}$ ($\\rm M_\\odot$)")
    ax.set_ylim((0, y_max) if not log_y else (initial_lower_ylim, np.log10(y_max)))
    ax.tick_params(axis = "y")

    
    ax_normalised = ax.twinx()# Set the limits and ticks for the second y-axis
    if log_y:
        ax_tick_positions = ax.get_yticks()
        actual_y_lims = ax.get_ylim()
        ax_tick_positions = ax_tick_positions[(ax_tick_positions >= actual_y_lims[0]) & (ax_tick_positions <= actual_y_lims[1])]
        ax_relitive_tick_positions = (ax_tick_positions - actual_y_lims[0]) / (actual_y_lims[1] - actual_y_lims[0])
        ax_normalised.set_yticks(ax_relitive_tick_positions)
        ax_normalised.set_yticklabels([f"{value:.1e}" for value in 10**ax_tick_positions / y_max])
        print(ax_relitive_tick_positions)
        print([f"{value:.1e}" for value in 10**ax_tick_positions / y_max])
    ax_normalised.set_ylim((0 if not log_y else (10**ax.get_ylim()[0] / y_max), 1))
    ax_normalised.set_ylabel("Cumulitive Fraction")
    ax_normalised.tick_params(axis = "y")
        
    plt.savefig(filename)


if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the modified present day SWIFT data file.", None],
                 ["filename", "Output file name.", None]
                ]
    kwargs_info = [["log-y", "l", "Log the Y-axis", False, True, None, None]]
    
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
