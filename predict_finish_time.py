AUTHOR = "Christopher Rowe"
VERSION = "1.1.1"
DATE = "27/03/2023"
DESCRIPTION = "Predicts the finish time of a simulation."

import datetime
import glob
from matplotlib import pyplot as plt
import numpy as np
import os
from QuasarCode.IO.Text.console import print_info, print_verbose_info, print_warning, print_verbose_warning, print_verbose_error, print_debug
from QuasarCode.Tools import ScriptWrapper
from sympy import var, Eq, solve, core
from typing import List

FILE_PATERN = "timesteps_*.txt"
FILE_LINE_DATA_START = 14
FILE_A_DATA_START = 23
FILE_A_DATA_END = 36
FILE_Z_DATA_START = 36
FILE_Z_DATA_END = 49
FILE_T_DATA_START = 139
FILE_T_DATA_END = 161
LINE_COLOUR_OPTIONS = ["b", "g", "r"]

def get_fit_value(x, fit, **kwargs):
    n = len(fit)
    return sum([fit[i] * x**(n - 1 - i) for i in range(n)], **kwargs)

def get_time_prediction(x, y, n, root_index, y_root = 0):
    fit = np.polyfit(x, y, n)

    print_verbose_info(("Fit Params:" + "\n{}"*n).format(*fit))

    prediction_avalible = True
    x_var = var('x')
    solutions = solve(Eq(get_fit_value(x_var, fit), y_root), x_var)
    if solutions is None:
        prediction_avalible = False
    elif isinstance(solutions, list):
        solutions = [solution for solution in solutions if isinstance(solution, core.numbers.Float) and float(solution) > 0]
        n_solutions = len(solutions)
        if n_solutions > 1:
            print_verbose_warning("Multiple valid roots avalible -> {}".format(solutions))
            if (root_index > 1 and root_index >= n_solutions) or (root_index < -2 and -root_index > n_solutions):
                print_verbose_error("Index {} was out of range for number of roots {}.\nFalling back to default option.".format(root_index, n_solutions))
                root_index = 0
            print_verbose_warning("Selecting root at index {}".format(root_index))
        if n_solutions > 0:
            end_time = float(solutions[root_index])
        else:
            prediction_avalible = False
    else:
        if isinstance(solutions, core.numbers.Float) and float(solutions) > 0:
            end_time = float(solutions)# Not sure if this is what would hapen if there is only one solution.
        else:
            prediction_avalible = False
    
    if prediction_avalible:
        return True, end_time, fit
    else:
        return False, None, fit
    
def find_file(location = ""):
    location_patern = os.path.join(location, FILE_PATERN) if location != "" else FILE_PATERN

    files = glob.glob(location_patern)
    if len(files) == 0:
        raise FileNotFoundError(f"Unable to find a file that matches the expected patern: {location_patern}")
    elif len(files) != 1:
        raise FileNotFoundError(f"Too many posible files!\nPattern: {location_patern}\nMatches: {files}\nUse \"input-file\" paramiter to specify a file (see --help).")
    
    return files[0]

