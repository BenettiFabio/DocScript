import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from src.pandoc.runner import execute_pandoc
from src.utils import (
    copy_dir_recursive,
    remove_dir,
    safe_path,
    should_skip_dir,
    should_skip_file,
    write_file,
)
from src.workflow import CMode

###############
# Description #
###############
"""
The contents of this file are all the functions
that interact with the filesystem.
"""

###########
# Defines #
###########
_PRJ_CONFIG_FILE = Path(__file__).resolve()  # /config.py
_PRJ_SRC_DIR = _PRJ_CONFIG_FILE.parent  # /src
_PRJ_ROOT_DIR = _PRJ_SRC_DIR.parent  # /DocScript
_PRJ_PARENT_DIR = _PRJ_ROOT_DIR.parent  # /MyPersonalDocs
_HOME_DIR = Path.home()

_VAULT_DIR = Path(os.path.join(_PRJ_ROOT_DIR, "..", "vault")).resolve()
_BANK_DIR = Path(os.path.join(_PRJ_ROOT_DIR, "..", "bank")).resolve()

_INITIALIZE_DIR = "initialization"
_INIT_V_DIR = "init-vault"
_INIT_B_DIR = "init-bank"
_SETUP_V_DIR = "setup-vault"
_CONFIG_DIR = "config"
_USR_CONF_DIR = "config-files"
_BUILD_DIR = "build"
_TEMPORARY_DIR = "rusco"
_ASSETS_DIR = "assets"
_DFLT_CONFIG_DIR = Path(os.path.join(_PRJ_ROOT_DIR, _CONFIG_DIR)).resolve()
_APPL_DIR = Path(os.path.join(_HOME_DIR, "Documents", "DocScript")).resolve()

COLLAB_FILE_NAME = "collaborator.md"
COMB_FILE_NAME = "combined_notes.md"
NEW_NOTE_NAME = "default-note.md"  # Name of new note file
YAML_NAME = "default-yaml.yaml"  # Name of YAML file
TEMPLATE_NAME = "default-template.tex"  # Name of TEMPLATE file
LUA_FILTER_NAME = "default-graphic.lua"  # Name of LUA FILTER file
PANDOC_OPT_NAME = "default-pandoc-opt.yaml"  # Name of PANDOC option file
CONFIG_FILE_NAME = ".conf"
MAIN_FILE_NAME = "main.md"
CUSTOM_FILE_NAME = "custom.md"

YAML_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, YAML_NAME)).resolve()
TEMPLATE_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, TEMPLATE_NAME)).resolve()
LUA_FILTER_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, LUA_FILTER_NAME)).resolve()
NEW_NOTE_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, NEW_NOTE_NAME)).resolve()
PANDOC_OPT_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, PANDOC_OPT_NAME)).resolve()

# Vault path
CONFIG_DIR_VAULT_PATH = Path(
    os.path.join(_VAULT_DIR, _CONFIG_DIR, CONFIG_FILE_NAME)
).resolve()
CONFIG_USR_V_FILES_DIR = Path(
    os.path.join(_VAULT_DIR, _CONFIG_DIR, _USR_CONF_DIR)
).resolve()
INIT_V_PATH = Path(os.path.join(_PRJ_ROOT_DIR, _INITIALIZE_DIR, _INIT_V_DIR)).resolve()
SETUP_V_PATH = Path(
    os.path.join(_PRJ_ROOT_DIR, _INITIALIZE_DIR, _SETUP_V_DIR)
).resolve()
BUILD_V_PATH = Path(os.path.join(_VAULT_DIR, _BUILD_DIR)).resolve()

# Bank path
CONFIG_DIR_BANK_PATH = Path(
    os.path.join(_BANK_DIR, _CONFIG_DIR, CONFIG_FILE_NAME)
).resolve()
CONFIG_USR_B_FILES_DIR = Path(
    os.path.join(_BANK_DIR, _CONFIG_DIR, _USR_CONF_DIR)
).resolve()
INIT_B_PATH = Path(os.path.join(_PRJ_ROOT_DIR, _INITIALIZE_DIR, _INIT_B_DIR)).resolve()
BUILD_B_PATH = Path(os.path.join(_BANK_DIR, _BUILD_DIR)).resolve()

