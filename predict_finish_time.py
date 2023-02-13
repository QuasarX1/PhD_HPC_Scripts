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
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_debug
from script_wrapper import ScriptWrapper

FILE_PATERN = "timesteps_*.txt"
FILE_LINE_DATA_START = 14
FILE_Z_DATA_START = 36
FILE_Z_DATA_END = 49
FILE_T_DATA_START = 139
FILE_T_DATA_END = 161

def __main():
    files = glob.glob(FILE_PATERN)
    if len(files) == 0:
        raise FileNotFoundError(f"Unable to find a file that matches the expected patern: {FILE_PATERN}")
    elif len(files) != 1:
        raise FileNotFoundError(f"Too many posible files!\nPattern: {FILE_PATERN}\nMatches: {files}")

    with open(files[0], "r") as file:
        lines = file.readlines()

    n_lines = len(lines)
    if n_lines < 18:
        raise RuntimeError("Not enough lines in file to make prediction.")

    z = []
    t = []
    for line in lines[FILE_LINE_DATA_START:-2]:# Chop off the headder and the last line as it likley isn't complete
        z.append(float(line[FILE_Z_DATA_START:FILE_Z_DATA_END]))
        t.append(float(line[FILE_T_DATA_START:FILE_T_DATA_END]))

    print_debug(f"Got {len(z)} redshift values and {len(t)} times.")

    t_csum = np.cumsum(np.array(t))
    z = np.array(z)

    fit = np.polyfit(t_csum, z, 3)

    print_verbose_info(f"Fit Params:\na = {fit[0]}\nb = {fit[1]}\nc = {fit[2]}\nd = {fit[3]}")

    
    prediction_avalible = True
    x_var = var('x')
    solutions = solve(Eq(fit[0]*x_var**3 + fit[1]*x_var**2 + fit[2]*x_var + fit[3], 0), x_var)
    if solutions is None:
        prediction_avalible = False
    elif isinstance(solutions, list):
        solutions = [solution for solution in solutions if isinstance(solution, core.numbers.Float)]
        if len(solutions) > 1:
            print_verbose_warning("Multiple roots avalible -> {}".format(solutions))
        end_time = float(solutions[0])
    else:
        if isinstance(solutions, core.numbers.Float):
            end_time = float(solutions)# Not sure if this is what would hapen if there is only one solution.
        else:
            prediction_avalible = False

    if prediction_avalible:
        print_info("Time untill completion: {}".format(datetime.timedelta(milliseconds = end_time - t_csum[-1])))
    else:
        print_warning("No valid fit root found.")

    plt.plot((t_csum / 1000 / 60**2), z, c = "b", label = "Data")
    fit_time_values = np.linspace(0, end_time, 10000) if prediction_avalible else t_csum
    plt.plot(fit_time_values / 1000 / 60**2, (fit[0] * fit_time_values**3) + (fit[1] * fit_time_values**2) + (fit[2] * fit_time_values) + fit[3], linestyle = ":", c = "orange", label = "Fit")#
    if prediction_avalible:
        plt.scatter([end_time / 1000 / 60**2], [0.0], c = "g", label = "End Time")
    plt.xlabel("Time (hours)")
    plt.ylabel("Redshift")
    plt.legend()
    plt.savefig("TimeEst.png")

if __name__ == "__main__":
    args_info = []
    kwargs_info = []
    
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
