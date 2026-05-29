import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from src.modes import CMode
from src.pandoc.runner import execute_pandoc
from src.utils import (
    convert_link_to_absolute,
    copy_dir_recursive,
    normalize_unc_path,
    remove_dir,
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
_APPL_NAME = "DocScript"

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
_APPL_DIR = Path(os.path.join(_HOME_DIR, "Documents", _APPL_NAME)).resolve()

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
LUA_FILTER_PATH = Path(os.path.join(
    _DFLT_CONFIG_DIR, LUA_FILTER_NAME)).resolve()
NEW_NOTE_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, NEW_NOTE_NAME)).resolve()
PANDOC_OPT_PATH = Path(os.path.join(
    _DFLT_CONFIG_DIR, PANDOC_OPT_NAME)).resolve()

# Vault path
CONFIG_DIR_VAULT_PATH = Path(
    os.path.join(_VAULT_DIR, _CONFIG_DIR, CONFIG_FILE_NAME)
).resolve()
CONFIG_USR_V_FILES_DIR = Path(
    os.path.join(_VAULT_DIR, _CONFIG_DIR, _USR_CONF_DIR)
).resolve()
INIT_V_PATH = Path(os.path.join(
    _PRJ_ROOT_DIR, _INITIALIZE_DIR, _INIT_V_DIR)).resolve()
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
INIT_B_PATH = Path(os.path.join(
    _PRJ_ROOT_DIR, _INITIALIZE_DIR, _INIT_B_DIR)).resolve()
BUILD_B_PATH = Path(os.path.join(_BANK_DIR, _BUILD_DIR)).resolve()

EXCLUDED_DIRS = [
    _ASSETS_DIR,
    _BUILD_DIR,
    _CONFIG_DIR,  # ,
    # _TEMPORARY_DIR
]

EXCLUDED_FILES = [COMB_FILE_NAME, NEW_NOTE_NAME,
                  MAIN_FILE_NAME, CUSTOM_FILE_NAME]


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


@dataclass
class BuildOptions:
    title: str | None = None
    yaml: str | None = None
    template: str | None = None
    lua: str | None = None
    pandoc: str | None = None


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


def apply_build_overrides(
    cfgCstmPath: CustomPaths,
    buildOpts: BuildOptions,
) -> None:
    """
    Override configuration paths using CLI build options.

    CLI options always have higher priority than config file values.
    """

    if buildOpts.template:
        cfgCstmPath.custom_teml_path = add_new_teml(buildOpts.template)

    if buildOpts.lua:
        cfgCstmPath.custom_luaf_path = add_new_luaf(buildOpts.lua)

    if buildOpts.yaml:
        cfgCstmPath.custom_yaml_path = add_new_yaml(buildOpts.yaml)

    if buildOpts.pandoc:
        cfgCstmPath.custom_pandoc_opt_path = add_new_yaml(buildOpts.pandoc)


def add_new_yaml(yaml_file: str | Path) -> str:
    """
    Update yaml file if the format is correct
    """

    yaml_file = str(yaml_file)
    ext = os.path.splitext(yaml_file)[1].lower()
    if ext not in [".yaml"]:
        print(f"Error: Input file '{yaml_file}' must be .yaml.")
        sys.exit(1)

    if not os.path.exists(yaml_file):
        print(f"Error: Infut file '{yaml_file}' not found.")
        sys.exit(1)

    return yaml_file


def add_new_teml(template_file: str | Path) -> str:
    """
    Update template file if the format is correct
    """
    template_file = str(template_file)
    ext = os.path.splitext(template_file)[1].lower()
    if ext not in [".tex"]:
        print(f"Error: Input file '{template_file}' must be .tex.")
        sys.exit(1)

    if not os.path.exists(template_file):
        print(f"Error: Input file '{template_file}' not found.")
        sys.exit(1)

    return template_file


