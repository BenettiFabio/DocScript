import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from src.utils import (
    copy_dir_recursive,
    safe_path,
    should_skip_dir,
    should_skip_file,
    write_file,
)

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

EXCLUDED_DIRS = [_ASSETS_DIR, _BUILD_DIR, _CONFIG_DIR, _TEMPORARY_DIR]

EXCLUDED_FILES = [COMB_FILE_NAME, NEW_NOTE_NAME, MAIN_FILE_NAME, CUSTOM_FILE_NAME]


# Manage all the non-default path if specified
@dataclass
class CustomPaths:
    custom_teml_path: str | None = None
    custom_luaf_path: str | None = None
    custom_yaml_path: str | None = None
    custom_new_note_path: str | None = None
    custom_pandoc_opt_path: str | None = None


def is_bank() -> bool:
    collab_file = safe_path(_BANK_DIR, COLLAB_FILE_NAME)
    return _BANK_DIR.exists() and collab_file.exists()


def is_vault() -> bool:
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
    start_file = str(start_file)
    ext = os.path.splitext(start_file)[1].lower()
    if ext not in [".md"]:
        print(f"Errore: il file di input '{start_file}' deve avere estensione .md.")
        sys.exit(1)

    if not os.path.exists(start_file):
        print(f"Errore: il file di input '{start_file}' non trovato.")
        sys.exit(1)

    return start_file


def check_integrity() -> None:
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
    noteName = str(noteName)

    # Check path
    if CustomPaths.custom_new_note_path:
        starting_note = ConfigPath.custom_new_note_path
    else:
        starting_note = str(NEW_NOTE_PATH)

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


def get_all_files_from_main(custom: bool) -> list[str]:
    """
    Read the main.md file (or custom.md)
    and return a list of all .md files specified
    """

    if custom:
        main_md_path = _VAULT_DIR / CUSTOM_FILE_NAME
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
            "(" in line and ")" in line
        ):  # Cerca i link che iniziano con l'argomento "(argomento/nome-nota.md)"
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


def check_inconsistency(
    matching_files_main: list[str], matching_files_root: list[str]
) -> None:
    """
    Check that all actual files are referenced in main.
    If any notes are missing from main, print an error with the missing files.
    Paths are normalized for comparison.
    """

    # -----------------------------------------------------------------
    # Filter “root” files (all .md files in the vault)
    # -----------------------------------------------------------------
    filtered_matching_files_root = [
        Path(path).name
        for path in matching_files_root
        if not path.startswith(f"{_TEMPORARY_DIR}/")
        and not Path(path).name.startswith(f"main.{_TEMPORARY_DIR}.")
    ]

    # -----------------------------------------------------------------
    # Normalize lists (file names only)
    # -----------------------------------------------------------------
    normalized_actual_list = [Path(path).name for path in filtered_matching_files_root]

    normalized_main_list = [Path(path).name for path in matching_files_main]

    main_set = set(normalized_main_list)
    actual_set = set(normalized_actual_list)

    missing_in_main = actual_set - main_set

    if missing_in_main:
        print("Errore: i seguenti file .md NON sono inclusi nel main:")
        for f in sorted(missing_in_main):
            print(f"- {f}")
        sys.exit(1)
