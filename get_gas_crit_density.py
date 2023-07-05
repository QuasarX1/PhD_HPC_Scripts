AUTHOR = "Christopher Rowe"
VERSION = "1.0.1"
DATE = "27/03/2023"
DESCRIPTION = "Gets \u03A9_b * \u03C1_crit(z) for the specified SWIFT snapshot."

from QuasarCode.Tools import ScriptWrapper
import swiftsimio as sw
from .contra.calculations import get_critical_gas_density

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
                           ["os", "script_wrapper.py (local file)", "swiftsimio", "sys", "unyt"],
                           [],
                           args_info,
                           kwargs_info)

    script.run(__main)