def __main(expansion_factor: bool, redshift: bool, input_files: List[str], output_file: str, poly_orders: List[int], no_graph: bool, root_indexes: List[int], labels: List[float], multipliers: List[str]):
    if input_files is None:
        input_file = [find_file()]
    else:
        if input_files[0] == "" or os.path.isdir(input_files[0]):
            input_files[0] = find_file(input_files[0])
        for i in range(1, len(input_files)):
            if os.path.isdir(input_files[i]):
                input_files[i] = find_file(input_files[i])

    all_t_csum = []
    all_z = []
    all_a = []
    all_prediction_avalible = []
    all_end_time = []
    all_fit = []
    all_labels = []
    all_multipliers = []

    for i, input_file in enumerate(input_files):
        print_info(f"Doing file index {i}")
        print_verbose_info(f"Label: {labels[i]}, Poly order: {poly_orders[i]}, Multiplier {multipliers[i]}")
        print_verbose_info(f"File: {input_file}")
        with open(input_file, "r") as file:
            lines = file.readlines()

        n_lines = len(lines)
        if n_lines < 18:
            raise RuntimeError(f"Not enough lines in file {input_file} to make prediction.")

        z = []
        a = []
        t = []
        for line in lines[FILE_LINE_DATA_START:-2]:# Chop off the headder and the last line as it likley isn't complete
            try:
                z_val = float(line[FILE_Z_DATA_START:FILE_Z_DATA_END])
                a_val = float(line[FILE_A_DATA_START:FILE_A_DATA_END])
                t_val = float(line[FILE_T_DATA_START:FILE_T_DATA_END])

                z.append(z_val)
                a.append(a_val)
                t.append(t_val)
            except: pass

        print_debug(f"Got {len(a)} expansion factor values, {len(z)} redshift values and {len(t)} times.")

        multiplier = multipliers[i] if len(multipliers) > 1 else multipliers[0]
        t_csum = np.cumsum(np.array(t) * multiplier)
        z = np.array(z)
        a = np.array(a)

        prediction_avalible, end_time, fit = get_time_prediction(x = t_csum, y = a if expansion_factor else z, y_root = 1 if expansion_factor else 0, n = poly_orders[i] if len(poly_orders) > 1 else poly_orders[0], root_index = root_indexes[i] if len(root_indexes) > 1 else root_indexes[0])

        if prediction_avalible:
            print_info("Time until completion: {}".format(datetime.timedelta(milliseconds = end_time - t_csum[-1])))
            print_info("Estimated date and time of completion: {}".format(datetime.datetime.now() + datetime.timedelta(milliseconds = end_time - t_csum[-1])))
            print_info("Estimated total runtime: {}".format(datetime.timedelta(milliseconds = end_time)))
        else:
            print_warning("No valid fit root found. Prediction not avalible.")

        all_t_csum.append(t_csum)
        all_z.append(z)
        all_a.append(a)
        all_prediction_avalible.append(prediction_avalible)
        all_end_time.append(end_time)
        all_fit.append(fit)
        all_labels.append(labels[i])
        all_multipliers.append(multiplier)

    if not no_graph:
        is_first_prediction = True
        for i in range(len(all_prediction_avalible)):
            line_colour = LINE_COLOUR_OPTIONS[i % len(LINE_COLOUR_OPTIONS)]
            plt.plot(all_a[i] if expansion_factor else all_z[i], (all_t_csum[i] / 1000 / 60**2), c = line_colour, label = all_labels[i] + ("" if all_multipliers[i] == 1.0 else f" (x{all_multipliers[i]})"))
            fit_time_values = np.linspace(0, all_end_time[i], 10000) if all_prediction_avalible[i] else all_t_csum[i]
            kwargs = {}
            if i == 0: kwargs["label"] = "Fit"
            plt.plot(get_fit_value(fit_time_values, all_fit[i]), fit_time_values / 1000 / 60**2, linestyle = ":", c = "orange", **kwargs)
            if all_prediction_avalible[i]:
                kwargs = {}
                if is_first_prediction:
                    kwargs["label"] = "End Time"
                    is_first_prediction = False
                plt.scatter([1.0 if expansion_factor else 0.0], [all_end_time[i] / 1000 / 60**2], c = "g" if len(all_prediction_avalible) == 1 else line_colour, **kwargs)
        plt.xlabel("Expansion Factor" if expansion_factor else "Redshift")
        plt.ylabel("Time (hours)")
        plt.legend()
        plt.savefig("TimeEst.png" if output_file is None else output_file)

if __name__ == "__main__":
    args_info = []
    kwargs_info = [["expansion-factor", "a", "Use the expansion factor. This is the default", False, True, None, True, ["redshift"]],
                   ["redshift", "z", "Use the expansion factor. This is the default", False, True, None, None, ["expansion-factor"]],
                   ["input-files", "f", "Optionally, specify the timesteps_x.txt file to use.\n Use this when there are multiple files that match the patern or to specify a file in another directory.\nTo plot multiple lines for seperate sumulations, optionally, specify further filepaths as a ; seperated list.", False, False, ScriptWrapper.make_list_converter(";"), None],
                   ["output-file", "o", "Optionally, specify a file (and path) to save the output graph to.\n Use this if you don't have write permission in the running simulation folder.", False, False, None, None],
                   ["poly-orders", "p", "Order of the polynomial used to produce the fit.\nNOTE: The root solving will take considerably longer with higher order polynomials!\nThis defaults to 1 (straight line).\nTo plot multiple lines for seperate sumulations, optionally, specify further arguments as a ; seperated list.", False, False, ScriptWrapper.make_list_converter(";", int), [1]],
                   ["no-graph", "g", "Don't create a graph - just attempt a time prediction.\nWARNING: the fit may not mbe appropriate!\nManual checking of the graph is advised - especially relitivley early on during the run.", False, True, None, None],
                   ["root-indexes", None, "Manually specify the index of the root to use if there is more than one valid root to the fitting function.\nThis will default to zero, but will also use index zero in the event that the index specified is out of range.\nTo plot multiple lines for seperate sumulations, optionally, specify further arguments as a ; seperated list.", False, False, ScriptWrapper.make_list_converter(";", int), [0]],
                   ["labels", None, "Labels for each input dataset (in the case of multiple datasets).\nTo plot multiple lines for seperate sumulations, optionally, specify further arguments as a ; seperated list.", False, False, ScriptWrapper.make_list_converter(";", str), ["Data"]],
                   ["multipliers", None, "Multiply the times by a fixed constant.\nTo plot multiple lines for seperate sumulations, optionally, specify further arguments as a ; seperated list.", False, False, ScriptWrapper.make_list_converter(";", float), [1.0]]]
    
    script = ScriptWrapper("predict_finish_time.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["console_log_printing.py (local file)", "datetime", "matplotlib", "numpy", "os", "script_wrapper.py (local file)", "sympy", "sys", "typing"],
                           [""],
                           args_info,
                           kwargs_info)

    script.run(__main)