def add_new_luaf(lua_file: str | Path) -> str:
    """
    Update lua filter file if the format is correct
    """
    lua_file = str(lua_file)
    ext = os.path.splitext(lua_file)[1].lower()
    if ext not in [".lua"]:
        print(f"Error: Input file '{lua_file}' must be .lua.")
        sys.exit(1)

    if not os.path.exists(lua_file):
        print(f"Error: Input file '{lua_file}' not found.")
        sys.exit(1)

    return lua_file


def add_new_start(start_file: str | Path) -> str:
    """
    Update starting file if the format is correct
    """
    start_file = str(start_file)
    ext = os.path.splitext(start_file)[1].lower()
    if ext not in [".md"]:
        print(f"Error: Input file '{start_file}' must be .md.")
        sys.exit(1)

    if not os.path.exists(start_file):
        print(f"Error: Input file '{start_file}' not found.")
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
        print(f"Error: Template directory: '{INIT_V_PATH}' does not exists.")
        sys.exit(1)

    if not os.path.exists(_DFLT_CONFIG_DIR):
        print(
            f"Error: config directory: '{_DFLT_CONFIG_DIR}' does not exists.")
        sys.exit(1)

    if not os.path.exists(SETUP_V_PATH):
        print(f"Error: setup directory: '{SETUP_V_PATH}' does not exists.")
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
        write_file(Path(os.path.join(_VAULT_DIR, "main.md")
                        ).resolve(), contenuto_main)

        # Write the custom.md file with the first default references
        contenuto_custom = """\
            <!--
                Copy here some of your file from the main.
                Pay attention to the order of notes!
            -->
            # Custom file for conversion order
        """
        write_file(
            Path(os.path.join(_VAULT_DIR, "custom.md")
                 ).resolve(), contenuto_custom
        )

        print("- Vault Dir : ok\n")

        # Create user directory for configuration files
        print("Copying the pandoc configuration files...")
        copy_dir_recursive(_DFLT_CONFIG_DIR, CONFIG_USR_V_FILES_DIR)

        # Write the .conf file with the default path
        # Use relative paths to ./config-files in the vault/config folder
        rel_yaml_path = Path(os.path.join("./", _USR_CONF_DIR, YAML_NAME))
        rel_template_path = Path(os.path.join(
            "./", _USR_CONF_DIR, TEMPLATE_NAME))
        rel_lua_path = Path(os.path.join("./", _USR_CONF_DIR, LUA_FILTER_NAME))
        rel_start_path = Path(os.path.join("./", _USR_CONF_DIR, NEW_NOTE_NAME))
        rel_pandoc_path = Path(os.path.join(
            "./", _USR_CONF_DIR, PANDOC_OPT_NAME))

        contenuto_conf = f"""\
            # default configuration - start path from config/
            .pandoc="{rel_pandoc_path}"
            .yaml="{rel_yaml_path}"
            .template="{rel_template_path}"
            .lua="{rel_lua_path}"
            .start="{rel_start_path}"
        """
        write_file(CONFIG_DIR_VAULT_PATH, contenuto_conf)

        print("- .config Dir : ok")

        # Copy some usefull files out of vault/ dir
        copy_dir_recursive(SETUP_V_PATH, _PRJ_PARENT_DIR)
        print("- VSCode Configuration files : ok\n")

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
            Path(os.path.join(_BANK_DIR, "custom.md")
                 ).resolve(), contenuto_custom
        )

        print("- Data Bank Structure : ok")

        # Create user directory for configuration files
        print("Copying the pandoc configuration files...")
        copy_dir_recursive(_DFLT_CONFIG_DIR, CONFIG_USR_B_FILES_DIR)

        # I write the references relating to the config-files folder inside the vault
        rel_yaml_path = Path(os.path.join("./", _USR_CONF_DIR, YAML_NAME))
        rel_template_path = Path(os.path.join(
            "./", _USR_CONF_DIR, TEMPLATE_NAME))
        rel_lua_path = Path(os.path.join("./", _USR_CONF_DIR, LUA_FILTER_NAME))
        rel_pandoc_path = Path(os.path.join(
            "./", _USR_CONF_DIR, PANDOC_OPT_NAME))

        contenuto_conf = f"""\
            # default configuration - start path from config/
            .pandoc="{rel_pandoc_path}"
            .yaml="{rel_yaml_path}"
            .template="{rel_template_path}"
            .lua="{rel_lua_path}"
        """
        write_file(CONFIG_DIR_BANK_PATH, contenuto_conf)

        print("- .config Dir : ok\n")

        print(
            "Tips: To get started, fill out the `collaborator` file "
            "with links to your collaborators' main.md files.\n"
            "Tips: Then run a -u (--update) "
            "and update the main.md file to see everyone's notes.\n"
        )


