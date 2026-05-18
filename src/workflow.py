import sys
from pathlib import Path

from src.config import (
    CustomPaths,
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
)
from src.modes import CMode
from src.pandoc.runner import check_precondition
from src.utils import (
    convert_link_to_absolute,
    safe_path
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

    file_found_root = []
    file_found_main = []
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
        check_inconsistency(filter_file_list_main,
                            filter_file_list_root, bypassFlag)

    else:
        # Bank: files live in multiple collaborator vaults.
        # No consistency check (there is no single root to compare against).
        filter_file_list_main = get_all_files_from_bank(mode)
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
    only_used_files = [root_map[Path(name).name]
                       for name in filter_file_list_main]

    # Effective conversion
    if dst is not None:
        combine_and_execute(only_used_files, cfgCstmPath, dst)
    else:
        print("Error: No output file selected")
        sys.exit(1)


def update_bank() -> None:
    """
    Update the collaborative bank by validating collaborator links to their
    `main.md` files and composing a combined `main.md` in the bank root.
    """

    print("Updating collaborative bank...")

    bank_dir = safe_path(_BANK_DIR)
    collab_file = safe_path(bank_dir, COLLAB_FILE_NAME)
    main_bank_path = safe_path(bank_dir, MAIN_FILE_NAME)

    if not collab_file.exists():
        print(f"Error: the file '{collab_file}' does not exist.")
        sys.exit(1)

    # Read collaborator file
    with open(str(collab_file), "r", encoding="utf-8") as f:
        lines = f.readlines()

    collaborator = None
    errors: list[str] = []
    # list of (name, path_to_main.md)
    collab_mainmd: list[tuple[str, Path]] = []

    for line in lines:
        line = line.strip()
        if line.startswith("##"):
            collaborator = line[2:].strip()

        # Search for markdown link to main.md
        match = re.search(r"\[.*?\]\((.*?main\.md)\)", line)
        if match:
            main_md_path = safe_path("..", match.group(1))
            if not Path(main_md_path).exists():
                errors.append(
                    f"Collaborator '{collaborator}': main.md not found at '{main_md_path}'"
                )
            else:
                print(
                    f"Collaborator '{collaborator}': main.md found at '{main_md_path}'")
                collab_mainmd.append((collaborator or "", Path(main_md_path)))

    if errors:
        print("The following errors were found in collaborator main.md links:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("All collaborator main.md links are valid.")

    # Read each collaborator's main.md and compose the combined main.md
    with open(str(main_bank_path), "w", encoding="utf-8") as out:
        out.write("# Combined Index\n\n")
        for collaborator, main_md_path in collab_mainmd:
            out.write(f"## {collaborator}\n\n")
            with open(str(main_md_path), "r", encoding="utf-8") as mf:
                for line in mf:
                    # Skip single # titles
                    if re.match(r"^#(?!#)", line):
                        continue
                    # Convert ## to ###
                    if line.startswith("##"):
                        line = "#" + line
                    # Convert relative links to absolute ones
                    newline = convert_link_to_absolute(line, str(main_md_path))
                    out.write(newline)
                out.write("\n")

    print(f"Combined main.md updated at {main_bank_path}")