EXCLUDED_DIRS = [
    _ASSETS_DIR,
    _BUILD_DIR,
    _CONFIG_DIR,  # ,
    # _TEMPORARY_DIR
]

EXCLUDED_FILES = [COMB_FILE_NAME, NEW_NOTE_NAME, MAIN_FILE_NAME, CUSTOM_FILE_NAME]


# Manage all the non-default path if specified
@dataclass
class CustomPaths:
    custom_teml_path: str | None = None
    custom_luaf_path: str | None = None
    custom_yaml_path: str | None = None
    custom_new_note_path: str | None = None
    custom_pandoc_opt_path: str | None = None

    def __post_init__(self) -> None:
        """
        Set Defaults if not initialized
        """
        if self.custom_teml_path is None:
            self.custom_teml_path = str(TEMPLATE_PATH)
        if self.custom_luaf_path is None:
            self.custom_luaf_path = str(LUA_FILTER_PATH)
        if self.custom_yaml_path is None:
            self.custom_yaml_path = str(YAML_PATH)
        if self.custom_new_note_path is None:
            self.custom_new_note_path = str(NEW_NOTE_PATH)
        if self.custom_pandoc_opt_path is None:
            self.custom_pandoc_opt_path = str(PANDOC_OPT_PATH)


def is_bank() -> bool:
    """
    Check if the directory is initialized like a data bank
    """

    collab_file = safe_path(_BANK_DIR, COLLAB_FILE_NAME)
    return _BANK_DIR.exists() and collab_file.exists()


def is_vault() -> bool:
    """
    Check if the directory is initialized like a vault
    """
    if os.path.exists(_VAULT_DIR):
        # Read the content of the vault directory
        vault_contents = os.listdir(_VAULT_DIR)

        # Check of an alredy initialized repository
        # don't delete what already exists
        vault_contents = [item for item in vault_contents if item != "build"]

        return bool(vault_contents)
    return False


def check_config_file(cfgCstmPath: CustomPaths) -> None:
    """
    Reads a configuration file and updates custom paths.
    It will use these paths to convert notes.
    If it finds lines in the format .flag="path/to/file".
    It will bypass any lines that don't start with `.`

    Note:   CustomPaths has default values ​​in the constructor.
            This function only overrides paths specified in the .conf file.
            Unspecified paths retain their default values.
    """

    # check to see if you are in a database or personal vault
    config_path_to_use = CONFIG_DIR_BANK_PATH if is_bank() else CONFIG_DIR_VAULT_PATH

    if not os.path.exists(config_path_to_use):
        return

    pattern = re.compile(r'^\.(\w+)\s*=\s*"([^"]+)"$')

    with open(config_path_to_use, encoding="utf-8") as conf_file:
        for line in conf_file:
            line = line.strip()

            if not line.startswith("."):
                continue

            match = pattern.match(line)
            if not match:
                continue

            key, value = match.groups()
            # I need an absolute path: I use safe_path() with two arguments
            # this way it resolves and becomes an absolute path.
            if is_bank():
                path = safe_path(_BANK_DIR, _CONFIG_DIR, value)
            else:
                path = safe_path(_VAULT_DIR, _CONFIG_DIR, value)

            if key == "template":
                cfgCstmPath.custom_teml_path = add_new_teml(path)
            elif key == "lua":
                cfgCstmPath.custom_luaf_path = add_new_luaf(path)
            elif key == "yaml":
                cfgCstmPath.custom_yaml_path = add_new_yaml(path)
            elif key == "start":
                cfgCstmPath.custom_new_note_path = add_new_start(path)
            elif key == "pandoc":
                cfgCstmPath.custom_pandoc_opt_path = add_new_yaml(path)


