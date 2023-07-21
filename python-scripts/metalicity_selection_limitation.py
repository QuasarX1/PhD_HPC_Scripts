AUTHOR = "Christopher Rowe"
VERSION = "1.0.0"
DATE = "11/07/2023"
DESCRIPTION = "Plots the particle selection fraction for a range of metalicity lower bounds."

import numpy as np
import os
import swiftsimio as sw
from matplotlib import pyplot as plt
from typing import Union, List

from QuasarCode import Console
from QuasarCode.Tools import ScriptWrapper

def get_tracked_fractions(metalicity_cuttoffs, metalicities, tracking_filter):
    #return [(tracking_filter & (metalicities >= cuttoff)).sum() / (metalicities >= cuttoff).sum() for cuttoff in metalicity_cuttoffs]

    metalicity_filters = metalicity_cuttoffs[:, None] <= metalicities
    return [(tracking_filter & metalicity_filters[i, :]).sum() / metalicity_filters[i, :].sum() for i in range(metalicity_filters.shape[0])]

def __main(filename: str, snapshot_files: List[str], labels: Union[List[str], None], title: Union[str, None]):
    n_datapoints = 1000
    max_Z = 0.0005
    metalicity_cuttoffs = np.linspace(0, max_Z, n_datapoints)
    Console.print_verbose_info(f"{n_datapoints} datapoints in range 0 <= Z <= {max_Z}")

    line_styles = ["-", "--", ":", "-."]
    for i, file in enumerate(snapshot_files):
        Console.print_verbose_info(f"Plotting line for data from: {file}")
        snap = sw.load(file)
        tracked_fractions = get_tracked_fractions(metalicity_cuttoffs, snap.gas.metal_mass_fractions, snap.gas.last_halo_ids != -1)
        plt.plot(metalicity_cuttoffs, tracked_fractions, label = labels[i] if labels is not None else None, alpha = 0.7, linestyle = line_styles[i % len(line_styles)])
    
    plt.semilogx()
    plt.xlabel("Z Cuttoff")
    plt.ylabel("Tracked Fraction of Metal Particles ($Z$ >= $\\rm Z_{min}$)")
    if title is not None:
        plt.title(title)
    if labels is not None:
        plt.legend()
    plt.savefig(filename)

if __name__ == "__main__":
    args_info = [["filename", "File to save plot in.", None],
                 ["snapshot_files", "SWIFT snapshot file(s). Use a semicolon seperated list.", ScriptWrapper.make_list_converter(";")]]
    kwargs_info = [["labels", "l", "Labels to use - one for each dataset. This can be omitted entierly if only one dataset is provided.", False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["title", "t", "Plot title.", False, False, None, None]]
    
    script = ScriptWrapper("metalicity_selection_limitation.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["numpy", "os", "QuasarCode"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
