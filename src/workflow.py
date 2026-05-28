import sys
from pathlib import Path

from src.config import (
    CustomPaths,
    BuildOptions,
    check_inconsistency,
    check_integrity,
    combine_and_execute,
    create_build_dir,
    create_new_note,
    create_vault_structure,
    get_all_files_from_bank,
    get_all_files_from_main,
    get_all_files_from_root,
    is_bank,
    is_vault,
    update_bank_files,
)
from src.modes import CMode
from src.pandoc.runner import check_precondition
from src.utils import safe_path

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
    Initialize the Vault (or the Bank) Structure
    """

    if is_bank():
        print("Error: The current folder is already initialized as a Bank.")
        sys.exit(1)

    if is_vault():
        print("Error: The current folder is already initialized as a Vault.")
        sys.exit(1)

    try:
        # Verify the DocScript infrastructure before copying necessary files
        check_integrity()

        if not bankFlag:
            print("Starting Vault creation...")
        else:
            print("Starting Bank creation...")

        create_vault_structure(bankFlag)

        print("Structure built successfully!\n")
        if not bankFlag:
            print("Enjoy your new Vault! <3")
        else:
            print("Enjoy working with your team mates! <3")

    except Exception as e:
        print(f"Error while building the Vault: {e}")
        sys.exit(1)


def start_note(ConfigPath: CustomPaths, noteName: str | Path) -> None:
    """
    Insert in the chosen path a new indented basic file.
    Is necessary to respect the infrastructure rules and the file format.
    """

    noteName = str(noteName)

    if is_bank():
        print("Error: You can add a note only in a private Vault")
        sys.exit(1)

    try:
        check_integrity()

        create_new_note(ConfigPath, noteName)

    except Exception as e:
        print(f"Error while creating the new note: {e}")
        sys.exit(1)


def conversion_procedure(
    mode: CMode,
    cfgCstmPath: CustomPaths,
    buildOpts: BuildOptions,
    src: str | None = None,
    dst: str | None = None,
) -> None:
    """
    Start a conversion with a single or multiple files, into a .pdf or .tex
    The file will be generated in build/

    Note:
    - Files will be searched within the local vault for personal use
    - Files will be searched within all collaborators' vaults
    for database use
    """

    # Check modality
    modality = mode.name
    if modality is CMode.NONE.name:
        print("Error: Conversion request not applicable")
        sys.exit(0)

    file_found_root: list[str] = []
    file_found_main: list[str] = []
    collaborators: dict[str, str] = {}
    if not is_bank():
        # Find files in vault
        file_found_root = get_all_files_from_root()
        file_found_main = get_all_files_from_main(mode)

        # Reduce the number of notes to only those of interest
        filter_file_list_main: list[str] = []
        filter_file_list_root: list[str] = []
        bypassFlag = False
        if modality == CMode.ONE.name:
            if src is not None:
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
        # Bank: files live in multiple collaborator vaults.
        # No consistency check (there is no single root to compare against).
        filter_file_list_main, collaborators = get_all_files_from_bank(mode)
        # For the bank case the main list already carries absolute paths,
        # so root and main can be the same list: the root_map below will
        # resolve correctly (filename → absolute path).
        filter_file_list_root = filter_file_list_main
        bypassFlag = True

    # Create Build dir
    create_build_dir()

    # Check system requirements
    check_precondition()

    # Create a list for combined_file.md
    root_map = {Path(p).name: p for p in filter_file_list_root}
    only_used_files = [root_map[Path(name).name] for name in filter_file_list_main]

    # Effective conversion
    if dst is not None:
        combine_and_execute(only_used_files, collaborators, cfgCstmPath, buildOpts, dst)
    else:
        print("Error: No output file selected")
        sys.exit(1)


def update_bank() -> None:
    """
    Update the collaborative bank by validating collaborator links to their
    `main.md` files and composing a combined `main.md` in the bank root.
    """

    update_bank_files()