def check_priority_opt(
    cfgCstmPath: CustomPaths,
    yaml: str | None = None,
    template: str | None = None,
    lua: str | None = None,
    pandoc: str | None = None,
) -> None:
    """_summary_

    Args:
    yaml (Optional[str], optional): _description_. Defaults to None.
    template (Optional[str], optional): _description_. Defaults to None.
    lua (Optional[str], optional): _description_. Defaults to None.
    pandoc (Optional[str], optional): _description_. Defaults to None.

    Checks for terminal options that may change configuration paths.
    These have higher priority than the configuration file.
    """
    if template:
        cfgCstmPath.custom_teml_path = add_new_teml(template)
    elif lua:
        cfgCstmPath.custom_luaf_path = add_new_luaf(lua)
    elif yaml:
        cfgCstmPath.custom_yaml_path = add_new_yaml(yaml)
    elif pandoc:
        cfgCstmPath.custom_pandoc_opt_path = add_new_yaml(pandoc)


def add_new_yaml(yaml_file: str | Path) -> str:
    """
    Update yaml file if the format is correct
    """

    yaml_file = str(yaml_file)
    ext = os.path.splitext(yaml_file)[1].lower()
    if ext not in [".yaml"]:
        print(f"Errore: il file di input '{yaml_file}' deve avere estensione .yaml.")
        sys.exit(1)

    if not os.path.exists(yaml_file):
        print(f"Errore: il file di input '{yaml_file}' non trovato.")
        sys.exit(1)

    return yaml_file


def add_new_teml(template_file: str | Path) -> str:
    """
    Update template file if the format is correct
    """
    template_file = str(template_file)
    ext = os.path.splitext(template_file)[1].lower()
    if ext not in [".tex"]:
        print(f"Errore: il file di input '{template_file}' deve avere estensione .tex.")
        sys.exit(1)

    if not os.path.exists(template_file):
        print(f"Errore: il file di input '{template_file}' non trovato.")
        sys.exit(1)

    return template_file


def add_new_luaf(lua_file: str | Path) -> str:
    """
    Update lua filter file if the format is correct
    """
    lua_file = str(lua_file)
    ext = os.path.splitext(lua_file)[1].lower()
    if ext not in [".lua"]:
        print(f"Errore: il file di input '{lua_file}' deve avere estensione .lua.")
        sys.exit(1)

    if not os.path.exists(lua_file):
        print(f"Errore: il file di input '{lua_file}' non trovato.")
        sys.exit(1)

    return lua_file


def add_new_start(start_file: str | Path) -> str:
    """
    Update starting file if the format is correct
    """
    start_file = str(start_file)
    ext = os.path.splitext(start_file)[1].lower()
    if ext not in [".md"]:
        print(f"Errore: il file di input '{start_file}' deve avere estensione .md.")
        sys.exit(1)

    if not os.path.exists(start_file):
        print(f"Errore: il file di input '{start_file}' non trovato.")
        sys.exit(1)

    return start_file


def chose_right_position(isBank: bool, file: str) -> Path:
    """
    Returns the path to the file, choosing the vault or bank directory
    """
    if not isBank:
        return safe_path(BUILD_V_PATH, file)
    return safe_path(BUILD_B_PATH, file)


def check_integrity() -> None:
    """
    Verify the integrity of the setup folder so you can initialize
    and use the architecture.
    """
    if not os.path.exists(INIT_V_PATH):
        print(f"Errore: la cartella template '{INIT_V_PATH}' non esiste.")
        sys.exit(1)

    if not os.path.exists(_DFLT_CONFIG_DIR):
        print(
            f"Errore: la cartella dei file di config '{_DFLT_CONFIG_DIR}' non esiste."
        )
        sys.exit(1)

    if not os.path.exists(SETUP_V_PATH):
        print(f"Errore: la cartella dei file di setup '{SETUP_V_PATH}' non esiste.")
        sys.exit(1)


