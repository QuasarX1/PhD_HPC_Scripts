"""
File: script_wrapper.py

Author: Christopher Rowe
Vesion: 1.2.0
Date:   30/01/2023

Singelton that handles command argument parsing for the currently running program.

Public API:

    ScriptWrapper (class)

Dependancies:

    console_log_printing (local file)
    sys
    traceback
"""

import console_log_printing as clp
from console_log_printing import print_info, print_verbose_info, print_warning, print_verbose_warning, print_error, print_verbose_error, print_debug, get_debug, get_verbose
from mpi_settings import MPI_Objects, get_MPI_avalible
import sys
import traceback

class ScriptWrapper(object):
    """
    Singelton that handles command argument parsing for the currently running program.

    Constructor Arguments:

              str filename                 --> The name of the entrypoint file.

              str author                   --> The name(s) of the file author(s).

              str version_string           --> String indicating the current version of the file.

              str edit_date                --> String indicating the date of the last edit.

              str description              --> A description of the function of the script.

        list[str] dependancies             --> A list of dependancies of the script.

        list[str] usage_paramiter_examples --> A list of strings demonstrating example paramiter
                                                   lists (exclude the call to the script).

             list positional_params        --> List of paramiter information for paramiters that must
                                                   appear at the start of the argument list in order
                                                   without a flag identifier (each paramiter is a list
                                                   with fields as below).
                                                   [
                                                    name, description, conversion func (nullable)
                                                   ]

             list params                   --> List of paramiter information (each paramiter is a list
                                                   with fields as below).
                                                   [
                                                    name, short name (nullable), description,
                                                    required?, flag?, conversion func (nullable),
                                                    default value, mutually exclusive flags (list[str])
                                                   ]

    Public Methods:

               run
        static passthrough_converter
        static bool_converter
        static make_list_converter
    """

    #TODO: set this up to enforce a singleton
    #__initialised = False
    #__instance = None
    #
    #def __new__(cls, *args, **kwargs):
    #    if ScriptWrapper.__initialised:
    #        #raise RuntimeError("A running program may only define one ScriptWrapper instance.")
    #        return ScriptWrapper.__instance
    #    else:
    #        ScriptWrapper.__initialised = True
    #        ScriptWrapper.__instance = super(ScriptWrapper, cls).__new__(cls)
    #        return ScriptWrapper.__instance

    def __init__(self, filename: str, author: str, version_string: str, edit_date: str,
                       description: str,
                       dependancies: list,
                       usage_paramiter_examples: list,
                       positional_params: list = [], params: list = []):
        self.raw_case_args = sys.argv[1:]
        self.lowercase_args = [arg.lower() for arg in sys.argv[1:]]
        if "-d" in self.lowercase_args or "--debug" in self.lowercase_args:
            clp.enable_debug()
        if "-v" in self.lowercase_args or "--verbose" in self.lowercase_args:
            clp.enable_verbose()

        rendered_dependancy_strings = "\n".join([f"    {dependancy}" for dependancy in dependancies])

        rendered_usage_examples = "\n".join([f"    python {filename} {param_list}" for param_list in usage_paramiter_examples])

        self.n_positionals = len(positional_params)
        
        self.argument_spec = {}
        self.argument_spec["help"] = { "short_name": "h", "description": "Display this docstring.", "is_required": False, "is_positional": False, "is_flag": True, "mutually_exclusive_flags": [], "converter_function": ScriptWrapper.passthrough_converter, "default_value": None  }
        self.argument_spec["debug"] = { "short_name": "d", "description": "Display debug infomation.", "is_required": False, "is_positional": False, "is_flag": True, "mutually_exclusive_flags": [], "converter_function": ScriptWrapper.passthrough_converter, "default_value": None  }
        self.argument_spec["verbose"] = { "short_name": "v", "description": "Display progression infomation.", "is_required": False, "is_positional": False, "is_flag": True, "mutually_exclusive_flags": [], "converter_function": ScriptWrapper.passthrough_converter, "default_value": None  }
        for param in positional_params:
            self.argument_spec[param[0]] = { "short_name": None, "description": param[1], "is_required": True, "is_positional": True, "is_flag": False, "converter_function": ScriptWrapper.passthrough_converter if param[2] is None else param[2], "default_value": None }
        for param in params:
            self.argument_spec[param[0]] = { "short_name": param[1], "description": param[2], "is_required": param[3], "is_positional": False, "is_flag": param[4], "mutually_exclusive_flags": [] if len(param) <= 7 else param[7], "converter_function": ScriptWrapper.passthrough_converter if param[5] is None else param[5], "default_value": param[6] if param[6] is not None else ((ScriptWrapper.passthrough_converter if param[5] is None else param[5])(False) if param[4] else None) }

        name_spacing = max([len(name) for name in self.argument_spec])
        indent_spacing = name_spacing + 26

        rendered_argument_spec = "".join(["\n\n    ({}) {}{}{} || {} --> {}".format((" p" if self.argument_spec[name]["is_positional"] else (" r" if self.argument_spec[name]["is_required"] else ("f " if self.argument_spec[name]["is_flag"] else "f+"))), "  " if self.argument_spec[name]["is_positional"] else "--", name, (name_spacing - len(name)) * " ", ("  " if self.argument_spec[name]["short_name"] is None else "-{}".format(self.argument_spec[name]["short_name"])), self.argument_spec[name]["description"].replace("\n", "\n" + (indent_spacing * " "))) for name in self.argument_spec])

        self.help_string = f"""
File: {filename}

Author: {author}
Vesion: {version_string}
Date:   {edit_date}

{description}



Commandline arguments & flags ( p = required positional argument,
                                r = required paramiter,
                               f  = optional flag,
                               f+ = optional flag with a required argument):{rendered_argument_spec}



Dependancies:

{rendered_dependancy_strings}



Example Usage:

{rendered_usage_examples}
"""

        if "-h" in self.lowercase_args or "--help" in self.lowercase_args:
            print(self.help_string)
            sys.exit()

        self.params = {}
        for name in self.argument_spec:
            self.params[name] = self.argument_spec[name]["default_value"] 

        param_check_strings = []
        param_name_reverse_lookup = {}
        for name in self.argument_spec:
            param_check_strings.append(f"--{name}")
            if self.argument_spec[name]["short_name"] is not None:
                param_check_strings.append("-{}".format(self.argument_spec[name]["short_name"]))
                param_name_reverse_lookup[self.argument_spec[name]["short_name"]] = name

        arg_index = 0
        while arg_index < len(self.lowercase_args):
            if self.lowercase_args[arg_index] in param_check_strings:
                param_name = None
                if self.lowercase_args[arg_index][1] == "-":
                    param_name = self.lowercase_args[arg_index][2:]
                else:
                    param_name = param_name_reverse_lookup[self.lowercase_args[arg_index][1:]]

                if self.argument_spec[param_name]["is_flag"]:
                    self.params[param_name] = self.argument_spec[param_name]["converter_function"](True)
                    for flag_name in self.argument_spec[param_name]["mutually_exclusive_flags"]:
                        self.params[flag_name] = self.argument_spec[param_name]["converter_function"](False)
                else:
                    self.params[param_name] = self.argument_spec[param_name]["converter_function"](self.raw_case_args[arg_index + 1])
                    arg_index += 1

            arg_index += 1

        for i in range(self.n_positionals):
            self.params[positional_params[i][0]] = self.argument_spec[positional_params[i][0]]["converter_function"](self.raw_case_args[i])

        self.use_MPI = False
        self.MPI_print_non_root_process_errors = False

    def __run(func):
        def inner(self, *args, **kwargs):
            is_root_process = True
            try:
                if not self.use_MPI or MPI_Objects.MPI_RANK == 0:
                    # Either the first MPI process or MPI isn't active
                    return func(self, *args, **kwargs)
                else:
                    if not get_MPI_avalible():
                        raise ImportError("MPI required but not avalible.")

                    # MPI active and not the first process
                    is_root_process = False
                    return func(self, *args, **kwargs)
                    
            except Exception as e:
                if is_root_process or self.MPI_print_non_root_process_errors:
                    has_message = e.__str__() != ""
                    print_error(f"Execution encountered an error{(':' if has_message else ' (no details avalible).') if get_debug() or get_verbose() else '.'}")
                    print_debug("Traceback (most recent call last):\n" + "".join(traceback.format_tb(e.__traceback__)) + type(e).__name__ + (f": {e.__str__()}" if has_message else ""))
                    if has_message and not get_debug():
                        print_error(e.__str__())
                    print_info("Terminating.")

        return inner

    @__run
    def run(self, func):
        kwargs = { param.replace("-", "_"): self.params[param] for param in self.params if param not in ("help", "debug", "verbose") }
        return func(**kwargs)

    @staticmethod
    def passthrough_converter(value: str) -> str:
        return value

    @staticmethod
    def bool_converter(value: str) -> bool:
        return value in ("true", "t", "yes", "y", "accept", "1")

    @staticmethod
    def reverse_flag_converter(value: bool) -> bool:
        return not value

    @staticmethod
    def make_list_converter(seperator = ",", item_converters: list = None):
        if item_converters is None: item_converters = ScriptWrapper.passthrough_converter
        def list_converter(value: str) -> bool:
            if not isinstance(item_converters, (list, tuple)):
                return [item_converters(item) for item in value.split(seperator)]
            else:
                strings = value.split(seperator)
                while len(item_converters) < len(strings):
                    item_converters.append(ScriptWrapper.passthrough_converter)
                return [item_converters[i](strings[i]) for i in range(len(strings))]
        return list_converter
