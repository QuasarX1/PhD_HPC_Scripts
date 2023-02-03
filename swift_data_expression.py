"""
File: swift_data_expression.py

Author: Christopher Rowe
Vesion: 2.0.0
Date:   31/11/2022

Allows conversion from a string expression containing variables
in the form of SWIFT particle file tree nodes into a loaded
variable.

Public API:

    seperate_terms(str)
    parse_string(str, swiftsimio.SWIFTDataset or swiftsimio.__SWIFTParticleDataset)

Dependancies:

    swiftsimio

To import all public methods, use:
from swift_data_expression import seperate_terms, parse_string
"""

try:
    import swiftsimio as sw
except:
    raise ImportError("This module is designed to work with swiftsimio, but the package is not avalible for import.")
import unyt
import numpy as np
from typing import Union, List, Tuple
import uuid

def __bracket_higherarchy(expression: str, open_character: str = "(", close_character: str = ")") -> List[Union[str, List]]:
    if (open_character in expression and close_character not in expression) or (open_character not in expression and close_character in expression):
        raise SyntaxError(f"Brackets not matched in \"{expression}\"")
    elif open_character not in expression and close_character not in expression:
        return [expression]

    open_bracket_positions = []
    all_opens_found = False
    while not all_opens_found:
        try:
            open_bracket_positions.append(expression.index(open_character, (open_bracket_positions[-1] + 1) if len(open_bracket_positions) > 0 else 0))
        except ValueError:
            all_opens_found = True
    open_bracket_positions = np.array(open_bracket_positions)

    close_bracket_positions = []
    all_closes_found = False
    while not all_closes_found:
        try:
            close_bracket_positions.append(expression.index(close_character, (close_bracket_positions[-1] + 1) if len(close_bracket_positions) > 0 else 0))
        except ValueError:
            all_closes_found = True
    close_bracket_positions = np.array(close_bracket_positions)

    if len(open_bracket_positions) != len(close_bracket_positions):
        raise SyntaxError(f"Brackets not matched in \"{expression}\"")

    expr_length = len(expression)
    left_i = open_bracket_positions[0]

    right_i = None
    for possible_right in close_bracket_positions:
        if (open_bracket_positions < possible_right).sum() - (close_bracket_positions < possible_right).sum() == 1:
            right_i = possible_right
            break

    output = (expression[0 : left_i], __bracket_higherarchy(expression[left_i + len(open_character) : right_i], open_character, close_character), *__bracket_higherarchy(expression[right_i + len(close_character) : expr_length], open_character, close_character))
    return [substring for substring in output if substring != ""]

def __join(values: List[Union[unyt.unyt_array, unyt.unyt_quantity, List]], operators: List[str], nvalues: int, value_i: int = 0, operator_i = 0, return_next_op_index = False) -> Union[unyt.unyt_array, unyt.unyt_quantity]:
    joined_value = values[value_i]
    next_value = value_i + 1
    next_operator = operator_i + 1
    
    if isinstance(joined_value, list):
        joined_value, operator_i = __join(values[value_i], operators, len(values[value_i]), 0, operator_i, True)
        next_operator = operator_i + 1

    if len(operators) > 0 and value_i < nvalues - 1:
        if operators[value_i] == "**":
            if isinstance(values[value_i + 1], list):
                power_value, operator_i = __join(values[next_value], operators, len(values[next_value]), 0, next_operator, True)
                joined_value **= power_value
                next_operator = operator_i + 1
            else:
                joined_value **= values[next_value]
            value_i = next_value

        next_value, next_operator = __join(values, operators, nvalues, value_i + 1, next_operator, True)
        if operators[operator_i] == "*":
            #joined_value *= next_value# DON'T DO THIS (causes overflow warning and max recursion error on large datasets...)
            joined_value = joined_value * next_value
        elif operators[operator_i] == "/":
            joined_value = joined_value / next_value
        elif operators[operator_i] == "+":
            joined_value = joined_value + next_value
        elif operators[operator_i] == "-":
            joined_value = joined_value - next_value
        else:
            raise RuntimeError()

    if not return_next_op_index:
        return joined_value
    else:
        return joined_value, next_operator