def create_vault_structure(BankFlag: bool = False) -> None:
    """
    Initialize the architecture starting from the initialization dir
    """
    if not BankFlag:
        # Classic Vault!
        copy_dir_recursive(INIT_V_PATH, _VAULT_DIR)
        # Write the main.md file with the first default references
        contenuto_main = """\
            # Argument 1
            
            - [ArgumentName1](main-arg1/main.main-arg1.first-note.md)
        """
        write_file(Path(os.path.join(_VAULT_DIR, "main.md")).resolve(), contenuto_main)

        # Write the custom.md file with the first default references
        contenuto_custom = """\
            <!--
                Copy here some of your file from the main.
                Pay attention to the order of notes!
            -->
            # Custom file for conversion order
        """
        write_file(
            Path(os.path.join(_VAULT_DIR, "custom.md")).resolve(), contenuto_custom
        )

        print("- Cartella vault : ok\n")

        # Create user directory for configuration files
        print("Copia dei file di configurazione per pandoc...")
        copy_dir_recursive(_DFLT_CONFIG_DIR, CONFIG_USR_V_FILES_DIR)

        # Write the .conf file with the default path
        # Usa percorsi relativi verso ./config-files nella cartella vault/config
        rel_yaml_path = Path(os.path.join("./", _USR_CONF_DIR, YAML_NAME))
        rel_template_path = Path(os.path.join("./", _USR_CONF_DIR, TEMPLATE_NAME))
        rel_lua_path = Path(os.path.join("./", _USR_CONF_DIR, LUA_FILTER_NAME))
        rel_start_path = Path(os.path.join("./", _USR_CONF_DIR, NEW_NOTE_NAME))
        rel_pandoc_path = Path(os.path.join("./", _USR_CONF_DIR, PANDOC_OPT_NAME))

        contenuto_conf = f"""\
            # default configuration - start path from config/
            .pandoc="{rel_pandoc_path}"
            .yaml="{rel_yaml_path}"
            .template="{rel_template_path}"
            .lua="{rel_lua_path}"
            .start="{rel_start_path}"
        """
        write_file(CONFIG_DIR_VAULT_PATH, contenuto_conf)

        print("- Cartella .config : ok")

        # Copy some usefull files out of vault/ dir
        copy_dir_recursive(SETUP_V_PATH, _PRJ_PARENT_DIR)
        print("- File di configurazione per VSCode : ok\n")

    else:
        # Data Bank with collaborators
        copy_dir_recursive(INIT_B_PATH, _BANK_DIR)

        # Write the custom.md file with the first default references
        contenuto_custom = """\
            <!--
                Copy here some of your file from the main.
                Pay attention to the order of notes!
            -->
            # Custom file for conversion order
        """
        write_file(
            Path(os.path.join(_BANK_DIR, "custom.md")).resolve(), contenuto_custom
        )

        print("- Struttura banca dati : ok")

        # Create user directory for configuration files
        print("Copia dei file di configurazione per pandoc...")
        copy_dir_recursive(_DFLT_CONFIG_DIR, CONFIG_USR_B_FILES_DIR)

        # Scrivo i riferimenti relativi alla cartella config-files dentro il vault
        rel_yaml_path = Path(os.path.join("./", _USR_CONF_DIR, YAML_NAME))
        rel_template_path = Path(os.path.join("./", _USR_CONF_DIR, TEMPLATE_NAME))
        rel_lua_path = Path(os.path.join("./", _USR_CONF_DIR, LUA_FILTER_NAME))
        rel_pandoc_path = Path(os.path.join("./", _USR_CONF_DIR, PANDOC_OPT_NAME))

        contenuto_conf = f"""\
            # default configuration - start path from config/
            .pandoc="{rel_pandoc_path}"
            .yaml="{rel_yaml_path}"
            .template="{rel_template_path}"
            .lua="{rel_lua_path}"
        """
        write_file(CONFIG_DIR_BANK_PATH, contenuto_conf)

        print("- Cartella .config : ok\n")

        print(
            "Tips: Per iniziare compila il file `collaborator` "
            "con i link al main.md dei tuoi collaboratori.\n"
            "Tips: Successivamente lancia un -u (--update) "
            "ed aggiorna il file main.md per vedere le note di tutti\n"
        )


