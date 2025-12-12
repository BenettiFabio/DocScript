import sys
from pathlib import Path

from src.config import (
    CustomPaths,
    check_integrity,
    create_new_note,
    create_vault_structure,
    is_bank,
    is_vault,
)

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
