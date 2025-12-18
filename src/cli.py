import argparse
import sys

import pyfiglet

from src import workflow
from src.config import CustomPaths, check_config_file, check_priority_opt
from src.version import DOCSCRIPT_VERSION as DCV
from src.workflow import CMode

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
            "DocScript - Conversione e gestione documentazione. "
            "Tips: genera un repo git vuoto e inserisci questo come un"
            "sottomodulo prima di lanciare un --init"
        ),
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio",
        add_help=False,
    )

    # -------------------------------
    # Gruppo 1: Single Operation
    # -------------------------------
    group_standalone = parser.add_mutually_exclusive_group()
    group_standalone.add_argument(
        "-i", "--init", action="store_true", help="Inizializza un nuovo vault"
    )
    group_standalone.add_argument(
        "-ib",
        "--init-bank",
        action="store_true",
        help="Inizializza una banca dati collaborativa",
    )
    group_standalone.add_argument(
        "-s", "--start", metavar="NOTE_NAME", help="Crea una nuova nota"
    )
    group_standalone.add_argument(
        "-u", "--update", action="store_true", help="Aggiorna la banca dati"
    )
    group_standalone.add_argument(
        "-v", "--version", action="store_true", help="Stampa la versione dello script"
    )
    group_standalone.add_argument(
        "-h", "--help", action="store_true", help="Mostra questo messaggio di aiuto"
    )

    # -------------------------------
    # Gruppo 2: Conversion Operation
    # -------------------------------
    group_conversion = parser.add_mutually_exclusive_group()
    group_conversion.add_argument(
        "-a", "--all", metavar="OUTPUT", help="Converte tutte le note"
    )
    group_conversion.add_argument(
        "-g",
        "--group",
        nargs=2,
        metavar=("ARGUMENT", "OUTPUT"),
        help="Converte un gruppo di note",
    )
    group_conversion.add_argument(
        "-n",
        "--note",
        nargs=2,
        metavar=("NOTE", "OUTPUT"),
        help="Converte una singola nota",
    )
    group_conversion.add_argument(
        "-c", "--custom", metavar="OUTPUT", help="Conversione custom da file custom.md"
    )

    # -------------------------------
    # Gruppo 3: Additive Operation
    # -------------------------------
    parser.add_argument(
        "-y", "--yaml", metavar="YAML_NAME", help="File YAML personalizzato"
    )
    parser.add_argument(
        "-t", "--template", metavar="TEMPLATE_NAME", help="Template personalizzato"
    )
    parser.add_argument(
        "-l", "--lua", metavar="LUA_NAME", help="Luafilter personalizzato"
    )
    parser.add_argument(
        "-p",
        "--pandoc",
        metavar="PANDOC_NAME",
        help="Applica un --metadata-file a pandoc personalizzato",
    )

    dispatch(parser)


def dispatch(parser: argparse.ArgumentParser) -> None:

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

    print(f"il mio dato enumerativo al momento é inizializzato a {cMode}")

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
        # workflow.update_bank()
        return
    if args.version:
        print("DocScript v" + DCV)
        return

    # -------------------------------
    # Group 2
    # -------------------------------
    if args.note:
        cMode = CMode.ONE
        workflow.conversion_procedure(cMode, src=args.note[0], dst=args.note[1])
        return
    if args.group:
        cMode = CMode.GROUP
        workflow.conversion_procedure(cMode, src=args.group[0], dst=args.group[1])
        return
    if args.all:
        cMode = CMode.ALL
        workflow.conversion_procedure(cMode, dst=args.all)
        return
    if args.custom:
        cMode = CMode.CUSTOM
        workflow.conversion_procedure(cMode, dst=args.custom)
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
                "Errore: le operazioni -i, -ib, -s, -u, -v, -h non possono essere "
                "combinate con -a, -g, -n, -c"
            )
            sys.exit(1)
        # Check that there are no additional options
        if args.yaml or args.template:
            print(
                "Errore: le operazioni -i, -ib, -s, -u, -v, -h non accettano "
                "opzioni aggiuntive"
            )
            sys.exit(1)


def get_command(args: argparse.Namespace) -> str:
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
