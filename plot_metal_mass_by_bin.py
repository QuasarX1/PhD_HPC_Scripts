AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "22/05/2023"
DESCRIPTION = "Plots the fraction of metal mass occupied by each log halo mass bin."

import swiftsimio as sw
import h5py
import numpy as np
import os
import pickle
from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_warning, print_debug
from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
import sys
from unyt import unyt_array
from matplotlib import pyplot as plt

source_file_relitive_add_to_path(__file__)

def load_data(file):
    snap = sw.load(file)

    #sfr_filter = snap.gas.star_formation_rates == 0

    m200 = snap.gas.last_halo_masses.to("Msun")#[sfr_filter]
    masses = snap.gas.masses.to("Msun")#[sfr_filter]
    metalicities = snap.gas.metal_mass_fractions#[sfr_filter]

    return m200, masses, metalicities

def bin_data(m200, masses, metalicities):
    metal_masses = masses * metalicities
    total_metal_mass = np.sum(metal_masses)

    filter_non_tracked_haloes = m200 == -1.000003
    filter_only_tracked_haloes = m200 != -1.000003

    log_m200_int = np.array(np.log10(m200[filter_only_tracked_haloes]), dtype = int)
    bins = np.unique(log_m200_int)

    def bin_fraction(particle_metal_masses):
        return np.sum(particle_metal_masses) / total_metal_mass

    untracked_fraction = bin_fraction(metal_masses[filter_non_tracked_haloes])
    bin_fractions = [bin_fraction(metal_masses[filter_only_tracked_haloes][log_m200_int == bins[i]]) for i in range(len(bins))]

    return bins, untracked_fraction, bin_fractions

def __main(data: str, filename: str, comparison_data: list, all_labels: list):
    # Load data
    m200, masses, metalicities = load_data(data)
    comparison_data = []
    for dataset in comparison_data:
        comparison_data.append(load_data(dataset))

    # Bin data
    bins, untracked_fraction, bin_fractions = bin_data(m200, masses, metalicities)
    binned_comparison_data = []
    for comparison_dataset in comparison_data:
        binned_comparison_data.append(bin_data(*comparison_dataset))

    n_bars_per_bin = len(comparison_data) + 1

    # Format data for plotting
    if len(all_labels) == 0 or (all_labels[0] == "" and n_bars_per_bin == 1):
        all_labels[0] = None
    elif n_bars_per_bin > 1:
        all_labels[0] = "Data"
    dataset_labels = all_labels# Change of variable name for clarity

    unique_bin_values = np.unique(np.append(bins, [binned_comparison_data[0] for i in range(len(binned_comparison_data))]))
    bin_labels = ["Untracked", *[f"$10^{{{bin_value}}}$" for bin_value in unique_bin_values]]
    n_bins = len(bin_labels)

    heights_by_bin = [[untracked_fraction, *[binned_comparison_data[i][1] for i in range(n_bars_per_bin - 1)]]]
    for bin_value in unique_bin_values:
        heights_by_bin.append([])
        for dataset_index in range(-1, n_bars_per_bin - 1):
            if dataset_index == -1:
                if bin_value in bins:
                    heights_by_bin[-1].append(bin_fractions[bins == bin_value][0])
                else:
                    heights_by_bin[-1].append(-1)
            else:
                if bin_value in binned_comparison_data[dataset_index][0]:
                    heights_by_bin[-1].append(binned_comparison_data[dataset_index][2][bins == bin_value][0])
                else:
                    heights_by_bin[-1].append(-1)

    # Plot data
    bar_colours = []
    dataset_label_check = np.full(len(dataset_labels), True)
    dataset_label_indexes = np.linspace(0, len(dataset_labels), endpoint = False)
    for i, label in enumerate(bin_labels):
            for _, (height, dataset_label_index, colour) in enumerate(sorted(zip(heights_by_bin[i], dataset_label_indexes, bar_colours), reverse = True, key = lambda x: x[0])):
                if height != -1:
                    plt.bar("Untracked", height, color = colour, label = dataset_labels[dataset_label_index] if dataset_label_check[dataset_label_index] else None)

        







    
    #bar_colours = None#TODO:
    #
    #for _, (height, label, colour) in enumerate(sorted(zip([untracked_fraction, *[binned_comparison_data[i][1] for i in range(len(binned_comparison_data))]], all_labels, bar_colours), reverse = True, key = lambda x: x[0])):
    #    plt.bar("Untracked", height, color = colour, label = label)
    #
    #for bin_value in all_bin_values:
    #    zip(bin_fractions, )
    #    plt.bar(f"$10^{{{bin_value}}}$", height, color = colour, label = label)
    #
    ##plt.bar(["Untracked", *[f"$10^{{{bin_value}}}$" for bin_value in bins]], [untracked_fraction, *bin_fractions], label = all_labels[0] if (len(all_labels) > 0 and (all_labels[0] != "" or len(comparison_data) == 0)) else "Data", alpha = 1.0 if len(comparison_data) == 0 else 0.4)
    ##for i, binned_comparison_dataset in enumerate(comparison_data):
    ##    plt.bar(["Untracked", *[f"$10^{{{bin_value}}}$" for bin_value in bins]], [untracked_fraction, *bin_fractions], label = all_labels[i + 1], alpha = 0.4)

    plt.title("Fraction of all metal mass by last halo mass\n(bins contain data within the stated order of magnitude)")
    plt.xlabel("$M_{\\rm halo}$ ($\\rm M_\\odot$)")
    plt.ylabel("$M_{\\rm Z,bin}$ / $M_{\\rm Z}$")
    plt.savefig(filename)


if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the modified present day SWIFT data file.", None],
                 ["filename", "Output file name.", None]
                ]
    kwargs_info = [["comparison-data", "c", "Data to compare against. Semicolon seperated list.", False, False, ScriptWrapper.make_list_converter(";"), []],
                   ["all-labels", "l", "labels for all datasets. Semicolon seperated list.\nLeave first entry blank to use default label for the initial dataset.", False, False, ScriptWrapper.make_list_converter(";"), [""]]
                   ]
    
    script = ScriptWrapper("plot_metal_mass_by_bin.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           [],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