def create_new_note(ConfigPath: CustomPaths, noteName: str | Path) -> None:
    """
    Create a new documentation note, with a minimal content already indented
    """

    noteName = str(noteName)

    # Set the custom path, use the default instead
    starting_note = ConfigPath.custom_new_note_path

    if not os.path.exists(safe_path(str(starting_note))):
        print(f"Error: Template file '{starting_note}' does not exist.")
        sys.exit(1)

    new_note_path = safe_path(_VAULT_DIR, noteName)

    # Check name like macro-arg/note-name.md
    macro_argomento_dir = safe_path(_VAULT_DIR, noteName.split("/")[0])
    if not os.path.exists(macro_argomento_dir) or not os.path.isdir(
        macro_argomento_dir
    ):
        print(
            f"Error: The macro-arg '{noteName.split('/')[0]}' does not exist. "
            "Create it before adding a note"
        )
        sys.exit(1)

    # Check consistency name
    note_name = os.path.basename(noteName)
    if not re.match(rf"^main\.{noteName.split('/')[0]}(?:\..+)?\.md$", note_name):
        print(
            f"Error: The note name '{note_name}' is invalid. "
            "Must start with 'main.macro-arg.' and end with '.md'."
        )
        sys.exit(1)

    # Copy template and rename
    try:
        with open(safe_path(str(starting_note)), encoding="utf-8") as template_file:
            content = template_file.read()

        with open(new_note_path, "w", encoding="utf-8") as new_note_file:
            new_note_file.write(content)

        print(f"Note created successfully: {new_note_path}")
    except Exception as e:
        print(f"Error creating note: {e}")
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


def _is_sub_main(file_path: str) -> bool:
    """
    Check if a file is a sub-main.md file.
    Pattern: folder/main.folder.*.md
    """
    filename = file_path.split("/")[-1]

    pattern = r"^main\.[^.]+\.[^.]+(?:\.[^.]+)*\.main\.md$"

    return re.match(pattern, filename) is not None


def _extract_markdown_links(line: str) -> list[str]:
    """
    Extract markdown links from a line.

    Example:
        [Title](path/file.md)
    """

    matches = re.findall(r"\[[^\]]*\]\(([^)]+\.md)\)", line)

    return matches


def _read_main_files_recursive(
    mainMdPath: Path, vaultBase: Path, visited: set[str] | None = None
) -> list[str]:
    """
    Recursively expands sub-main markdown files inline.

    Supports:
        - legacy flat structure
        - recursive sub-main structure

    Prevents:
        - directory opening
        - invalid recursion
        - infinite loops
    """

    if visited is None:
        visited = set()

    # Prevent infinite recursion
    abs_path = str(safe_path(mainMdPath))

    if abs_path in visited:
        return []

    visited.add(abs_path)

    # Must exist
    if not mainMdPath.exists():
        return []

    # MUST be a file
    if not mainMdPath.is_file():
        return []

    # MUST be markdown
    if mainMdPath.suffix != ".md":
        return []

    # Read markdown safely
    with open(mainMdPath, encoding="utf-8") as main_md_file:
        main_md_content = main_md_file.readlines()

    matching_files: list[str] = []

    main_dir = mainMdPath.parent

    for line in main_md_content:

        markdown_links = _extract_markdown_links(line)

        for file_path in markdown_links:

            # Resolve relative path
            resolved_path = safe_path(
                normalize_unc_path(
                    str(safe_path(main_dir, str(file_path)).resolve()))
            )

            # Skip invalid paths
            if not resolved_path.exists():
                continue

            # Prevent opening directories
            if not resolved_path.is_file():
                continue

            # Skip non-markdown
            if resolved_path.suffix != ".md":
                continue

            # Expand recursively if sub-main
            if _is_sub_main(resolved_path.name):

                sub_files = _read_main_files_recursive(
                    resolved_path, vaultBase, visited
                )

                matching_files.extend(sub_files)

            else:
                matching_files.append(str(resolved_path))

    return matching_files