def seperate_terms(expression: str) -> Tuple[List[Union[str, List]], List[str]]:
    """
    function seperate_terms

    Seperates the terms of an expression from its operators and returns
    a list of each. Terms that include unyt unit expressions should be
    enclosed with "#<" ">#".

    Paramiters:
        str expression -> A string expression.

    Returns:
        tuple(list[str], list[str]) -> A list of all terms and a list of
                                           the joining operators.
    """

    # Temporeraly remove the indicated unyt terms
    unit_value_chunks = [substring for substring in __bracket_higherarchy(expression, "#<", ">#") if expression[expression.index(substring[0] if isinstance(substring, list) else substring) - 2 :][:2] == "#<"]
    unyt_value_dict = {}
    unyt_checked_expression = expression
    for string_value_single_item_list in unit_value_chunks:
        placeholder = str(uuid.uuid4()).replace("-", "")
        unyt_value_dict[placeholder] = string_value_single_item_list[0]
        unyt_checked_expression = unyt_checked_expression.replace(f"<{string_value_single_item_list[0]}>", placeholder, 1)

    bracket_ordered_terms = __bracket_higherarchy(unyt_checked_expression)

    # Create a list of string terms by removing operators
    def split_on_ops(exp: List[Union[List, str]]):
        if isinstance(exp, list):
            return [split_on_ops(sub_exp) for sub_exp in exp] if len(exp) > 1 else split_on_ops(exp[0])
        else:
            result = [value for value in exp.replace("**", "/").replace("*", "/").replace("+", "/").replace("-", "/").split("/") if value != ""]
            return result if len(result) > 1 else result[0]
    attribute_strings = split_on_ops(bracket_ordered_terms)
    if not isinstance(attribute_strings, list):
        attribute_strings = [attribute_strings]

    def unpack(arr):
        if isinstance(arr, list):
            temp_list = []
            for item in arr:
                unpacked_value = unpack(item)
                if isinstance(unpacked_value, list):
                    temp_list.extend(unpacked_value)
                else:
                    temp_list.append(unpacked_value)
            return temp_list
        else:
            return arr
    flattened_attribute_strings = unpack(attribute_strings)
    
    # Create a list of string operators using the identified terms
    attribute_opperators = unyt_checked_expression.replace("(", "").replace(")", "")
    for i in range(len(flattened_attribute_strings)):
        attribute_opperators = attribute_opperators.replace(flattened_attribute_strings[i], "|")
    attribute_opperators = attribute_opperators.replace("#", "").strip("|").split("|")

    # Re-add the unyt terms - replacing the # indicators
    def replace_unyt_strings(nested_string_list):
        for i in range(len(nested_string_list)):
            if isinstance(nested_string_list[i], list):
                nested_string_list[i] = replace_unyt_strings(nested_string_list[i])
            else:
                if "#" in nested_string_list[i]:
                    first_opener = nested_string_list[i].index("#")
                    next_closer = nested_string_list[i].index("#", first_opener + 1)
                    nested_string_list[i] = nested_string_list[i][: first_opener] + unyt_value_dict[nested_string_list[i][first_opener + 1 : next_closer]] + nested_string_list[i][next_closer + 1 :]

                    #i -= 1# Force the substring to be re-checked in case more than one is present

        return nested_string_list
        
    attribute_strings = replace_unyt_strings(attribute_strings)

    return attribute_strings, attribute_opperators

def parse_string(expression: str, root_node: sw.SWIFTDataset) -> Union[unyt.unyt_array, unyt.unyt_quantity]:
    """
    function parse_string

    Parses a string expression for combining SWIFT datasets and constants.
    Mathematics is permitted with the cavieats that no spaces are
    permitted and no mathematics ordering rules are applied! Also, no
    consecutive 'power of' operators (**) are permitted. Values with an
    associated unyt unit expression should be enclosed with "#<" ">#".

    All SWIFT datasets should be specified with the root attribute ommitted.

    Paramiters:
                            str expression -> A string expression.
        swiftsimio.SWIFTDataset root_node  -> The root node that SWIFT datasets are specified from.
                                                  E.g. the opened file if an expression term is "gas.masses".

    Returns:
        A combined variable that may be used as a swiftsimio data set.
    """
    attribute_strings, attribute_opperators = seperate_terms(expression)

    def parser(attribute_strings):
        attribute_array = []
        for attribute in attribute_strings:
            if isinstance(attribute, list):
                attribute_array.append(parser(attribute))
            else:
                try:
                    #value = float(attribute)
                    value = unyt.unyt_quantity.from_string(attribute)
                    attribute_array.append(value)
                except:
                    attribute_sections = attribute.split(".")
                    attribute_opject = root_node
                    for i in range(len(attribute_sections)):
                        attribute_opject = attribute_opject.__getattribute__(attribute_sections[i])
                    attribute_array.append(attribute_opject)
        return attribute_array

    # Parse the attributes by making them either floats or dataset values using the root node
    attribute_array: List[Union[unyt.unyt_array, unyt.unyt_quantity, List]] = parser(attribute_strings)
            
    # Stich all the attributes together using the opperators
    return __join(attribute_array, attribute_opperators, len(attribute_array))