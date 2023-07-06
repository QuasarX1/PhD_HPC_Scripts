AUTHOR = "Christopher Rowe"
VERSION = "2.0.0"
DATE = "06/07/2023"
DESCRIPTION = "Gets \u03A9_b * \u03C1_crit(z) for the specified SWIFT snapshot."

import swiftsimio as sw

from QuasarCode import source_file_relitive_add_to_path
from QuasarCode.Tools import ScriptWrapper

source_file_relitive_add_to_path(__file__, "..")
from contra.calculations import get_critical_gas_density

def __main(file, unit, hide_unit):
    data = sw.load(file)
    v = get_critical_gas_density(data, unit)
    if hide_unit:
        v = float(v.value)
    print(v)

if __name__ == "__main__":
    args_info = [["file", "SWIFT snapshot file.", None]]
    kwargs_info = [["unit", "u", "Unit to convert the value into.\nDefault is \"(10**10)*Msun/Mpc**3\".", False, False, None, "(10**10)*Msun/Mpc**3"],
                   ["hide-unit", None, "Remove the unit from the output value.", False, True, None, False]]
    
    script = ScriptWrapper("get_gas_crit_density.py",
                           AUTHOR,
                           VERSION,
                           DATE,
                           DESCRIPTION,
                           ["swiftsimio", "QuasarCode"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
