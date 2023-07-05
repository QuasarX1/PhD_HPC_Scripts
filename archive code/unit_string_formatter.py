"""
File: unit_string_formatter.py

Author: Christopher Rowe
Vesion: 1.0.0
Date:   24/04/2023

Alters constant values in unyt string representations to display
in scientific notation.

Public API:

    format_unit_string(str)
    format_unit_string(str, bool)
    format_unit_string(str, int)
    format_unit_string(str, int, bool)

Dependancies:

    N/A

To import all public methods, use:
from unit_string_formatter import format_unit_string
"""

def format_unit_string(unit_expression: str, decimal_places: int = 2, use_tex = True):
    sections = unit_expression.replace("*", "|").replace("/", "|").split("|")

    ops_chars = [char for char in unit_expression if char in ("*", "/")]
    ops = []
    i = 1
    if len(ops_chars) > 0:
        ops.append(ops_chars[0])
    while i < len(ops_chars):
        if ops_chars[i - 1] == ops_chars[i]:
            ops[-1] = ops[-1] + ops[-1]
        else:
            ops.append(ops_chars[i])

    for i in range(len(sections)):
        if len(sections[i]) > 5:
            temp = f"{float(sections[i]):.{decimal_places}e}".replace("e+", "\\times10^|" if use_tex else "*10**|")
            temp_sections = temp.split("|")
            exponent = int(temp_sections[1])
            if float(temp_sections[0].split("\\" if use_tex else "*")[0]) != 1.0:
                sections[i] = f"{temp_sections[0]}{{{exponent}}}" if use_tex else f"{temp_sections[0]}{exponent}"
            else:
                sections[i] = f"10^{{{exponent}}}" if use_tex else f"10**{exponent}" 

    result = sections[0]
    for i in range(1, len(sections)):
        result = result + ops[i - 1] + sections[i]

    return result

if __name__ == "__main__":
    print(format_unit_string("1*erg"))
    print(format_unit_string("10*erg"))
    print(format_unit_string("100*erg"))
    print(format_unit_string("1000*erg"))
    print(format_unit_string("10000*erg"))
    print(format_unit_string("100000*erg"))
    print(format_unit_string("1000000000000000000000000000000*erg"))
    print(format_unit_string("100000000000000000000000000000000000000000000000000*erg", decimal_places = 0))
    print(format_unit_string("100000000000000000000000000000000000000000000000000*erg", decimal_places = 0, use_tex = False))
    print(format_unit_string("148254000000000000000000000000000000000000000000000*erg", decimal_places = 3))
