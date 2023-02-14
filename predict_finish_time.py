AUTHOR = "Christopher Rowe"
VERSION = "1.0.1"
DATE = "13/02/2023"
DESCRIPTION = "Predicts the finish time of a simulation."

import datetime
import glob
from matplotlib import pyplot as plt
import numpy as np
import os
from sympy import var, Eq, solve, core
import sys

sys.path.append(__file__.rsplit(os.path.pathsep, 1)[0])
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_verbose_error, print_debug
from script_wrapper import ScriptWrapper

FILE_PATERN = "timesteps_*.txt"
FILE_LINE_DATA_START = 14
FILE_A_DATA_START = 23
FILE_A_DATA_END = 36
FILE_Z_DATA_START = 36
FILE_Z_DATA_END = 49
FILE_T_DATA_START = 139
FILE_T_DATA_END = 161

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
            print_verbose_warning("Selecting root at index {}".format(root_index))
        if n_solutions > 0:
            end_time = float(solutions[0])
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

def __main(expansion_factor: bool, redshift: bool, input_file: str, output_file: str, poly_order: int, no_graph: bool, root_index: int):
    if input_file is None:
        files = glob.glob(FILE_PATERN)
        if len(files) == 0:
            raise FileNotFoundError(f"Unable to find a file that matches the expected patern: {FILE_PATERN}")
        elif len(files) != 1:
            raise FileNotFoundError(f"Too many posible files!\nPattern: {FILE_PATERN}\nMatches: {files}\nUse \"input-file\" paramiter to specify a file (see --help).")
        
        input_file = files[0]

    with open(input_file, "r") as file:
        lines = file.readlines()

    n_lines = len(lines)
    if n_lines < 18:
        raise RuntimeError("Not enough lines in file to make prediction.")

    z = []
    a = []
    t = []
    for line in lines[FILE_LINE_DATA_START:-2]:# Chop off the headder and the last line as it likley isn't complete
        z.append(float(line[FILE_Z_DATA_START:FILE_Z_DATA_END]))
        a.append(float(line[FILE_A_DATA_START:FILE_A_DATA_END]))
        t.append(float(line[FILE_T_DATA_START:FILE_T_DATA_END]))

    print_debug(f"Got {len(a)} expansion factor values, {len(z)} redshift values and {len(t)} times.")

    t_csum = np.cumsum(np.array(t))
    z = np.array(z)
    a = np.array(a)

    prediction_avalible, end_time, fit = get_time_prediction(x = t_csum, y = a if expansion_factor else z, y_root = 1 if expansion_factor else 0, n = poly_order, root_index = root_index)

    if prediction_avalible:
        print_info("Time until completion: {}".format(datetime.timedelta(milliseconds = end_time - t_csum[-1])))
        print_info("Estimated date and time of completion: {}".format(datetime.datetime.now() + datetime.timedelta(milliseconds = end_time - t_csum[-1])))
        print_info("Estimated total runtime: {}".format(datetime.timedelta(milliseconds = end_time)))
    else:
        print_warning("No valid fit root found. Prediction not avalible.")

    if not no_graph:
        plt.plot((t_csum / 1000 / 60**2), a if expansion_factor else z, c = "b", label = "Data")
        fit_time_values = np.linspace(0, end_time, 10000) if prediction_avalible else t_csum
        plt.plot(fit_time_values / 1000 / 60**2, get_fit_value(fit_time_values, fit), linestyle = ":", c = "orange", label = "Fit")
        if prediction_avalible:
            plt.scatter([end_time / 1000 / 60**2], [1.0 if expansion_factor else 0.0], c = "g", label = "End Time")
        plt.xlabel("Time (hours)")
        plt.ylabel("Expansion Factor" if expansion_factor else "Redshift")
        plt.legend()
        plt.savefig("TimeEst.png" if output_file is None else output_file)

if __name__ == "__main__":
    args_info = []
    kwargs_info = [["expansion-factor", "a", "Use the expansion factor. This is the default", False, True, None, True, ["redshift"]],
                   ["redshift", "z", "Use the expansion factor. This is the default", False, True, None, None, ["expansion-factor"]],
                   ["input-file", "f", "Optionally, specify the timesteps_x.txt file to use.\n Use this when there are multiple files that match the patern or to specify a file in another directory.", False, False, None, None],
                   ["output-file", "o", "Optionally, specify a file (and path) to save the output graph to.\n Use this if you don't have write permission in the running simulation folder.", False, False, None, None],
                   ["poly-order", "p", "Order of the polynomial used to produce the fit.\nNOTE: The root solving will take considerably longer with higher order polynomials!\nThis defaults to 1 (straight line).", False, False, int, 1],
                   ["no-graph", "g", "Don't create a graph - just attempt a time prediction.\nWARNING: the fit may not mbe appropriate!\nManual checking of the graph is advised - especially relitivley early on during the run.", False, True, None, None],
                   ["root-index", None, "Manually specify the index of the root to use if there is more than one valid root to the fitting function.\nThis will default to zero, but will also use index zero in the event that the index specified is out of range.", False, False, int, 0]]
    
    script = ScriptWrapper("predict_finish_time.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["console_log_printing.py (local file)", "datetime", "matplotlib", "numpy", "os", "script_wrapper.py (local file)", "sympy", "sys"],
                           [""],
                           args_info,
                           kwargs_info)

    script.run(__main)
