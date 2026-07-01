import argparse
import os
import sys

import pyfiglet

from src import workflow
from src.config import (
    CustomPaths,
    AssetsExtList,
    BuildOptions,
    check_config_file,
    apply_build_overrides,
)
from src.modes import CMode
from src.pandoc.runner import (
    SUPPORTED_OUTPUT_EXTENSIONS,
    SUPPORTED_OUTPUT_EXTENSIONS_TEXT,
)
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
    "fix-links",
}
NEED_FS_COMMANDS = {
    "start",
    "update",
    "lint",
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
        "-L", "--lint", action="store_true", help="Consistency check of all links"
    )
    group_standalone.add_argument(
        "-fl",
        "--fix-links",
        action="store_true",
        help="Automatic Fix of all links, run -L before this",
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
    parser.add_argument("-y", "--yaml", metavar="YAML_NAME",
                        help="Custom YAML file")
    parser.add_argument(
        "-t", "--template", metavar="TEMPLATE_NAME", help="Custom Template file"
    )
    parser.add_argument("-l", "--lua", metavar="LUA_NAME",
                        help="Custom LuaFilter file")
    parser.add_argument(
        "-p",
        "--pandoc",
        metavar="PANDOC_NAME",
        help="Apply custom --metadata-file into pandoc option",
    )
    parser.add_argument(
        "-T",
        "--title",
        metavar="DOCUMENT_TITLE",
        help="Override document title for this conversion",
    )

    dispatch(parser)


def dispatch(parser: argparse.ArgumentParser) -> None:
    """
    Handle the arguments from cmd line
    """

    args = parser.parse_args()

    build_opts = BuildOptions(
        title=args.title,
        yaml=args.yaml,
        template=args.template,
        lua=args.lua,
        pandoc=args.pandoc,
    )

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
        AssetsCustomExt = AssetsExtList()
        if request in NEED_FS_COMMANDS:
            # check the configuration file -> overwrite the defaults
            check_config_file(cfgCstmPath=ConfigCustomPaths,
                              sstCstmXt=AssetsCustomExt)
            # check cli options -> overwrite configuration file options
            apply_build_overrides(
                cfgCstmPath=ConfigCustomPaths,
                buildOpts=build_opts,
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
    if args.lint:
        print("Lint all links")
        workflow.run_linter(AssetsCustomExt)
        return
    if args.fix_links:
        print("Automatic fix links")
        workflow.fix_links()
        return
    # -------------------------------
    # Group 2
    # -------------------------------
    if args.note:
        cMode = CMode.ONE
        validate_output(args.note[1])
        workflow.conversion_procedure(
            cMode, ConfigCustomPaths, build_opts, src=args.note[0], dst=args.note[1]
        )
        return
    if args.group:
        cMode = CMode.GROUP
        validate_output(args.group[1])
        workflow.conversion_procedure(
            cMode,
            ConfigCustomPaths,
            build_opts,
            src=args.group[0],
            dst=args.group[1],
        )
        return
    if args.all:
        cMode = CMode.ALL
        validate_output(args.all)
        workflow.conversion_procedure(
            cMode, ConfigCustomPaths, build_opts, src=None, dst=args.all
        )
        return
    if args.custom:
        cMode = CMode.CUSTOM
        validate_output(args.custom)
        workflow.conversion_procedure(
            cMode, ConfigCustomPaths, build_opts, src=None, dst=args.custom
        )
        return

    print(pyfiglet.figlet_format("DocScript", font="slant"))
    parser.print_help()
    sys.exit(0)


def validate_args(args: argparse.Namespace) -> None:
    """
    Validate the coherence of the arguments
    """

    standalone_ops = [
        args.init,
        args.init_bank,
        args.start,
        args.update,
        args.help,
        args.version,
        args.lint,
        args.fix_links,
    ]

    conversion_ops = [
        args.all,
        args.group,
        args.note,
        args.custom,
    ]

    additive_opts = [
        args.yaml,
        args.template,
        args.lua,
        args.pandoc,
        args.title,
    ]

    active_standalone = sum(1 for op in standalone_ops if op)
    active_conversion = sum(1 for op in conversion_ops if op)

    # standalone + conversion forbidden
    if active_standalone > 0 and active_conversion > 0:
        print(
            "Error: Operations -i, -ib, -s, -u, -v, -h -L -fl"
            "cannot be combined with -a, -g, -n, -c"
        )
        sys.exit(1)

    # additive options require conversion mode
    if any(additive_opts) and active_conversion == 0:
        print(
            "Error: Additional options "
            "(-y, -t, -l, -p, -T) "
            "require a conversion operation"
        )
        sys.exit(1)


def validate_output(output: str | None) -> None:
    """
    Verify that the output file has a supported extension.
    If it is not valid, terminate the program.
    """
    outPath = safe_path(str(output))
    ext = os.path.splitext(outPath)[1].lower()
    if ext not in SUPPORTED_OUTPUT_EXTENSIONS:
        print(
            f"Error: The output file '{output}' must be {SUPPORTED_OUTPUT_EXTENSIONS_TEXT}"
        )
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
    if args.lint:
        return "lint"
    if args.fix_links:
        return "fix-links"
    return "help"