def create_new_note(ConfigPath: CustomPaths, noteName: str | Path) -> None:
    """
    Create a new documentation note, with a minimal content already indented
    """

    noteName = str(noteName)

    # Usa il percorso custom se impostato, altrimenti usa il default
    starting_note = ConfigPath.custom_new_note_path

    if not os.path.exists(safe_path(str(starting_note))):
        print(f"Errore: il file template '{starting_note}' non esiste.")
        sys.exit(1)

    new_note_path = safe_path(_VAULT_DIR, noteName)

    # Check name like macro-arg/note-name.md
    macro_argomento_dir = safe_path(_VAULT_DIR, noteName.split("/")[0])
    if not os.path.exists(macro_argomento_dir) or not os.path.isdir(
        macro_argomento_dir
    ):
        print(
            f"Errore: il macro-arg '{noteName.split('/')[0]}' non esiste. "
            "Crealo manualmente prima di aggiungere note."
        )
        sys.exit(1)

    # Check consistency name
    note_name = os.path.basename(noteName)
    if not re.match(rf"^main\.{noteName.split('/')[0]}(?:\..+)?\.md$", note_name):
        print(
            f"Errore: il nome della nota '{note_name}' non è valido. "
            "Deve iniziare con 'main.macro-arg.' e terminare con '.md'."
        )
        sys.exit(1)

    # Copy template and rename
    try:
        with open(safe_path(str(starting_note)), encoding="utf-8") as template_file:
            content = template_file.read()

        with open(new_note_path, "w", encoding="utf-8") as new_note_file:
            new_note_file.write(content)

        print(f"Nota creata con successo: {new_note_path}")
    except Exception as e:
        print(f"Errore durante la creazione della nota: {e}")
        sys.exit(1)


def create_build_dir() -> None:
    """
    Create a build dir in the correct location
    """
    if not is_bank():
        if not os.path.exists(BUILD_V_PATH):
            os.makedirs(BUILD_V_PATH)
    else:
        if not os.path.exists(BUILD_B_PATH):
            os.makedirs(BUILD_B_PATH)


def get_all_files_from_root() -> list[str]:
    """
    Read all the files .md in the vault
    """
    matched_files = []

    for root, dirs, files in os.walk(_VAULT_DIR):
        dirs[:] = [d for d in dirs if not should_skip_dir(d, EXCLUDED_DIRS)]

        for file in files:
            if not file.endswith(".md"):
                continue
            if should_skip_file(file, EXCLUDED_FILES):
                continue

            full_path = os.path.join(root, file)
            matched_files.append(str(full_path))

    return matched_files


def get_all_files_from_main(mode: CMode) -> list[str]:
    """
    Read the main.md file (or custom.md)
    and return a list of all .md files specified
    """

    modality = mode.name
    custom = False
    if modality == CMode.CUSTOM.name:
        main_md_path = _VAULT_DIR / CUSTOM_FILE_NAME
        custom = True
    else:
        main_md_path = _VAULT_DIR / MAIN_FILE_NAME

    # Check if exists
    if not os.path.exists(main_md_path):
        if custom:
            print(
                "Errore: il file custom.md non è stato trovato "
                f"in {os.path.dirname(main_md_path)} ."
            )
        else:
            print(
                "Errore: il file main.md non è stato trovato "
                f"in {os.path.dirname(main_md_path)} ."
            )
        sys.exit(1)

    # Read the content
    with open(main_md_path, encoding="utf-8") as main_md_file:
        main_md_content = main_md_file.readlines()

    # Take the link of notes
    matching_files = []
    for line in main_md_content:
        if (
            "(" in line
            and ")" in line
            # Cerca i link che iniziano con l'argomento "(argomento/nome-nota.md)"
        ):
            start_idx = line.find("(") + 1
            end_idx = line.find(")")
            if start_idx != -1 and end_idx != -1:
                file_path = line[start_idx:end_idx]
                if file_path.endswith(".md"):
                    matching_files.append(file_path)

    # If void file exit
    if not matching_files:
        print(f"Errore: nessun file trovato in {'custom.md' if custom else 'main.md'}.")
        sys.exit(1)

    return matching_files


