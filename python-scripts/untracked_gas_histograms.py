AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "12/07/2023"
DESCRIPTION = "Plots the cumulitive sum of metal masses for particles in assending order of last halo mass."

import swiftsimio as sw
import numpy as np
import swiftsimio as sw
from matplotlib import pyplot as plt

from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.calculations import get_critical_gas_density as critical_gas_density

def __main(data: str, only_metals: bool):
    n_bins = 40
    filename_base = "untracked_gas_distribution" if not only_metals else "untracked_metal_gas_distribution"

    # Read data
    snap = sw.load(data)
    data_filter = (snap.gas.last_halo_ids == -1) if not only_metals else ((snap.gas.last_halo_ids == -1) & (snap.gas.mean_metal_weighted_redshifts > 0))
    metalicities = np.log10(snap.gas.metal_mass_fractions[data_filter] + 1)
    densities = np.log10(snap.gas.densities.to("Msun/Mpc**3") / critical_gas_density(snap, "Msun/Mpc**3"))[data_filter]
    zZ = np.log10(snap.gas.mean_metal_weighted_redshifts[data_filter] + 1)
    temperatures = np.log10(snap.gas.temperatures[data_filter])

    hist, bin_edges = np.histogram(metalicities, n_bins)
    bin_centres = (bin_edges[1:] + bin_edges[:-1]) / 2
    plt.plot(bin_centres, hist)
    plt.xlabel("$\\rm log_{10}$ 1 + Metalicity (metal mass fraction)")
    plt.ylabel("N")
    plt.title("Untracked{} Gas Distribution (Z)".format("" if not only_metals else " Metal"), usetex = True)
    plt.savefig(f"{filename_base}_metalicity.png")
    plt.clf()

    hist, bin_edges = np.histogram(densities, n_bins)
    bin_centres = (bin_edges[1:] + bin_edges[:-1]) / 2
    plt.plot(bin_centres, hist)
    plt.xlabel("$\\rm log_{10}$ $\\rho$ / <$\\rm \\rho$>")
    plt.ylabel("N")
    plt.title("Untracked{} Gas Distribution ($\\rho$)".format("" if not only_metals else " Metal"), usetex = True)
    plt.savefig(f"{filename_base}_density.png")
    plt.clf()

    hist, bin_edges = np.histogram(zZ[zZ != -np.inf], n_bins)
    bin_centres = (bin_edges[1:] + bin_edges[:-1]) / 2
    plt.plot(bin_centres, hist)
    plt.xlabel("$\\rm log_{10}$ 1 + $z_{\\rm Z}$")
    plt.ylabel("N")
    plt.title("Untracked{} Gas Distribution ($z_{{\\rm Z}}$)".format("" if not only_metals else " Metal"), usetex = True)
    plt.savefig(f"{filename_base}_redshift.png")
    plt.clf()

    hist, bin_edges = np.histogram(temperatures, n_bins)
    bin_centres = (bin_edges[1:] + bin_edges[:-1]) / 2
    plt.plot(bin_centres, hist)
    plt.xlabel("$\\rm log_{10}$ Temperature (K)")
    plt.ylabel("N")
    plt.title("Untracked{} Gas Distribution (T)".format("" if not only_metals else " Metal"), usetex = True)
    plt.savefig(f"{filename_base}_temperature.png")
    plt.clf()



if __name__ == "__main__":
    args_info = [
                 ["data", "Path to the modified present day SWIFT data file.", None]
                ]
    kwargs_info = [["only-metals", "m", "Include only particals with nonzero metallicity.", False, True, None, None]]
    
    script = ScriptWrapper("untracked_gas_histograms.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           [],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
