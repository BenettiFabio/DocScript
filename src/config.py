import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

###########
# Defines #
###########
_PRJ_CONFIG_FILE = Path(__file__).resolve()  # /config.py
_PRJ_SRC_DIR = _PRJ_CONFIG_FILE.parent  # /src
_PRJ_ROOT_DIR = _PRJ_SRC_DIR.parent  # /DocScript
_HOME_DIR = Path.home()

_VAULT_DIR = Path(os.path.join(_PRJ_ROOT_DIR, "..", "vault")).resolve()
_BANK_DIR = Path(os.path.join(_PRJ_ROOT_DIR, "..", "bank")).resolve()

_CONFIG_DIR = "config"
_DFLT_CONFIG_DIR = Path(os.path.join(_PRJ_ROOT_DIR, _CONFIG_DIR)).resolve()
_APPL_DIR = Path(os.path.join(_HOME_DIR, "Documents", "DocScript")).resolve()

COLLAB_FILE_NAME = "collaborator.md"
COMB_FILE_NAME = "combined_notes.md"
NEW_NOTE_NAME = "default-note.md"  # Nome del nuovo file nota
YAML_NAME = "default-yaml.yaml"  # Nome del file YAML
TEMPLATE_NAME = "default-template.tex"  # Nome del template
LUA_FILTER_NAME = "default-graphic.lua"  # Nome del filtro Lua
PANDOC_OPT_NAME = "default-pandoc-opt.yaml"  # Nome del file per opt personalizzate
CONFIG_FILE_NAME = ".conf"

YAML_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, YAML_NAME)).resolve()
TEMPLATE_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, TEMPLATE_NAME)).resolve()
LUA_FILTER_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, LUA_FILTER_NAME)).resolve()
NEW_NOTE_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, NEW_NOTE_NAME)).resolve()
PANDOC_OPT_PATH = Path(os.path.join(_DFLT_CONFIG_DIR, PANDOC_OPT_NAME)).resolve()
CONFIG_DIR_VAULT_PATH = Path(
    os.path.join(_VAULT_DIR, _CONFIG_DIR, CONFIG_FILE_NAME)
).resolve()
CONFIG_DIR_BANK_PATH = Path(
    os.path.join(_BANK_DIR, _CONFIG_DIR, CONFIG_FILE_NAME)
).resolve()


# contengono i path non di default se specificati
@dataclass
class CustomPaths:
    custom_teml_path: str | None = None
    custom_luaf_path: str | None = None
    custom_yaml_path: str | None = None
    custom_new_note_path: str | None = None
    custom_pandoc_opt_path: str | None = None


def to_unc_slash_path(windows_path: str) -> str:
    """
    Converte un path UNC di Windows con backslash (\\\\server\\share\\path)
    in un path UNC compatibile con strumenti esterni come pandoc (//server/share/path).
    """

    # Se inizia con \\ è un UNC path → rete
    if windows_path.startswith("\\\\"):

        # Rimuove eventuale prefisso \\?\ (che può apparire nei path Windows "lunghi")
        path_str = windows_path.replace("\\\\?\\", "")

        # ottengo tutti i drive di rete inseriti nel sistema
        result = subprocess.run("net use", capture_output=True, text=True, shell=True)
        lines = result.stdout.splitlines()
        mapped_drives = {}

        for line in lines:
            parts = line.strip().split()
            if (
                len(parts) >= 2
                and parts[0].endswith(":")
                and parts[1].startswith("\\\\")
            ):
                drive_letter = parts[0]
                unc_path = parts[1]
                mapped_drives[drive_letter] = unc_path

        # Normalizza il path
        full_path = str(Path(path_str).resolve())
        normalized_path = full_path.replace("\\", "/")

        # Prova a sostituire con lettera di drive, se matcha
        for drive, unc in sorted(
            mapped_drives.items(), key=lambda x: len(x[1]), reverse=True
        ):
            unc_norm = unc.replace("\\", "/")
            unc_parts = unc_norm.strip("/").split("/")
            full_parts = normalized_path.strip("/").split("/")

            try:
                # Trova la prima cartella condivisa
                idx = full_parts.index(unc_parts[-1])

                # Costruisci il path a partire dalla prima cartella trovata
                relative_parts = full_parts[idx + 1 :]
                resolved_drive_path = Path(drive + "/") / Path(*relative_parts)
                return str(resolved_drive_path).replace("\\", "/")

            except ValueError:
                continue  # La cartella finale non è nel path completo

        # Se non trovato, restituisco il path originale
        return windows_path  # bypass
    return windows_path