def get_all_files_from_bank(mode: CMode) -> list[str]:
    """
    Reads collaborator.md to build a map  name → collaborator main.md path.
    Then reads the bank main.md (or custom.md) to know which notes to include
    and in which order.
    Returns a list of absolute paths resolved inside each collaborator's vault.
    """

    collab_file = safe_path(_BANK_DIR, COLLAB_FILE_NAME)
    if not collab_file.exists():
        print(f"Errore: '{collab_file}' non trovato.")
        sys.exit(1)

    # 1. collaborator.md  →  { name: absolute path of their main.md }
    all_collaborators: dict[str, str] = {}
    current_name: str | None = None

    with open(collab_file, encoding="utf-8") as cf:
        for line in cf:
            line = line.strip()
            if line.startswith("##"):
                current_name = line[2:].strip()
            match = re.search(r"\[.*?\]\((.*?\.md)\)", line)
            if match and current_name:
                raw = match.group(1)
                abs_main = safe_path(_BANK_DIR, raw)
                if not abs_main.exists():
                    print(
                        f"Errore: main.md di '{current_name}' "
                        f"non trovato in '{abs_main}'."
                    )
                    sys.exit(1)
                all_collaborators[current_name] = str(abs_main)

    # 2. bank main.md / custom.md  →  sections and note links
    if mode == CMode.CUSTOM:
        index_file = safe_path(_BANK_DIR, CUSTOM_FILE_NAME)
    else:
        index_file = safe_path(_BANK_DIR, MAIN_FILE_NAME)

    if not index_file.exists():
        print(f"Errore: '{index_file}' non trovato.")
        sys.exit(1)

    # Collect only the collaborators actually listed in the index file
    active_collaborators: list[str] = []
    with open(index_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("##") or line.startswith("#"):
                name = line.lstrip("#").strip()
                if name in all_collaborators:
                    active_collaborators.append(name)

    # 3. Resolve each note to an absolute path in the collaborator vault
    matching_files: list[str] = []
    current_collab: str | None = None

    with open(index_file, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if stripped.startswith("##") or stripped.startswith("#"):
                current_collab = stripped.lstrip("#").strip()
                continue

            note_match = re.search(r"\[.*?\]\(([^)]+\.md)\)", stripped)
            if note_match and current_collab in active_collaborators:
                note_rel = note_match.group(1)
                collab_main = all_collaborators.get(current_collab)

                if not collab_main:
                    print(
                        f"Attenzione: '{current_collab}' non in collaborator.md, skip."
                    )
                    continue

                note_abs = safe_path(os.path.dirname(collab_main), note_rel)

                if note_abs.exists():
                    matching_files.append(str(note_abs))
                else:
                    print(
                        f"Attenzione: nota '{note_rel}' di '{current_collab}' "
                        f"non trovata in '{note_abs}', skip."
                    )

    if not matching_files:
        label = CUSTOM_FILE_NAME if mode == CMode.CUSTOM else MAIN_FILE_NAME
        print(f"Errore: nessun file trovato in '{label}'.")
        sys.exit(1)

    return matching_files


def check_inconsistency(
    matching_files_main: list[str], matching_files_root: list[str], bypassFlag: bool
) -> None:
    """
    Check that all actual files are referenced in main.
    If any notes are missing from main, print an error with the missing files.
    Paths are normalized for comparison.
    """

    if not bypassFlag:

        # Filter “root” files (all .md files in the vault)
        filtered_matching_files_root = [
            Path(path).name
            for path in matching_files_root
            if not path.startswith(f"{_TEMPORARY_DIR}/")
            and not Path(path).name.startswith(f"main.{_TEMPORARY_DIR}.")
        ]

        # Normalize lists (file names only)
        normalized_actual_list = [
            Path(path).name for path in filtered_matching_files_root
        ]

        normalized_main_list: list[str] = [
            Path(path).name for path in matching_files_main
        ]

        main_set = set(normalized_main_list)
        actual_set = set(normalized_actual_list)

        missing_in_main = actual_set - main_set

        if missing_in_main:
            print("Errore: i seguenti file .md NON sono inclusi nel main:")
            for f in sorted(missing_in_main):
                print(f"- {f}")
            sys.exit(1)
    else:
        # Check only the existence of files (file names only)

        # root is the entire vault (_TEMPORARY_DIR included)
        normalized_actual_list = [str(Path(path)) for path in matching_files_root]
        normalized_main_list = [Path(path).name for path in matching_files_main]
        path_by_name = {Path(p).name: p for p in normalized_actual_list}

        for filename in normalized_main_list:
            # check the file name if found in root
            if filename not in path_by_name:
                print(f"Errore: file {filename} non presente nel vault")
                sys.exit(1)

            full_path = path_by_name[filename]

            # check if exists in root
            if not Path(full_path).exists():
                print(f"Errore: file {full_path} non trovato su filesystem")
                sys.exit(1)


def combine_and_execute(
    matching_files: list[str],
    cfgCstmPath: CustomPaths,
    dst: str,
) -> None:
    """
    Combines all notes into a single .md file, removes the standard header
    from each, prepends the YAML block, then runs the pandoc conversion.

    Vault:  conversion runs directly in the vault build folder.
    Bank:   files are staged in _APPL_DIR (local), converted there,
            the result is copied back to the bank build folder,
            then _APPL_DIR is deleted entirely.

    In both cases the build folder is cleaned afterwards,
    keeping only .md / .tex / .pdf files.
    """

    # 1. Combine notes
    unified = chose_right_position(is_bank(), COMB_FILE_NAME)
    dst_path = chose_right_position(is_bank(), dst)

    with open(unified, "w", encoding="utf-8") as out:
        for file in matching_files:
            if os.path.exists(file):
                out.writelines(remove_std_header(Path(file)))
                out.write("\n")
            else:
                print(f"Avviso: '{file}' non trovato, sarà ignorato.")

    # 1.1. Attach the yaml from config files
    copy_config_yaml(unified, cfgCstmPath)
    print(f"File combinato creato: {unified}")

    # 2. Resolve base paths
    vault_dir = str(_BANK_DIR) if is_bank() else str(_VAULT_DIR)
    assets_dir = str(safe_path(vault_dir, _ASSETS_DIR))
    build_dir = BUILD_B_PATH if is_bank() else BUILD_V_PATH

    # 3a. Vault: direct conversion
    if not is_bank():
        execute_pandoc(
            str(cfgCstmPath.custom_teml_path),
            str(cfgCstmPath.custom_luaf_path),
            str(cfgCstmPath.custom_pandoc_opt_path),
            unified,
            dst_path,
            vault_dir,
            assets_dir,
            str(build_dir),
        )

    # 3b. Bank: stage → convert locally → copy back → cleanup
    else:
        app_dir = safe_path(_APPL_DIR)
        app_build = app_dir / _BUILD_DIR
        app_config = app_dir / _CONFIG_DIR
        app_assets = app_dir / _ASSETS_DIR

        app_build.mkdir(parents=True, exist_ok=True)
        app_config.mkdir(parents=True, exist_ok=True)

        # -- Copy combined note --
        local_unified = app_build / unified.name
        shutil.copy2(unified, local_unified)

        # -- Copy assets --
        if app_assets.exists():
            shutil.rmtree(app_assets)
        if os.path.exists(assets_dir):
            shutil.copytree(assets_dir, app_assets)

        # -- Copy config files (renamed to default names so execute_pandoc
        #    doesn't need to know which custom file is in use) --
        shutil.copy2(str(cfgCstmPath.custom_teml_path), app_config / TEMPLATE_NAME)
        shutil.copy2(str(cfgCstmPath.custom_luaf_path), app_config / LUA_FILTER_NAME)
        shutil.copy2(
            str(cfgCstmPath.custom_pandoc_opt_path), app_config / PANDOC_OPT_NAME
        )

        # -- Convert locally --
        local_dst = app_build / Path(dst_path).name

        execute_pandoc(
            str(app_config / TEMPLATE_NAME),
            str(app_config / LUA_FILTER_NAME),
            str(app_config / PANDOC_OPT_NAME),
            local_unified,
            local_dst,
            str(app_dir),
            str(app_assets),
            str(app_build),
        )

        # -- Copy result back to bank build --
        if local_dst.exists():
            shutil.copy2(local_dst, dst_path)
        else:
            print(f"Attenzione: output '{local_dst}' non trovato dopo la conversione.")

        # -- Delete _APPL_DIR entirely --
        remove_dir(app_dir)

    # Remove temp files
    clean_build_dir(build_dir)


def remove_std_header(filePath: Path) -> list[str]:
    """
    Reads a md file, return the content without the specified header.
    Do not modify any other rows.
    """
    if not os.path.exists(filePath):
        print(f"Errore: il file '{filePath}' non esiste.")
        sys.exit(1)

    # Read all the file
    with open(filePath, encoding="utf-8") as file:
        lines = file.readlines()

    # Remove header rows
    content_started = False
    filtered_lines = []
    for line in lines:
        if "<!-- /code_chunk_output -->" in line:
            content_started = True
            continue
        if content_started:
            filtered_lines.append(line)

    # If the header does not exists, return the entire content
    if not content_started:
        return lines

    return filtered_lines


def copy_config_yaml(CombinedPath: Path, cfgCstmPath: CustomPaths) -> None:
    """
    Copy the YAML from the config/.conf file in the specified file
    Paste this YAML to the top of combined_notes_path
    """

    try:
        # Legge il contenuto del file config/my_yaml.yaml
        with open(str(cfgCstmPath.custom_yaml_path), encoding="utf-8") as f:
            content = f.read()

        yaml_block = None
        # Se il file inizia con '---' cerco il marcatore di chiusura ('---' o '...')
        if content.lstrip().startswith("---"):
            # Trova il primo marcatore di chiusura che compare su una linea a parte
            m = re.search(r"\n(---|\.\.\.)(?:\r?\n)", content)
            if m:
                yaml_block = content[: m.end()]

        if yaml_block:
            # Legge il contenuto attuale del file combined_notes.md
            with open(CombinedPath, encoding="utf-8") as f:
                combined_content = f.read()

            # Se il file combined_notes.md ha già un blocco YAML lo rimuovo
            if combined_content.lstrip().startswith("---"):
                m2 = re.search(r"\n(---|\.\.\.)(?:\r?\n)", combined_content)
                if m2:
                    combined_content = combined_content[m2.end() :].lstrip()

            # Aggiunge il nuovo blocco YAML all'inizio
            new_content = f"{yaml_block}\n\n{combined_content}"

            # Scrive il nuovo contenuto nel file combined_notes.md
            with open(CombinedPath, "w", encoding="utf-8") as f:
                f.write(new_content)

        else:
            print(f"Nessun blocco YAML trovato in {cfgCstmPath.custom_yaml_path}")

    except Exception as e:
        print(f"Errore durante la copia del blocco YAML: {str(e)}")


def clean_build_dir(build_dir: Path) -> None:
    """
    Removes from build_dir every file whose extension is not
    .md, .tex or .pdf (e.g. latexmk artefacts: .aux, .log, .fls, …).
    Subdirectories are left untouched.
    """
    allowed = {".md", ".tex", ".pdf"}

    if not build_dir.exists():
        return

    for item in build_dir.iterdir():
        if item.is_file() and item.suffix.lower() not in allowed:
            try:
                item.unlink()
                print(f"Rimosso artefatto: {item.name}")
            except Exception as exc:
                print(f"Attenzione: impossibile rimuovere '{item.name}': {exc}")