def get_all_files_from_main(mode: CMode) -> list[str]:
    """
    Read the main.md file (or custom.md)
    and return a list of all .md files specified.
    Recursively expands sub-main.md files while maintaining order.
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
                "Error: The custom.md file was not found "
                f"in {os.path.dirname(main_md_path)}."
            )
        else:
            print(
                "Error: The main.md file was not found "
                f"in {os.path.dirname(main_md_path)} ."
            )
        sys.exit(1)

    # Read files recursively, expanding sub-mains
    matching_files = _read_main_files_recursive(main_md_path, _VAULT_DIR)

    # If void file exit
    if not matching_files:
        print(
            f"Error: No files found in {'custom.md' if custom else 'main.md'}.")
        sys.exit(1)

    return matching_files


def get_all_files_from_bank(mode: CMode) -> tuple[list[str], dict[str, str]]:
    """
    Reads collaborator.md to build a map  name → collaborator main.md path.
    Then reads the bank main.md (or custom.md) to know which notes to include
    and in which order.
    Returns a list of absolute paths resolved inside each collaborator's vault
    and a dictionary of active collaborators.
    """

    collab_file = safe_path(_BANK_DIR, COLLAB_FILE_NAME)
    if not collab_file.exists():
        print(f"Error: '{collab_file}' not found.")
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
                        f"Error: main.md of '{current_name}' "
                        f"not found in '{abs_main}'."
                    )
                    sys.exit(1)
                all_collaborators[current_name] = str(abs_main)

    # 2. bank main.md / custom.md  →  sections and note links
    if mode == CMode.CUSTOM:
        index_file = safe_path(_BANK_DIR, CUSTOM_FILE_NAME)
    else:
        index_file = safe_path(_BANK_DIR, MAIN_FILE_NAME)

    if not index_file.exists():
        print(f"Error: '{index_file}' not found.")
        sys.exit(1)

    # Collect only the collaborators actually listed in the index file
    active_collaborators: list[str] = []
    with open(index_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("##") or line.startswith("#"):
                name = line.lstrip("#").strip()
                if name in all_collaborators and name not in active_collaborators:
                    active_collaborators.append(name)

    active_collaborators_map = {
        name: all_collaborators[name] for name in active_collaborators
    }

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
            if note_match and current_collab in active_collaborators_map:
                note_rel = note_match.group(1)
                collab_main = active_collaborators_map.get(current_collab)

                if not collab_main:
                    print(
                        f"Warning: '{current_collab}' not in collaborator.md, skip.")
                    continue

                note_abs = safe_path(os.path.dirname(collab_main), note_rel)

                if note_abs.exists():
                    note_path = Path(note_abs)

                    if _is_sub_main(note_path.name):
                        matching_files.extend(
                            _read_main_files_recursive(
                                note_path,
                                Path(os.path.dirname(collab_main)),
                            )
                        )
                    else:
                        matching_files.append(str(note_path))
                else:
                    print(
                        f"Warning: Note '{note_rel}' from '{current_collab}'"
                        f"not found in '{note_abs}', skip."
                    )

    if not matching_files:
        label = CUSTOM_FILE_NAME if mode == CMode.CUSTOM else MAIN_FILE_NAME
        print(f"Error: No file found in '{label}'.")
        sys.exit(1)

    return matching_files, active_collaborators_map


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

        missing_in_main = {f for f in missing_in_main if not _is_sub_main(f)}

        if missing_in_main:
            print("Error: The following .md files are NOT included in main:")
            for f in sorted(missing_in_main):
                print(f"- {f}")
            sys.exit(1)
    else:
        # Check only the existence of files (file names only)

        # root is the entire vault (_TEMPORARY_DIR included)
        normalized_actual_list = [str(Path(path))
                                  for path in matching_files_root]
        normalized_main_list = [
            Path(path).name for path in matching_files_main]
        path_by_name = {Path(p).name: p for p in normalized_actual_list}

        for filename in normalized_main_list:
            # check the file name if found in root
            if filename not in path_by_name:
                print(f"Error: File: {filename} does not exist in the vault")
                sys.exit(1)

            full_path = path_by_name[filename]

            # check if exists in root
            if not Path(full_path).exists():
                print(f"Error: File {full_path} not found in the filesystem")
                sys.exit(1)


def copy_assets(output_dir: str, collaborators: dict[str, str]) -> None:
    """
    Copy the assets directories of all collaborators into output_dir.
    If multiple collaborators use the same asset subfolders, the contents are
    merged without overwriting unchanged files.
    """
    for name, main_md_path in collaborators.items():
        collab_assets_dir = os.path.join(
            os.path.dirname(main_md_path), "assets")
        if os.path.exists(collab_assets_dir):
            copy_dir_recursive(collab_assets_dir, output_dir)
            print(f"Assets copied for {name} into {output_dir}")
        else:
            print(
                f"Warning: assets not found for {name} in {collab_assets_dir}")


def combine_and_execute(
    matching_files: list[str],
    collaborators: dict[str, str],
    cfgCstmPath: CustomPaths,
    buildOpts: BuildOptions,
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
                print(f"Warning: '{file}' not found, will be ignored.")

    # 1.1. Attach the yaml from config files
    copy_config_yaml(unified, cfgCstmPath, buildOpts.title)
    print(f"File combinato creato: {normalize_unc_path(str(unified))}")

    # 2. Resolve base paths
    vault_dir = str(_BANK_DIR) if is_bank() else str(_VAULT_DIR)
    assets_dir = str(safe_path(vault_dir, _ASSETS_DIR))
    build_dir = BUILD_B_PATH if is_bank() else BUILD_V_PATH

    # 3a. Vault: direct conversion
    if not is_bank():
        execute_pandoc(
            str(normalize_unc_path(str(cfgCstmPath.custom_teml_path))),
            str(normalize_unc_path(str(cfgCstmPath.custom_luaf_path))),
            str(normalize_unc_path(str(cfgCstmPath.custom_pandoc_opt_path))),
            safe_path(normalize_unc_path(str(unified))),
            safe_path(normalize_unc_path(str(dst_path))),
            str(normalize_unc_path(vault_dir)),
            str(normalize_unc_path(assets_dir)),
            str(normalize_unc_path(str(build_dir))),
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
        print(f"1 - Moving combined note... to {app_build}")
        local_unified = app_build / unified.name
        shutil.copy2(unified, local_unified)

        # -- Copy assets --
        print(f"2 - Copying assets... to {app_assets}")
        if app_assets.exists():
            shutil.rmtree(app_assets)
        app_assets.mkdir(parents=True, exist_ok=True)
        copy_assets(str(app_assets), collaborators)

        # -- Copy config files (renamed to default names so execute_pandoc
        #    doesn't need to know which custom file is in use) --
        print(f"3 - Copying config files... to {app_config}")
        shutil.copy2(str(cfgCstmPath.custom_teml_path),
                     app_config / TEMPLATE_NAME)
        shutil.copy2(str(cfgCstmPath.custom_luaf_path),
                     app_config / LUA_FILTER_NAME)
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
        print(f"4 - Copying result... to {dst_path}")
        if local_dst.exists():
            shutil.copy2(local_dst, dst_path)
        else:
            print(
                f"Warning: Output '{local_dst}' not found after the conversion.")

        # -- Delete _APPL_DIR entirely --
        remove_dir(app_assets)

    # Remove temp files
    clean_build_dir(build_dir)


def remove_std_header(filePath: Path) -> list[str]:
    """
    Reads a md file, return the content without the specified header.
    Do not modify any other rows.
    """
    if not os.path.exists(filePath):
        print(f"Error: The file: '{filePath}' does not exist.")
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


def inject_title_into_yaml(yaml_block: str, title: str) -> str:
    """
    Insert or override CompanyStudyTitle
    inside a YAML frontmatter block.
    """

    safe_title = title.replace('"', '\\"')

    if re.search(
        r"^CompanyStudyTitle\s*:",
        yaml_block,
        flags=re.MULTILINE,
    ):
        return re.sub(
            r"^CompanyStudyTitle\s*:.*$",
            f'CompanyStudyTitle: "{safe_title}"',
            yaml_block,
            flags=re.MULTILINE,
        )

    # insert before closing marker
    closing_match = re.search(
        r"\n(---|\.\.\.)\s*$",
        yaml_block,
    )

    if closing_match:
        idx = closing_match.start()

        return (
            yaml_block[:idx] +
            f'\nCompanyStudyTitle: "{safe_title}"' + yaml_block[idx:]
        )

    return yaml_block


def copy_config_yaml(
    CombinedPath: Path, cfgCstmPath: CustomPaths, cstmTitle: str | None
) -> None:
    """
    Copy the YAML from the config/.conf file in the specified file
    Paste this YAML to the top of combined_notes_path
    """

    try:
        # Read the contents of the config/my_yaml.yaml file
        with open(str(cfgCstmPath.custom_yaml_path), encoding="utf-8") as f:
            content = f.read()

        yaml_block = None
        # If the file starts with '---' I look for the closing marker ('---' or '...')
        if content.lstrip().startswith("---"):
            # Find the first closing marker that appears on a separate line
            m = re.search(r"\n(---|\.\.\.)(?:\r?\n)", content)
            if m:
                yaml_block = content[: m.end()]

        if yaml_block and cstmTitle:
            yaml_block = inject_title_into_yaml(yaml_block, cstmTitle)

        if yaml_block:
            # Read the current contents of the combined_notes.md file
            with open(CombinedPath, encoding="utf-8") as f:
                combined_content = f.read()

            # If the combined_notes.md file already has a YAML block I remove it
            if combined_content.lstrip().startswith("---"):
                m2 = re.search(r"\n(---|\.\.\.)(?:\r?\n)", combined_content)
                if m2:
                    combined_content = combined_content[m2.end():].lstrip()

            # Add the new YAML block at the beginning
            new_content = f"{yaml_block}\n\n{combined_content}"

            # Write the new content to the combined_notes.md file
            with open(CombinedPath, "w", encoding="utf-8") as f:
                f.write(new_content)

        else:
            print(f"No YAML block found in {cfgCstmPath.custom_yaml_path}")

    except Exception as e:
        print(f"Error during the copy of the YAML block: {str(e)}")


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
                print(f"Revove some artifact: {item.name}")
            except Exception as exc:
                print(f"Warning: Impossible remove '{item.name}': {exc}")


def update_bank_files() -> None:
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
    with open(normalize_unc_path(str(collab_file)), encoding="utf-8") as f:
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
                    f"Collaborator '{collaborator}': "
                    f"main.md not found at '{main_md_path}'"
                )
            else:
                print(
                    f"Collaborator '{collaborator}': "
                    f"main.md found at '{main_md_path}'"
                )
                collab_mainmd.append((collaborator or "", Path(main_md_path)))

    if errors:
        print("The following errors were found in collaborator main.md links:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("All collaborator main.md links are valid.")

    # Read each collaborator's main.md and compose the combined main.md
    with open(normalize_unc_path(str(main_bank_path)), "w", encoding="utf-8") as out:
        out.write("# Combined Index\n\n")
        for collaborator, main_md_path in collab_mainmd:
            out.write(f"## {collaborator}\n\n")
            with open(str(main_md_path), encoding="utf-8") as mf:
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
