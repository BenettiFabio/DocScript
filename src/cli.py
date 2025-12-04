import argparse
import sys

import pyfiglet

# from src import workflow
from src.config import CustomPaths, check_config_file, check_priority_opt

###########
# Defines #
###########
JUMP_CHECK_COMMANDS = {
    "init",
    "init-bank",
    "help",
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
    # Gruppo 1: Operazioni singole
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
        "-h", "--help", action="store_true", help="Mostra questo messaggio di aiuto"
    )

    # -------------------------------
    # Gruppo 2: Operazioni di conversione
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
    # Gruppo 3: Opzioni aggiuntive
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

    # verifica che gli argomenti siano  in ordine giusto senza errori di dipendenze
    validate_args(args)

    request = get_command(args)
    if request not in JUMP_CHECK_COMMANDS:
        ConfigCustomPaths = CustomPaths()
        if request in NEED_FS_COMMANDS:
            # verifico file di configurazione -> sovrascrive i default
            check_config_file(cfgCstmPath=ConfigCustomPaths)
            # verifico opzioni a terminale -> sovrascrive file di configurazione
            check_priority_opt(
                cfgCstmPath=ConfigCustomPaths,
                yaml=args.yaml,
                template=args.template,
                lua=args.lua,
                pandoc=args.pandoc,
                start=args.start,
            )

    # -------------------------------
    # Gruppo 1
    # -------------------------------
    if args.init:
        # workflow.init_vault()
        print("init-vault")
        return
    if args.init_bank:
        print("init-bank")
        # workflow.init_bank()
        return
    if args.start:
        print("new-note")
        # workflow.start_note(args.start)
        return
    if args.update:
        print("update-bank")
        # workflow.update_bank()
        return

    # -------------------------------
    # Gruppo 2
    # -------------------------------
    if args.all:
        print("convert-all")
        # workflow.convert_all(
        #    args.all
        # )
        return
    if args.group:
        print("convert-group")
        # workflow.convert_group(
        #    args.group[0],
        #    args.group[1]
        # )
        return
    if args.note:
        print("convert-note")
        # workflow.convert_note(
        #    args.note[0],
        #    args.note[1]
        # )
        return
    if args.custom:
        print("convert-customs")
        # workflow.convert_custom(
        #    args.custom
        # )
        return
    print(pyfiglet.figlet_format("DocScript", font="slant"))
    parser.print_help()
    sys.exit(0)


def validate_args(args: argparse.Namespace) -> None:
    """Valida la coerenza degli argomenti"""
    # Se è un'operazione standalone, non deve avere altre opzioni
    standalone_ops = [args.init, args.init_bank, args.start, args.update, args.help]
    conversion_ops = [args.all, args.group, args.note, args.custom]

    # Conta quante operazioni standalone sono attive
    active_standalone = sum(1 for op in standalone_ops if op)

    # Se c'è un'operazione standalone attiva
    if active_standalone > 0:
        # Controlla che non ci siano operazioni di conversione
        active_conversion = sum(1 for op in conversion_ops if op)
        if active_conversion > 0:
            print(
                "Errore: le operazioni -i, -ib, -s, -u, -h non possono essere "
                "combinate con -a, -g, -n, -c"
            )
            sys.exit(1)
        # Controlla che non ci siano opzioni aggiuntive
        if args.yaml or args.template:
            print(
                "Errore: le operazioni -i, -ib, -s, -u, -h non accettano "
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
    return "help"
