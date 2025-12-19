import sys
from enum import Enum
from pathlib import Path

from src.config import (
    CustomPaths,
    check_inconsistency,
    check_integrity,
    create_build_dir,
    create_new_note,
    create_vault_structure,
    get_all_files_from_main,
    get_all_files_from_root,
    is_bank,
    is_vault,
)
from src.pandoc.runner import check_precondition
from src.utils import safe_path


class CMode(Enum):
    NONE = 0
    ONE = 1
    GROUP = 2
    ALL = 3
    CUSTOM = 4


###############
# Description #
###############
"""
The contents of this file are all the functions
that describe the behavior of each interaction
that the user can perform with this tool.
It is the implementation of the user requests handled by cli.py.
"""


def init_vault(bankFlag: bool = False) -> None:
    """
    Initialize the Vault Structure
    """

    if is_bank():
        print("Errore: la cartella corrente é giá inizializzata come Bank dati.")
        sys.exit(1)

    if is_vault():
        print("Errore: la cartella corrente é giá inizializzata come Vault dati.")
        sys.exit(1)

    try:
        # Verify the DocScript infrastructure before copying necessary files
        check_integrity()

        if not bankFlag:
            print("Inizio creazione del vault...")
        else:
            print("Inizio creazione banca dati...")

        create_vault_structure(bankFlag)

        print("Struttura costruita con successo!\n")
        if not bankFlag:
            print("Enjoy your new Vault! <3")
        else:
            print("Enjoy working with your team mates! <3")

    except Exception as e:
        print(f"Errore durante la costruzione del Vault: {e}")
        sys.exit(1)


def start_note(ConfigPath: CustomPaths, noteName: str | Path) -> None:
    noteName = str(noteName)

    if is_bank():
        print("Errore: Puoi aggiungere una nota solo in un Vault privato")
        sys.exit(1)

    try:
        check_integrity()

        create_new_note(ConfigPath, noteName)

    except Exception as e:
        print(f"Errore durante la creazione della nuova nota: {e}")
        sys.exit(1)


def conversion_procedure(
    mode: CMode,
    src: str | None = None,
    dst: str | None = None,
) -> None:

    # Check modality
    modality = mode.name
    if modality is CMode.NONE.name:
        print("Error: Richiesta di conversione non applicabile")
        sys.exit(0)

    file_found_root = []
    file_found_main = []
    if not is_bank():
        # Find files in vault
        file_found_root = get_all_files_from_root()
        if modality == CMode.CUSTOM.name:
            file_found_main = get_all_files_from_main(True)
        else:
            file_found_main = get_all_files_from_main(False)

        # Reduce the number of notes to only those of interest
        filter_file_list_main = []
        filter_file_list_root = []
        bypassFlag = False
        if modality == CMode.ONE.name:
            filter_file_list_main.append(src)
            filter_file_list_root = file_found_root
            bypassFlag = True

        elif modality == CMode.CUSTOM.name:
            filter_file_list_main = file_found_main
            filter_file_list_root = file_found_root
            bypassFlag = True

        elif modality == CMode.GROUP.name:
            for p in file_found_root:
                if src in safe_path(p).parts:
                    filter_file_list_root.append(p)

            for p in file_found_main:
                if src in safe_path(p).parts:
                    filter_file_list_main.append(p)

        else:
            filter_file_list_main = file_found_main
            filter_file_list_root = file_found_root

        # Check of consistency if not custom
        check_inconsistency(filter_file_list_main, filter_file_list_root, bypassFlag)

    else:
        print("TODO: find file if bank")

    # Create Build dir
    create_build_dir()

    # Check system requirements
    check_precondition()

    # Create combined_file.md
    # - remove header from every files
    # - combine the files
    # - write yaml on top

    # Effective conversion

    # Remove temp files
