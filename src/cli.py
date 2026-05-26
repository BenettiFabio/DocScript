import argparse
import os
import sys

import pyfiglet

from src import workflow
from src.config import CustomPaths, check_config_file, check_priority_opt
from src.modes import CMode
from src.utils import safe_path
from src.version import DOCSCRIPT_VERSION as DCV

###############
# Description #
###############
"""
The contents of this file are all the functions
that describe terminal behavior
and that route requests based on the initial options.
"""

###########
# Defines #
###########
JUMP_CHECK_COMMANDS = {
    "init",
    "init-bank",
    "help",
    "version",
}
NEED_FS_COMMANDS = {
    "start",
    "update",
    "convert-all",
    "convert-note",
    "convert-group",
    "convert-custom",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="make.py",
        description=(
            "DocScript - Manage and Convert Documentation "
            "Tips: create an empty git repo, and add this project"
            "as a submodule before running --init command"
        ),
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio",
        add_help=False,
    )

    # -------------------------------
    # Group 1: Single Operation
    # -------------------------------
    group_standalone = parser.add_mutually_exclusive_group()
    group_standalone.add_argument(
        "-i", "--init", action="store_true", help="Initialize a new Vault"
    )
    group_standalone.add_argument(
        "-ib",
        "--init-bank",
        action="store_true",
        help="Initialize a new collaborative data Bank",
    )
    group_standalone.add_argument(
        "-s", "--start", metavar="NOTE_NAME", help="Create a new note"
    )
    group_standalone.add_argument(
        "-u", "--update", action="store_true", help="Update data Bank"
    )
    group_standalone.add_argument(
        "-v", "--version", action="store_true", help="Print the script version"
    )
    group_standalone.add_argument(
        "-h", "--help", action="store_true", help="Show this help message"
    )

    # -------------------------------
    # Group 2: Conversion Operation
    # -------------------------------
    group_conversion = parser.add_mutually_exclusive_group()
    group_conversion.add_argument(
        "-a", "--all", metavar="OUTPUT", help="Converts all the vault notes"
    )
    group_conversion.add_argument(
        "-g",
        "--group",
        nargs=2,
        metavar=("ARGUMENT", "OUTPUT"),
        help="Convert a group of notes",
    )
    group_conversion.add_argument(
        "-n",
        "--note",
        nargs=2,
        metavar=("NOTE", "OUTPUT"),
        help="Converta single note",
    )
    group_conversion.add_argument(
        "-c",
        "--custom",
        metavar="OUTPUT",
        help="Custom conversion from a list in custom.md",
    )

    # -------------------------------
    # Gruppo 3: Additive Operation
    # -------------------------------
    parser.add_argument("-y", "--yaml", metavar="YAML_NAME", help="Custom YAML file")
    parser.add_argument(
        "-t", "--template", metavar="TEMPLATE_NAME", help="Custom Template file"
    )
    parser.add_argument("-l", "--lua", metavar="LUA_NAME", help="Custom LuaFilter file")
    parser.add_argument(
        "-p",
        "--pandoc",
        metavar="PANDOC_NAME",
        help="Apply custom --metadata-file into pandoc option",
    )

    dispatch(parser)


def dispatch(parser: argparse.ArgumentParser) -> None:
    """
    Handle the arguments from cmd line
    """

    args = parser.parse_args()

    if args.help and not any([args.all, args.group, args.note, args.custom]):
        print(pyfiglet.figlet_format("DocScript", font="slant"))
        parser.print_help()
        sys.exit(0)

    # Check that the arguments are in the correct order without dependency errors
    validate_args(args)

    # proceeds to read the configuration files only after a check
    # of the file system structure
    request = get_command(args)
    if request not in JUMP_CHECK_COMMANDS:
        ConfigCustomPaths = CustomPaths()
        if request in NEED_FS_COMMANDS:
            # check the configuration file -> overwrite the defaults
            check_config_file(cfgCstmPath=ConfigCustomPaths)
            # check cli options -> overwrite configuration file options
            check_priority_opt(
                cfgCstmPath=ConfigCustomPaths,
                yaml=args.yaml,
                template=args.template,
                lua=args.lua,
                pandoc=args.pandoc,
            )

    cMode = CMode.NONE

    # -------------------------------
    # Group 1
    # -------------------------------
    if args.init:
        workflow.init_vault()
        return
    if args.init_bank:
        bankFlag = True
        workflow.init_vault(bankFlag)
        return
    if args.start:
        print("new-note")
        workflow.start_note(ConfigCustomPaths, args.start)
        return
    if args.update:
        print("update-bank")
        workflow.update_bank()
        return
    if args.version:
        print("DocScript v" + DCV)
        return

    # -------------------------------
    # Group 2
    # -------------------------------
    if args.note:
        cMode = CMode.ONE
        validate_output(args.note[1])
        workflow.conversion_procedure(
            cMode, ConfigCustomPaths, src=args.note[0], dst=args.note[1]
        )
        return
    if args.group:
        cMode = CMode.GROUP
        validate_output(args.group[1])
        workflow.conversion_procedure(
            cMode, ConfigCustomPaths, src=args.group[0], dst=args.group[1]
        )
        return
    if args.all:
        cMode = CMode.ALL
        validate_output(args.all)
        workflow.conversion_procedure(cMode, ConfigCustomPaths, src=None, dst=args.all)
        return
    if args.custom:
        cMode = CMode.CUSTOM
        validate_output(args.custom)
        workflow.conversion_procedure(
            cMode, ConfigCustomPaths, src=None, dst=args.custom
        )
        return

    print(pyfiglet.figlet_format("DocScript", font="slant"))
    parser.print_help()
    sys.exit(0)


def validate_args(args: argparse.Namespace) -> None:
    """
    Validate the coherence of the arguments
    """

    # If it is a standalone operation, it should not have any other options
    standalone_ops = [
        args.init,
        args.init_bank,
        args.start,
        args.update,
        args.help,
        args.version,
    ]
    conversion_ops = [args.all, args.group, args.note, args.custom]

    # Counts how many standalone operations are active
    active_standalone = sum(1 for op in standalone_ops if op)

    # If there is an active standalone operation
    if active_standalone > 0:
        # Check that there are no conversion operations
        active_conversion = sum(1 for op in conversion_ops if op)
        if active_conversion > 0:
            print(
                "Error: Operations -i, -ib, -s, -u, -v, -h cannot be combined "
                "with -a, -g, -n, -c"
            )
            sys.exit(1)
        # Check that there are no additional options
        if args.yaml or args.template:
            print(
                "Error: Operations -i, -ib, -s, -u, -v, -h do not "
                "accept additional options"
            )
            sys.exit(1)


def validate_output(output: str | None) -> None:
    """
    Verify that the output file has a valid extension (.pdf or .tex).
    If it is not valid, terminate the program.
    """
    outPath = safe_path(str(output))
    ext = os.path.splitext(outPath)[1].lower()
    if ext not in [".pdf", ".tex"]:
        print(f"Error: The output file '{output}' must be .pdf o .tex.")
        sys.exit(1)


def get_command(args: argparse.Namespace) -> str:
    """
    Return a string from the cmd selected
    """
    if args.init:
        return "init"
    if args.init_bank:
        return "init-bank"
    if args.start:
        return "start"
    if args.update:
        return "update"
    if args.all:
        return "convert-all"
    if args.group:
        return "convert-group"
    if args.note:
        return "convert-note"
    if args.custom:
        return "convert-custom"
    if args.version:
        return "version"
    return "help"