def safe_path(*args: str | Path) -> Path:
    """
    Converte path a formato UNC/slash.
    - Se 1 parametro: applica conversione semplice su Path/str già costruito
    - Se N parametri: crea path con os.path.join, resolve, e poi converte
    """
    # Versione corta: conversione diretta
    if len(args) == 1:
        return Path(to_unc_slash_path(str(args[0])))

    joined_path = os.path.join(*(str(a) for a in args))
    resolved_path = Path(joined_path).resolve()
    return Path(to_unc_slash_path(str(resolved_path)))


def is_bank() -> bool:
    collab_file = safe_path(_BANK_DIR, COLLAB_FILE_NAME)
    return _BANK_DIR.exists() and collab_file.exists()


def check_config_file(cfgCstmPath: CustomPaths) -> None:
    """
    Legge un file di configurazione e aggiorna i path custom
    userá questi path per convertire le note
    se trova linee nel formato .flag="path/to/file".
    bypassa qualsiasi linea che non inizia con `.`
    """

    print("do something in check_config_file")
    # check per verificare se si é in una banca dati o un vault personale
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
            # mi serve un path assoluto: sfrutto safe_path con due argomenti
            # in questo modo fa il resolve e diventa assoluto per forza
            if is_bank():
                path = safe_path(_BANK_DIR, _CONFIG_DIR, value)
            else:
                path = safe_path(_VAULT_DIR, _CONFIG_DIR, value)

            if key == "template":
                print("template")
                # cfgCstmPath.custom_teml_path = add_new_teml(path)
            elif key == "lua":
                print("lua")
                # cfgCstmPath.custom_luaf_path = add_new_luaf(path)
            elif key == "yaml":
                print("yaml")
                # cfgCstmPath.custom_yaml_path = add_new_yaml(path)
            elif key == "start":
                print("start")
                # cfgCstmPath.custom_new_note_path    = add_new_start(path)
            elif key == "pandoc":
                print("pandoc")
                # cfgCstmPath.custom_pandoc_opt_path  = add_new_yaml(path)


def check_priority_opt(
    cfgCstmPath: CustomPaths,
    yaml: str | None = None,
    template: str | None = None,
    lua: str | None = None,
    pandoc: str | None = None,
    start: str | None = None,
) -> None:
    """_summary_

    Args:
        yaml (Optional[str], optional): _description_. Defaults to None.
        template (Optional[str], optional): _description_. Defaults to None.
        lua (Optional[str], optional): _description_. Defaults to None.
        pandoc (Optional[str], optional): _description_. Defaults to None.

    Verifica opzioni a terminale che possano cambiare i path di configurazione
    Questi hanno prioritá maggiore rispetto al file di configurazione
    """

    print("do something in check_priority_opt")
    if template:
        print("template opt")
        # cfgCstmPath.custom_teml_path = add_new_teml(path)
    elif lua:
        print("lua opt")
        # cfgCstmPath.custom_luaf_path = add_new_luaf(path)
    elif yaml:
        print("yaml opt")
        # cfgCstmPath.custom_yaml_path = add_new_yaml(path)
    elif start:
        print("start opt")
        # cfgCstmPath.custom_new_note_path    = add_new_start(path)
    elif pandoc:
        print("pandoc opt")
        # cfgCstmPath.custom_pandoc_opt_path  = add_new_yaml(path)
