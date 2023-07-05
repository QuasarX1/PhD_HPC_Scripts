#Aperture_mass_bh_30_kpc
AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "03/07/2023"
DESCRIPTION = "Plots black hole mass against halo stellar mass and fits a line.."

import h5py
import numpy as np
#from QuasarCode.IO.Text.console import Console.print_info
from QuasarCode import Console, source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper
import os
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import swiftsimio as sw
from unyt import unyt_array, unyt_quantity

source_file_relitive_add_to_path(__file__)
from velociraptor_multi_load import Multifile_VR_Catalogue

__PARTTYPE_NAMES = ("Dark Matter",
                    "Gas        ",
                    "Stars      ",
                    "Black Holes")
__PARTTYPE_NUMBERS = (1, 0, 4, 5)

def fitting_function(x, a, b, c):
    return (a * x**2) + (b * x) + c

def fit_data(x, y):
    popt, pcov = curve_fit(fitting_function, x, y)
    return popt

def plot_fit_line(x, popt, **kwargs):
    x_values = np.linspace(x.min(), x.max(), 1000)
    plt.plot(x_values, fitting_function(x_values, *popt), **kwargs)

def __main(filename, snapshot_files: list, catalogue_files: list, labels: list):
    if len(snapshot_files) != len(catalogue_files):
        raise ValueError("Inconsistent number of snapshot and catalogue files provided..")

    if len(labels) == 0 and len(catalogue_files) > 1 or len(labels) > 1 and len(labels) != len(catalogue_files):
        raise ValueError("Unable to match labels to datasets.")

    for i in range(len(snapshot_files)):
        snap_file = snapshot_files[i]
        cat_file = catalogue_files[i]

        # Load BH info from the snapshot (to get individual subgrid masses)
        snapshot = sw.load(snap_file)
        snap_bh_ids = snapshot.black_holes.particle_ids.value
        snap_bh_masses = snapshot.black_holes.subgrid_masses.to_value("Msun")

        # Open ALL catalogue files and read halo stellar masses
        folder_and_file = cat_file.rsplit(os.path.sep, maxsplit = 1)
        catalogue = Multifile_VR_Catalogue(folder_and_file[0] if len(folder_and_file) > 1 else ".", folder_and_file[-1].split(".", maxsplit = 1)[0])
#        cat_halo_ids = catalogue.ids.id.value.value
#        halo_m_star = np.log10(catalogue.masses.mass_star.value.to_value("Msun"))
        #m_bh = np.log10(catalogue.masses.mass_bh.value.to("Msun"))

        # Create mapping of BH particle id to halo id
        fields = catalogue.halo_properties_by_particle(["ids.id", "particle_ids", "masses.mass_star"], parttype = 5)
#        cat_halo_ids_by_particle = fields["ids.id"]
        cat_bh_ids = fields["particle_ids"]
        log_halo_m_star_by_particle = np.log10(fields["masses.mass_star"].to_value("Msun"))

        snap_filter__bh_particles_in_haloes = np.isin(snap_bh_ids, cat_bh_ids)
        sorted_indexes__cat_bh_ids = np.argsort(cat_bh_ids)
        inverse_sorted_indexes__cat_bh_ids = np.argsort(sorted_indexes__cat_bh_ids)
        sorted_indexes__filtered_snap_bh_ids = np.argsort(snap_bh_ids[snap_filter__bh_particles_in_haloes])

        logged_filtered_bh_masses__by_catalogue_order = np.log10(snap_bh_masses[snap_filter__bh_particles_in_haloes][sorted_indexes__filtered_snap_bh_ids][inverse_sorted_indexes__cat_bh_ids])

        bad_data_filter = (~np.isnan(log_halo_m_star_by_particle)) & (~np.isnan(logged_filtered_bh_masses__by_catalogue_order)) & (np.abs(log_halo_m_star_by_particle) != np.inf) & (np.abs(logged_filtered_bh_masses__by_catalogue_order) != np.inf)
        x_data = log_halo_m_star_by_particle[bad_data_filter]
        y_data = logged_filtered_bh_masses__by_catalogue_order[bad_data_filter]

        plot_object_list = plt.scatter(x_data, y_data, s = 2, alpha = 0.7, label = labels[i] if len(labels) != 0 else None)
        fit = fit_data(x_data, y_data)
        Console.print_info(f"Fit params: {fit}")
        plot_fit_line(x_data, fit, color = plot_object_list.get_facecolor()[0])

    plt.xlabel("$\\rm log_{10}$ $M_{\\rm *}$ ($\\rm M_\odot$)")
    plt.ylabel("$\\rm log_{10}$ $M_{\\rm BH}$ ($\\rm M_\odot$)")
    if len(labels) > 0:
        plt.legend()
    plt.savefig(filename)

if __name__ == "__main__":
    args_info = [["filename", "File to save plot in.", None],
                 ["snapshot-files", "SWIFT snapshot file(s). Use a semicolon seperated list.", ScriptWrapper.make_list_converter(";")],
                 ["catalogue-files", "VELOCIraptor catalogue properties file(s). Use a semicolon seperated list.", ScriptWrapper.make_list_converter(";")],
                 ["labels", "Labels - one per dataset. Can be ommited if only one file is provided.", ScriptWrapper.make_list_converter(";")]]
    kwargs_info = []
    
    script = ScriptWrapper("plot_BH_mass_stellar_mass.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["console_log_printing (local file)", "h5py", "os", "script_wrapper.py (local file)", "sys"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)

"""
np.polyfit
np.polyval
plot-bh-stellar-mass test2.png "/mnt/data2/users/astrcrai/simulations/COLIBRE/L0050N0376/colibre_0014.hdf5;/mnt/data2/users/astrcrai/simulations/COLIBRE/L0050N0376_bigSeed/colibre_0014.hdf5" "/mnt/data2/users/astrcrai/simulations/COLIBRE/L0050N0376/haloes/halo_0014.properties.0;/mnt/data2/users/astrcrai/simulations/COLIBRE/L0050N0376_bigSeed/haloes/halo_0014.properties.0" "Ref L50N376;Biig Seed" -v -d
"""
