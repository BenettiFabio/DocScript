import argparse
import os
import re
import sys
import shutil
from pathlib import Path
import time
import stat
import pyfiglet
import textwrap
# import win32net # need pywin32
import subprocess

## DEFINES ##

PY_VERSION = "3.3.0"

CONFIG_DIR_NAME     = "config"
CONFFILE_DIR_NAME   = "config-files"
INITIALIZE_DIR_NAME = "initialization"

TEMPORARY_DIR       = "rusco"   # Macro per la cartella temporanea
BUILD_DIR_NAME      = "build"   # Cartella con file prodotti dalla conversione
ASSETS_DIR_NAME     = "assets"  # Cartella con risorse allegate al vault

SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
MAKE_DIR        = Path(os.path.join(SCRIPT_DIR, "..", "vault", BUILD_DIR_NAME)).resolve()
VAULT_DIR       = Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve()
BANK_DIR        = Path(os.path.join(SCRIPT_DIR, "..", "bank")).resolve()
OUTPUT_DIR      = MAKE_DIR
HOME_DIR        = Path.home()
APPLICATION_DIR = Path(os.path.join(HOME_DIR, "Documents", "DocScript")).resolve()
DEFAULT_CONF_DIR= Path(os.path.join(SCRIPT_DIR, CONFIG_DIR_NAME)).resolve()

YAML_NAME       = "default-yaml.yaml"    # Nome del file YAML
TEMPLATE_NAME   = "default-template.tex" # Nome del template
LUA_FILTER_NAME = "default-graphic.lua"  # Nome del filtro Lua
NEW_NOTE_NAME   = "default-note.md"      # Nome del nuovo file nota
PANDOC_OPT_NAME = "default-pandoc-opt.yaml" # Nome del file contenente le opzioni personalizzate da dare a pandoc
COLLAB_FILE     = "collaborator.md"
COMB_FILE_NAME  = "combined_notes.md"
CONFIG_FILE_NAME= ".conf"

NOTE_PATH       = None
OUTPUT_PATH     = None
YAML_PATH       = Path(os.path.join(SCRIPT_DIR, DEFAULT_CONF_DIR, YAML_NAME)).resolve()
TEMPLATE_PATH   = Path(os.path.join(SCRIPT_DIR, DEFAULT_CONF_DIR, TEMPLATE_NAME)).resolve()
LUA_FILTER_PATH = Path(os.path.join(SCRIPT_DIR, DEFAULT_CONF_DIR, LUA_FILTER_NAME)).resolve()
NEW_NOTE_PATH   = Path(os.path.join(SCRIPT_DIR, DEFAULT_CONF_DIR, NEW_NOTE_NAME)).resolve()
PANDOC_OPT_PATH = Path(os.path.join(SCRIPT_DIR, DEFAULT_CONF_DIR, PANDOC_OPT_NAME)).resolve()
CONFIG_DIR_PATH = Path(os.path.join(VAULT_DIR, CONFIG_DIR_NAME, CONFIG_FILE_NAME)).resolve()
CONFIG_DIR_BANK_PATH = Path(os.path.join(BANK_DIR, CONFIG_DIR_NAME, CONFIG_FILE_NAME)).resolve()

EXCLUDED_DIRS       = [
    ASSETS_DIR_NAME,
    BUILD_DIR_NAME,
    CONFIG_DIR_NAME,
    TEMPORARY_DIR
]
EXCLUDED_FILES      = [
    COMB_FILE_NAME,
    NEW_NOTE_NAME,
    "main.md",
    "custom.md"
]

custom  = False # variabile per gestire la conversione di un file custom.md
is_bank = False # variabile per gestire il caso particolare di una banca dati collaborativa

custom_yaml_path = None # contengono i path non di default se specificati
custom_teml_path = None
custom_luaf_path = None
custom_new_note_path    = None
custom_pandoc_opt_path  = None

## FUNCTIONS ##
def normalize_unc_path(windows_path: str) -> str:
    """
    Converte un path UNC di Windows con backslash (\\\\server\\share\\path)
    in un path UNC compatibile con strumenti esterni come pandoc (//server/share/path).
    """
    
    # ottengo tutti i drive di rete inseriti nel sistema
    result = subprocess.run("net use", capture_output=True, text=True, shell=True)
    lines  = result.stdout.splitlines()
    mapped_drives = {}
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].endswith(":") and parts[1].startswith("\\\\"):
            drive_letter = parts[0]
            unc_path = parts[1]
            mapped_drives[drive_letter] = unc_path
    
    # Normalizza il path
    full_path = str(Path(windows_path).resolve())
    normalized_path = full_path.replace("\\", "/")

    # Prova a sostituire con lettera di drive, se matcha
    for drive, unc in sorted(mapped_drives.items(), key=lambda x: len(x[1]), reverse=True):
        unc_norm    = unc.replace("\\", "/")
        unc_parts   = unc_norm.strip("/").split("/")
        full_parts  = normalized_path.strip("/").split("/")
        
        try:
            # Trova la prima cartella condivisa
            idx = full_parts.index(unc_parts[-1])

            # Costruisci il path a partire dalla prima cartella trovata
            relative_parts  = full_parts[idx + 1:]
            final_path      = str(Path(drive + "/") / Path(*relative_parts)).replace("\\", "/")
            return final_path
        except ValueError:
            continue  # La cartella finale non è nel path completo, prova con il prossimo

    # Se non trovato fallirebbe comunque, restituisco il path originale
    return windows_path # bypass

def to_unix_path(raw_path: str) -> str:
    """
    Converte un percorso proveniente da Windows/UNC in un percorso POSIX
    valido. Se il percorso è già POSIX (inizia con '/' o è relativo),
    lo restituisce invariato.

    • Back‑slash → slash
    • Rimuove eventuali prefissi '\\\\?\\' o '\\\\' (UNC)
    • Se il percorso contiene una lettera di unità (es. 'C:\\folder')
      la trasforma in '/c/folder' (con la lettera minuscola) – solo
      quando il codice è in esecuzione su Linux.
    """
    is_windows = os.name == "nt"
    
    # Rimuove prefissi Windows speciali
    if raw_path.startswith("\\\\?\\"):
        raw_path = raw_path[4:]     # elimina '\\?\'
    
    # ====== WIN ======
    if is_windows:
        # Se inizia con \\ è un UNC path → rete
        if raw_path.startswith('\\\\'):
            return normalize_unc_path(raw_path)
        else:
            return raw_path
    
    # ====== UNIX ======
    # backslash → slash
    raw_path = raw_path.replace("\\", "/")

    # UNC → /server/share/...
    if raw_path.startswith("//"):
        return "/" + raw_path.lstrip("/")
    
    # Drive letter → /c/...
    if re.match(r"^[a-zA-Z]:/", raw_path):
        drive = raw_path[0].lower()
        return f"/{drive}{raw_path[2:]}"

    return raw_path

def safe_path(*parts):
    """
    Normalizza il Path gestendo varianti di OS e dischi di rete

    • Se viene passato un solo argomento:
        – se è già un `Path` o una stringa, lo normalizza con `to_unix_path`.
    • Se vengono passati più argomenti:
        – li concatena con `os.path.join`, poi normalizza.
    • Sempre restituisce un oggetto `Path` risolto (senza risolvere
      eventuali symlink di rete, ma con `strict=False` per evitare
      eccezioni se il percorso non esiste ancora).
    """
    
    if len(parts) == 1:
        p = parts[0]
        # stringa o altro: normalizza
        return Path(to_unix_path(str(p)))

    # più componenti → join, poi normalizza
    joined = os.path.join(*parts)
    return Path(to_unix_path(joined))

def should_skip_dir(dir_path):
    """Verifica se una directory deve essere saltata nella scansione"""
    return dir_path in EXCLUDED_DIRS

def should_skip_file(file_path: str):
    """Verifica se un file deve essere escluso da una scansione"""
    file_name = os.path.basename(file_path)
    return file_name in EXCLUDED_FILES

def copy_dir_recursive(src: str, dst: str) -> None:
    """
    Copia ricorsivamente il contenuto di una directory `src` in `dst`,
    preservando la struttura e copiando solo i file che differiscono
    per dimensione o timestamp.

    Args:
        src (str): percorso della directory sorgente
        dst (str): percorso della directory di destinazione se non esiste la crea
    """
    if not os.path.exists(src):
        raise FileNotFoundError(f"La directory sorgente non esiste: {src}")

    for root, _, files in os.walk(src):
        relative_path   = os.path.relpath(root, src)
        target_dir      = os.path.join(dst, relative_path)
        os.makedirs(target_dir, exist_ok=True)

        for file in files:
            src_file    = os.path.join(root, file)
            dest_file   = os.path.join(target_dir, file)

            # Se il file di destinazione esiste, controlla dimensione e timestamp
            if os.path.exists(dest_file):
                src_stat = os.stat(src_file)
                dst_stat = os.stat(dest_file)

                same_size   = src_stat.st_size == dst_stat.st_size
                same_mtime  = int(src_stat.st_mtime) == int(dst_stat.st_mtime)

                if same_size and same_mtime:
                    # File identico -> salta copia
                    continue

            # Copia file e metadata
            shutil.copy2(src_file, dest_file)

def create_config_dirs(base_dir: str, config_dir_name: str, subdirs: list[str]):
    """
    Crea una struttura di cartelle di configurazione sotto `base_dir/config_dir_name`,
    usando la lista di sottodirectory specificata in `subdirs`.

    Args:
        base_dir (str): directory radice (es. vault_dir)
        config_dir_name (str): nome della cartella di configurazione
        subdirs (list[str]): lista delle sottocartelle da creare
    """
    
    config_root = os.path.join(base_dir, config_dir_name)
    if not os.path.exists(config_root):
        os.makedirs(config_root)

    for subdir in subdirs:
        target_dir = os.path.join(config_root, subdir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

def convert_link_to_absolute(markdown_text, base_path):
    """
    Converte i link relativi Markdown in link assoluti mantenendo la sintassi Markdown.
    """
    base_path = Path(base_path).parent.resolve()

    def replacer(match):
        label       = match.group(1)
        rel_path    = match.group(2)
        abs_path    = (base_path / rel_path).resolve()
        return f"[{label}]({abs_path})"

    # Match Markdown links come [text](relative/path.md)
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    return pattern.sub(replacer, markdown_text).replace("\\", "/")

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def CopyAssets(output_dir, collaborators):    
    """
    Copia il contenuto delle cartelle assets di tutti i collaboratori dentro output_dir.
    Se due collaboratori hanno cartelle di argomento con lo stesso nome, unisce i contenuti.
    Le sottocartelle (es: imgs, pdfs) vengono unite, non sovrascritte.
    """
    for name, main_md_path in collaborators.items():
        collab_assets_dir = os.path.join(os.path.dirname(main_md_path), "assets")
        if os.path.exists(collab_assets_dir):
            for root, dirs, files in os.walk(collab_assets_dir):
                # Calcola il path relativo rispetto alla cartella assets del collaboratore
                rel_path = os.path.relpath(root, collab_assets_dir)
                dest_dir = os.path.join(output_dir, rel_path) if rel_path != "." else output_dir
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                for file in files:
                    src_file  = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
            print(f"Assets copiati per {name} in {output_dir}")
        else:
            print(f"Attenzione: assets non trovati per {name} in {collab_assets_dir}")

def isNetworkPath():
    here = os.getcwd()
    return (here.startswith('\\\\') or not here.startswith('C:')) 

def CopyYAMLInformation(combined_notes_path):
    """
    Cerca il blocco YAML all'inizio del file main.md e lo copia in cima al file combined_notes_path.
    Se non trova il blocco YAML nel file main_path, non fa nulla.
    
    Args:
        combined_notes_path (str): Percorso del file combined_notes.md
    """
    yaml_path = YAML_PATH # default
    
    if custom_yaml_path: # se inserito nel file di config
        yaml_path = safe_path(custom_yaml_path)
    
    try:
        # Legge il contenuto del file main.md
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        yaml_block = None
        # Se il file inizia con '---' cerco il marcatore di chiusura ('---' o '...')
        if content.lstrip().startswith('---'):
            # Trova il primo marcatore di chiusura che compare su una linea a parte
            m = re.search(r"\n(---|\.\.\.)(?:\r?\n)", content)
            if m:
                yaml_block = content[:m.end()]

        if yaml_block:
            # Legge il contenuto attuale del file combined_notes.md
            with open(combined_notes_path, 'r', encoding='utf-8') as f:
                combined_content = f.read()

            # Se il file combined_notes.md ha già un blocco YAML lo rimuovo (se presente all'inizio)
            if combined_content.lstrip().startswith('---'):
                m2 = re.search(r"\n(---|\.\.\.)(?:\r?\n)", combined_content)
                if m2:
                    combined_content = combined_content[m2.end():].lstrip()

            # Aggiunge il nuovo blocco YAML all'inizio
            new_content = f"{yaml_block}\n\n{combined_content}"

            # Scrive il nuovo contenuto nel file combined_notes.md
            with open(combined_notes_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        else:
            print(f"Nessun blocco YAML trovato in {yaml_path}")

    except Exception as e:
        print(f"Errore durante la copia del blocco YAML: {str(e)}")

def check_config_conversion_file():
    """
    Legge un file di configurazione e aggiorna le variabili globali
    se trova linee nel formato .flag="path/to/file".
    bypassa qualsiasi linea che non inizia con `.`
    """

    global custom_teml_path, custom_luaf_path, custom_yaml_path, custom_new_note_path, custom_pandoc_opt_path

    # check per verificare se si é in una banca dati o un vault personale
    bank_dir = safe_path(SCRIPT_DIR, "..", "bank")
    collab_file = safe_path(bank_dir, COLLAB_FILE)
    global is_bank
    
    if os.path.exists(collab_file):
        is_bank = True
    
    config_path_to_use = None
    if is_bank:
        config_path_to_use = CONFIG_DIR_BANK_PATH
    else:
        config_path_to_use = CONFIG_DIR_PATH
        
    if not os.path.exists(config_path_to_use):
        return

    pattern = re.compile(r'^\.(\w+)\s*=\s*"([^"]+)"$')

    with open(config_path_to_use, 'r', encoding='utf-8') as conf_file:
        for line in conf_file:
            line = line.strip()

            if not line.startswith('.'):
                continue

            match = pattern.match(line)
            if not match:
                continue

            key, value = match.groups()
            if is_bank:
                path = safe_path(BANK_DIR, CONFIG_DIR_NAME, value) # avendo due argomenti fa necessariamente il resolve, facendo diventare il path assoluto
            else:
                path = safe_path(VAULT_DIR, CONFIG_DIR_NAME, value)
            
            key, value = match.groups()            
            if key == "template":
                custom_teml_path = add_new_teml(path)
            elif key == "lua":
                custom_luaf_path = add_new_luaf(path)
            elif key == "yaml":
                custom_yaml_path = add_new_yaml(path)
            elif key == "start":
                custom_new_note_path    = add_new_start(path)
            elif key == "pandoc":
                custom_pandoc_opt_path  = add_new_yaml(path)

def validate_output(output):
    """
    Verifica che il file di output abbia un'estensione valida (.pdf o .tex).
    Se non è valido, termina il programma.
    """
    global OUTPUT_PATH
    ext = os.path.splitext(output)[1].lower()
    if ext not in [".pdf", ".tex"]:
        print(f"Errore: il file di output '{output}' deve avere estensione .pdf o .tex.")
        sys.exit(1)
    else:
        OUTPUT_PATH = Path(os.path.join(OUTPUT_DIR, output)).resolve()

def add_new_yaml(yaml_file):
    ext = os.path.splitext(yaml_file)[1].lower()
    if ext not in [".yaml"]:
        print(f"Errore: il file di input '{yaml_file}' deve avere estensione .yaml.")
        sys.exit(1)
    
    if not os.path.exists(yaml_file):
        print(f"Errore: il file di input '{yaml_file}' non trovato.")
        sys.exit(1)
    
    return yaml_file

def add_new_teml(template_file):
    ext = os.path.splitext(template_file)[1].lower()
    if ext not in [".tex"]:
        print(f"Errore: il file di input '{template_file}' deve avere estensione .tex.")
        sys.exit(1)
    
    if not os.path.exists(template_file):
        print(f"Errore: il file di input '{template_file}' non trovato.")
        sys.exit(1)
    
    return template_file

def add_new_luaf(lua_file):
    ext = os.path.splitext(lua_file)[1].lower()
    if ext not in [".lua"]:
        print(f"Errore: il file di input '{lua_file}' deve avere estensione .lua.")
        sys.exit(1)
    
    if not os.path.exists(lua_file):
        print(f"Errore: il file di input '{lua_file}' non trovato.")
        sys.exit(1)
    
    return lua_file

def add_new_start(start_file):
    ext = os.path.splitext(start_file)[1].lower()
    if ext not in [".md"]:
        print(f"Errore: il file di input '{start_file}' deve avere estensione .md.")
        sys.exit(1)
    
    if not os.path.exists(start_file):
        print(f"Errore: il file di input '{start_file}' non trovato.")
        sys.exit(1)
    
    return start_file

def CheckPreconditions():
    """
    Verifica che il sistema abbia i prerequisiti necessari per la conversione.
    Controlla se xelatex e pandoc sono installati e disponibili nel PATH.
    """
    
    # Controlla se xelatex è nel PATH
    if (sys.platform.startswith("win")):
        if os.system("where xelatex >nul 2>nul") != 0:
            print("Errore: xelatex non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("xelatex installato.")

    if (sys.platform.startswith("linux")):
        if os.system("which xelatex > /dev/null") != 0:
            print("Errore: xelatex non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("xelatex installato.")

    # Controlla se pandoc è nel PATH
    if (sys.platform.startswith("win")):
        if os.system("where pandoc >nul 2>nul") != 0:
            print("Errore: pandoc non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("pandoc installato.")

    if (sys.platform.startswith("linux")):
        if os.system("which pandoc > /dev/null") != 0:
            print("Errore: pandoc non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("pandoc installato.")

    # Controlla se i font GNU FreeFonts sono installati
    if (sys.platform.startswith("win")):
        if os.system('fc-list | findstr /i "FreeSerif FreeSans FreeMono" >nul 2>nul') != 0:
            print("Errore: i font GNU FreeFonts non sono installati.")
            sys.exit(1)
        else:
            print("Font GNU FreeFonts installati.")

    if (sys.platform.startswith("linux")):
        if os.system('locate Free .ttf | grep /usr/share/fonts/TTF/ > /dev/null') != 0:
            print("Errore: i font GNU FreeFonts non sono installati in /usr/share/fonts/TTF .")
            sys.exit(1)
        else:
            print("Font GNU FreeFonts installati.")        


def get_all_files_from_main(custom):
    """
    Legge il file main.md (o custom.md) e restituisce una lista di tutti i file .md referenziati.
    """
    # Percorso del file main.md o custom.md
    vault_dir = safe_path(SCRIPT_DIR, "..", "vault")
    if custom:
        main_md_path = vault_dir / "custom.md"
    else:
        main_md_path = vault_dir / "main.md"

    # Controlla se il file main.md esiste
    if not os.path.exists(main_md_path):
        if custom:
            print(f"Errore: il file custom.md non è stato trovato in {os.path.dirname(main_md_path)} .")
        else:
            print(f"Errore: il file main.md non è stato trovato in {os.path.dirname(main_md_path)} .")
        sys.exit(1)

    # Leggi il contenuto di main.md
    with open(main_md_path, "r", encoding="utf-8") as main_md_file:
        main_md_content = main_md_file.readlines()

    # Lista per raccogliere i file referenziati
    matching_files = []
    # Cerca i link che corrispondono all'argomento
    for line in main_md_content:
        if "(" in line and ")" in line:  # Cerca i link che iniziano con l'argomento "(argomento/nome-nota.md)"
            start_idx = line.find("(") + 1
            end_idx = line.find(")")
            if start_idx != -1 and end_idx != -1:
                file_path = line[start_idx:end_idx]
                if file_path.endswith(".md"):
                    matching_files.append(file_path)

    # Se non ci sono file corrispondenti, mostra un errore
    if not matching_files:
        print(f"Errore: nessun file trovato in {'custom.md' if custom else 'main.md'}.")
        sys.exit(1)
        
    return matching_files

def get_all_files_from_collab_main(custom):
    """
    Legge il file main.md (o custom.md) della banca dati e il file collaborator.md.
    Per ogni sezione ## NOME COLLABORATORE prende solo le note elencate sotto quella sezione,
    cerca il path relativo nel main.md del collaboratore e restituisce il path assoluto.
    """
    bank_dir = safe_path(SCRIPT_DIR, "..", "bank")
    if custom:
        main_md_path = safe_path(bank_dir, "custom.md")
    else:
        main_md_path = safe_path(bank_dir, "main.md")
    collab_file = safe_path(bank_dir, COLLAB_FILE)

    if not os.path.exists(collab_file):
        print(f"Errore: il file '{collab_file}' non esiste.")
        sys.exit(1)
    if not os.path.exists(main_md_path):
        print(f"Errore: il file main.md non è stato trovato in {os.path.dirname(main_md_path)} .")
        sys.exit(1)

    # Mappa nome collaboratore -> path main.md collaboratore
    collaborators = {}
    with open(collab_file, "r", encoding="utf-8") as cf:
        current_name = None
        for line in cf:
            line = line.strip()
            if line.startswith("##"):
                current_name = line[2:].strip()
            match = re.search(r'\[.*\]\((.*\.md)\)', line)
            if match and current_name:
                main_md_path_collab = os.path.join(os.path.dirname(cf.name), match.group(1))
                collaborators[current_name] = main_md_path_collab

    EffectiveCollaborators = []
    with open(main_md_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("##"):
                    name = line[2:].strip()
                    EffectiveCollaborators.append(name)

    # Cerca dentro il main_md_path solo i collaboratori presenti tra tutti quelli di collaborator.md
    FinalCollab = {name: collaborators[name] for name in EffectiveCollaborators if name in collaborators}

    # Leggi il custom.ms o main.md e raccogli le note per collaboratore
    with open(main_md_path, "r", encoding="utf-8") as mf:
        lines = mf.readlines()

    matching_files = []
    current_collab = None
    for line in lines:
        line = line.strip()
        if line.startswith("##") or line.startswith("#"):
            current_collab = line[2:].strip()
        elif re.search(r'\[.*?\]\([^)]+\.md\)', line) and current_collab:
            # Estrai il path relativo della nota
            note_match = re.search(r'\[.*?\]\(([^)]+\.md)\)', line)
            if note_match:
                note_rel_path = note_match.group(1)
                # Cerca il main.md del collaboratore
                main_md_path_collab = collaborators.get(current_collab)
                if not main_md_path_collab or not os.path.exists(main_md_path_collab):
                    print(f"main.md non trovato per {current_collab} in {main_md_path_collab}")
                    continue
                # Risolvi il path assoluto rispetto al vault del collaboratore
                note_abs_path = os.path.abspath(os.path.join(os.path.dirname(main_md_path_collab), note_rel_path))
                if os.path.exists(note_abs_path):
                    matching_files.append(note_abs_path)
                else:
                    print(f"Nota '{note_rel_path}' non trovata per {current_collab} in {note_abs_path}")

    if not matching_files:
        print(f"Errore: nessun file trovato in {'custom.md' if custom else 'main.md'}.")
        sys.exit(1)

    return matching_files, FinalCollab
    
def get_files_for_argument_from_main(argomento):
    """
    Legge il file main.md e restituisce una lista di file che corrispondono all'argomento specificato.
    """
    # Percorso del file main.md
    main_md_path = safe_path(VAULT_DIR, "main.md")

    # Controlla se il file main.md esiste
    if not os.path.exists(main_md_path):
        print(f"Errore: il file main.md non è stato trovato in {os.path.dirname(main_md_path)}.")
        sys.exit(1)

    # Leggi il contenuto di main.md
    with open(main_md_path, "r", encoding="utf-8") as main_md_file:
        main_md_content = main_md_file.readlines()

    # Lista per raccogliere i file che corrispondono all'argomento
    matching_files = []

    # Cerca i link che corrispondono all'argomento
    for line in main_md_content:
        if f"({argomento}/" in line:  # Cerca i link che iniziano con l'argomento "(argomento/nome-nota.md)"
            start_idx   = line.find("(") + 1
            end_idx     = line.find(")")
            if start_idx != -1 and end_idx != -1:
                file_path = line[start_idx:end_idx]
                if file_path.startswith(f"{argomento}/"):
                    matching_files.append(file_path)

    # Se non ci sono file corrispondenti, mostra un errore
    if not matching_files:
        print(f"Errore: nessun file trovato per l'argomento '{argomento}' in main.md.")
        sys.exit(1)

    return matching_files

def get_all_files_from_root():
    """
    Legge tutti i file nel vault e restituisce una lista di tutti i file .md.
    """
    # Percorso del file main.md
    root_vault_path = safe_path(VAULT_DIR)
    matched_files   = []

    for root, dirs, files in os.walk(root_vault_path):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        for file in files:
            if not file.endswith(".md"):
                continue
            if should_skip_file(file):
                continue

            full_path = os.path.join(root, file)
            matched_files.append(full_path)

    return matched_files

def get_files_for_argument_from_root(argomento):
    """
    Legge tutti i file nel vault e restituisce una lista di file che corrispondono all'argomento specificato.
    """
    # Percorso del file main.md
    # root_vault_path = safe_path("..", "vault")
    root_vault_path = safe_path(VAULT_DIR)
    matched_files   = []

    # Pattern da cercare nel nome del file
    pattern = re.compile(rf'^main\.{re.escape(argomento)}\..*\.md$')

    for root, dirs, files in os.walk(root_vault_path):
        # Escludi le directory non volute
        if should_skip_dir(root):
            continue

        for file in files:
            if should_skip_file(file):
                continue
            if file.endswith(".md") and pattern.match(file):
                full_path = os.path.join(root, file)
                matched_files.append(full_path)
    
    return matched_files

def SearchAndCombineNotes(matching_files):
    """
    Combina le note corrispondenti in un unico file .md, rimuovendo l'header specificato.
    """
    combined_file_path = safe_path(MAKE_DIR, COMB_FILE_NAME)
    
    # Crea la directory di output se non esiste
    if not os.path.exists(MAKE_DIR):
        os.makedirs(MAKE_DIR)

    vault_dir = safe_path(SCRIPT_DIR, "..", "vault")
    with open(combined_file_path, "w", encoding="utf-8") as combined_md_file:
        for file in matching_files:
            file_path = str(vault_dir / file)
            if os.path.exists(file_path):
                # Ottieni il contenuto senza header
                filtered_lines = RemoveHeaderFromFile(file_path)

                # Scrivi il contenuto filtrato nel file combinato
                combined_md_file.writelines(filtered_lines)
                combined_md_file.write("\n")
            else:
                print(f"Avviso: il file '{file}' non è stato trovato e sarà ignorato.")

    print(f"File combinato creato: {combined_file_path}")
    # Aggiunge il blocco YAML da main.md se presente
    try:
        CopyYAMLInformation(combined_file_path)
    except Exception:
        pass
    return combined_file_path

def CombineNotes(matching_files):
    """
    Combina le note corrispondenti in un unico file .md, rimuovendo l'header specificato.
    """
    combined_file_path = safe_path(MAKE_DIR, COMB_FILE_NAME)

    # Crea la directory di output se non esiste
    if not os.path.exists(MAKE_DIR):
        os.makedirs(MAKE_DIR)

    vault_dir = safe_path(SCRIPT_DIR, "..", "vault")
    
    with open(combined_file_path, "w", encoding="utf-8") as combined_md_file:
        for file in matching_files:
            file_path = str(vault_dir / file)
            if os.path.exists(file_path):
                # Ottieni il contenuto senza header
                filtered_lines = RemoveHeaderFromFile(file_path)

                # Scrivi il contenuto filtrato nel file combinato
                combined_md_file.writelines(filtered_lines)
                combined_md_file.write("\n")
            else:
                print(f"Avviso: il file '{file}' non è stato trovato e sarà ignorato.")

    print(f"File combinato creato: {combined_file_path}")
    # Aggiunge il blocco YAML da main.md se presente
    try:
        CopyYAMLInformation(combined_file_path)
    except Exception:
        pass
    return combined_file_path

def checkInconsistency(matching_files_main, matching_files_root):
    """
    Controlla che tutti i file effettivi siano referenziati nel main.
    Se mancano delle note nel main, stampa un errore con i file mancanti.
    I percorsi vengono normalizzati per il confronto.
    """

    # -----------------------------------------------------------------
    # Filtra i file “root” (tutti i .md presenti nel vault)
    # -----------------------------------------------------------------
    filtered_matching_files_root = [
        Path(path).name
        for path in matching_files_root
        if not path.startswith(f"{TEMPORARY_DIR}/")
        and not Path(path).name.startswith(f"main.{TEMPORARY_DIR}.")
    ]

    # -----------------------------------------------------------------
    # Normalizza le liste (solo i nomi dei file)
    # -----------------------------------------------------------------
    normalized_actual_list = [
        Path(path).name for path in filtered_matching_files_root
    ]

    normalized_main_list = [
        Path(path).name for path in matching_files_main
    ]

    main_set   = set(normalized_main_list)
    actual_set = set(normalized_actual_list)

    missing_in_main = actual_set - main_set

    if missing_in_main:
        print("Errore: i seguenti file .md NON sono inclusi nel main:")
        for f in sorted(missing_in_main):
            print(f"- {f}")
        sys.exit(1)

def RemoveHeaderFromFile(file_path):
    """
    Legge un file Markdown e restituisce il contenuto senza l'header specificato.
    Non modifica il file sorgente.
    """
    if not os.path.exists(file_path):
        print(f"Errore: il file '{file_path}' non esiste.")
        sys.exit(1)

    # Leggi il contenuto del file
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Rimuovi l'header
    content_started = False
    filtered_lines  = []
    for line in lines:
        if "<!-- /code_chunk_output -->" in line:
            content_started = True
            continue
        if content_started:
            filtered_lines.append(line)

    # Se l'header non è stato trovato, restituisci l'intero contenuto
    if not content_started:
        # hinibition of warning print
        # print(f"Avviso: header non trovato nel file '{file_path}'. Restituisco il contenuto completo.")
        return lines

    return filtered_lines

##############################
## FUNCTIONS FOR CONVERSION ##
##############################
def InitBank():
    print("Inizializzazione della banca dati collaborativa...")
    parent_dir      = safe_path(SCRIPT_DIR, "..")
    template_dir    = safe_path(SCRIPT_DIR, INITIALIZE_DIR_NAME, "init-bank")
    collab_file     = safe_path(parent_dir, COLLAB_FILE)
    bank_dir        = safe_path(parent_dir, "bank")
    vault_dir       = safe_path(parent_dir, "vault")
    
    if os.path.exists(collab_file):
        print("Errore: il file dei collaboratori esiste già, se giá compilato puoi lanciare un -u per aggiornarlo.")
        sys.exit(1)
        
    if os.path.exists(vault_dir):
        print("Errore: la cartella corrente é giá un vault, non puoi inizializzare una banca dati collaborativa.")
        sys.exit(1)
    
    if os.path.exists(bank_dir):
        print("Errore: la cartella corrente é giá inizializzata come banca dati, puoi giá usarla modificando il file collaborator.md.")
        sys.exit(1)

    try:
        if not os.path.exists(template_dir):
            print(f"Errore: la cartella template '{template_dir}' non esiste.")
            sys.exit(1)
        
        copy_dir_recursive(template_dir, bank_dir)
        print(f"- Struttura banca dati : ok")
        
        # Creazione delle cartelle per l'utente per i file di configurazione
        # create_config_dirs(bank_dir, CONFIG_DIR_NAME, CONFIG_DIRS)
        
        # Scrive il config file con i riferimenti di default
        config_file = os.path.join(vault_dir, CONFIG_DIR_NAME, CONFIG_FILE_NAME)
        
        # Scrivo i riferimenti relativi alla cartella config-files dentro il vault
        rel_yaml_path       = Path(os.path.join("./", CONFFILE_DIR_NAME, YAML_NAME))
        rel_template_path   = Path(os.path.join("./", CONFFILE_DIR_NAME, TEMPLATE_NAME))
        rel_lua_path        = Path(os.path.join("./", CONFFILE_DIR_NAME, LUA_FILTER_NAME))
        rel_pandoc_path     = Path(os.path.join("./", CONFFILE_DIR_NAME, PANDOC_OPT_NAME))
        # contenuto = f'# default configuration - start from build/\n.yaml="{rel_yaml_path}"\n.template="{rel_template_path}"\n.lua="{rel_lua_path}"\n'
        contenuto = f"""\
            # default configuration - start path from build/
            .pandoc="{rel_pandoc_path}"
            .yaml="{rel_yaml_path}"
            .template="{rel_template_path}"
            .lua="{rel_lua_path}"
        """
        contenuto = textwrap.dedent(contenuto)
        
        with open(config_file, "w") as f:
            f.write(contenuto)
        print(f"- Cartella .config : ok\n")
        
        print(f"Tips : Per iniziare compila il file {COLLAB_FILE} con i tuoi collaboratori.")
        print(f"Tips : Successivamente lancia un -u (--update) per aggiornare il file main.md")
        
        print(f"Enjoy working with you team mates! <3")
        
    except Exception as e:
        print(f"Errore durante l'inizializzazione: {e}")
        sys.exit(1)

def InitVault():
    """
    Inizializza la struttura del vault copiando i file e le cartelle necessarie.
    """
    parent_dir  = safe_path(SCRIPT_DIR, "..")
    template_dir= safe_path(SCRIPT_DIR, INITIALIZE_DIR_NAME, "init-vault")
    setup_dir   = safe_path(SCRIPT_DIR, INITIALIZE_DIR_NAME, "setup-vault")
    config_dir  = safe_path(SCRIPT_DIR, CONFIG_DIR_NAME)
    bank_dir    = safe_path(parent_dir, "bank")
    vault_dir   = safe_path(parent_dir, "vault")
    usr_config_dir= safe_path(vault_dir, CONFIG_DIR_NAME, CONFFILE_DIR_NAME)

    if os.path.exists(bank_dir):
        print("Errore: la cartella corrente é giá inizializzata come banca dati, non puoi inizializzare un vault.")
        sys.exit(1)
    
    # Controlla se esiste già una cartella chiamata 'vault'
    if os.path.exists(vault_dir):
        # Ottieni il contenuto della cartella 'vault'
        vault_contents = os.listdir(vault_dir)
        
        # Check di un repo già inizializzato, non si vuole cancellare ciò che già esiste
        vault_contents = [item for item in vault_contents if item != "build"]
        if vault_contents:
            print("Errore: Il Vault contiene già file, non è necessario inizializzare.")
            sys.exit(1)

    try:
        if not os.path.exists(template_dir):
            print(f"Errore: la cartella template '{template_dir}' non esiste.")
            sys.exit(1)
        
        if not os.path.exists(config_dir):
            print(f"Errore: la cartella dei file di config '{config_dir}' non esiste.")
            sys.exit(1)

        print(f"Inizio creazione del vault...")
        copy_dir_recursive(template_dir, vault_dir)
        
        # Scrive il main file iniziale con i primi riferimenti di default
        main_file = os.path.join(vault_dir, "main.md")
        contenuto = f"""\
            # Argomento 1
            
            - [NomeArgomento1](main-arg1/main.main-arg1.first-note.md)
        """
        contenuto = textwrap.dedent(contenuto)
        
        with open(main_file, "w") as f:
            f.write(contenuto)
        
        
        print(f"- Cartella vault : ok\n")
        
        # Creazione delle cartelle per l'utente per i file di configurazione
        print(f"Copia dei file di configurazione per pandoc...")
        copy_dir_recursive(config_dir, usr_config_dir)
        # create_config_dirs(vault_dir, CONFIG_DIR_NAME, CONFIG_DIRS)
        
        # Scrive il config file con i riferimenti di default
        config_file = os.path.join(vault_dir, CONFIG_DIR_NAME, CONFIG_FILE_NAME)
        
        # Usa percorsi relativi verso ./config-files nella cartella vault/config
        rel_yaml_path       = Path(os.path.join("./", CONFFILE_DIR_NAME, YAML_NAME))
        rel_template_path   = Path(os.path.join("./", CONFFILE_DIR_NAME, TEMPLATE_NAME))
        rel_lua_path        = Path(os.path.join("./", CONFFILE_DIR_NAME, LUA_FILTER_NAME))
        rel_start_path      = Path(os.path.join("./", CONFFILE_DIR_NAME, NEW_NOTE_NAME))
        rel_pandoc_path     = Path(os.path.join("./", CONFFILE_DIR_NAME, PANDOC_OPT_NAME))
        # contenuto = f'# default configuration - start path from build/\n.yaml="{rel_yaml_path}"\n.template="{rel_template_path}"\n.lua="{rel_lua_path}"\n.start="{rel_start_path}"\n'
        contenuto = f"""\
            # default configuration - start path from config/
            .pandoc="{rel_pandoc_path}"
            .yaml="{rel_yaml_path}"
            .template="{rel_template_path}"
            .lua="{rel_lua_path}"
            .start="{rel_start_path}"
        """
        contenuto = textwrap.dedent(contenuto)
        
        with open(config_file, "w") as f:
            f.write(contenuto)
        
        print(f"- Cartella .config : ok")
        
        # Copia tutto il contenuto della cartella setup-vault fuori dalla cartella 'vault'
        copy_dir_recursive(setup_dir, parent_dir)
        print(f"- File di configurazione per VSCode : ok\n")
        
        print(f"Struttura del Vault costruita con successo!")
        print(f"Enjoy your new vault! <3")
    
    except Exception as e:
        print(f"Errore durante la costruzione del Vault: {e}")
        sys.exit(1)

def UpdateBank():
    print("Aggiornamento della banca dati collaborativa...")
    bank_dir    = safe_path(SCRIPT_DIR, "..", "bank")
    collab_file = safe_path(bank_dir, COLLAB_FILE)
    main_bank_path = safe_path(bank_dir, "main.md")
    if not os.path.exists(collab_file):
        print(f"Errore: il file '{collab_file}' non esiste.")
        sys.exit(1)

    # Check del file collaborator.md
    with open(collab_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    collaborator = None
    errors       = []
    collab_mainmd= []  # Lista di tuple (nome, path_mainmd)
    for line in lines:
        line = line.strip()
        if line.startswith("##"):
            collaborator = line[2:].strip()
        # Cerca link markdown a main.md
        match = re.search(r'\[.*?\]\((.*?main\.md)\)', line)
        if match:
            main_md_path = safe_path("..", match.group(1))  # Definisci qui la variabile
            if not os.path.exists(main_md_path):
                errors.append(f"Collaboratore '{collaborator}': main.md non trovato in '{main_md_path}'")
            else:
                print(f"Collaboratore '{collaborator}': main.md trovato in '{main_md_path}'")
                collab_mainmd.append((collaborator, main_md_path))

    if errors:
        print("Sono stati trovati i seguenti errori nei link ai main.md:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
        
    else:
        print("Tutti i link ai main.md dei collaboratori sono validi.")
        
    # Proseguo alla lettura dei singoli main.md
    with open(main_bank_path, "w", encoding="utf-8") as out:
        out.write("# Indice complessivo\n\n")
        for collaborator, main_md_path in collab_mainmd:
            out.write(f"## {collaborator}\n\n")
            with open(main_md_path, "r", encoding="utf-8") as mf:
                for line in mf:
                    # Salta titoli con un solo #
                    if re.match(r"^#(?!#)", line):
                        continue
                    # Trasforma i sottotitoli ## in ###
                    if line.startswith("##"):
                        line = "#" + line
                    # Altrimenti copia semplcicemente il contenuto aggiungendo il path del collaboratore
                    newline = convert_link_to_absolute(line, main_md_path)
                    out.write(newline)
                out.write("\n")
    print(f"main.md complessivo aggiornato in {main_bank_path}")

def ConversionSingleNote(nota):
    global NOTE_PATH
    NOTE_PATH = None  # Inizializza come None per indicare che non è stato trovato

    # Directory di partenza
    vault_path = os.path.join("..")

    # Cerca il file nelle sottocartelle di vault, escludendo assets/ e build/
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in [ASSETS_DIR_NAME, BUILD_DIR_NAME]]

        # Cerca il file .md corrispondente
        for file in files:
            if file == nota and file.endswith(".md"):
                NOTE_PATH = os.path.join(root, file)
                break
        if NOTE_PATH:
            break

    # Se non trovato
    if not NOTE_PATH:
        print(f"Errore: il file '{nota}' non è stato trovato nel vault.")
        sys.exit(1)

    # Crea la directory di output se non esiste
    if not os.path.exists(safe_path(OUTPUT_DIR)):
        os.makedirs(safe_path(OUTPUT_DIR))
    
    # Verifica che il sistema abbia i requisiti necessari alla conversione    

    CheckPreconditions()
    # Ottieni il contenuto senza header
    filtered_lines = RemoveHeaderFromFile(NOTE_PATH)

    # Scrivi il contenuto filtrato in un file temporaneo
    temp_file_path = safe_path(MAKE_DIR, COMB_FILE_NAME)
    with open(temp_file_path, "w", encoding="utf-8") as temp_file:
        temp_file.writelines(filtered_lines)

    # Esegui la conversione sul file temporaneo
    # Assicura che il blocco YAML di main.md sia presente in cima al file combinato
    try:
        CopyYAMLInformation(temp_file_path)
    except Exception:
        pass
    NoteConversion(temp_file_path)
        
    # Elimina il file temporaneo
    try:
        os.remove(temp_file_path)
    except Exception as e:
        print(f"Errore durante l'eliminazione del file temporaneo: {e}")

def ConversionGroupNote(argomento):
    # Ottieni i file corrispondenti all'argomento
    print("Consistency check started...")
    matching_files_main = get_files_for_argument_from_main(argomento)
    matching_files_root = get_files_for_argument_from_root(argomento)
    
    checkInconsistency(matching_files_main, matching_files_root)
    print("Consistency check passed!")

    # Crea la directory di output se non esiste
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Verifica che il sistema abbia i prerequisiti necessari alla conversione
    CheckPreconditions()

    # Crea la nota .md unita
    combined_note_path = CombineNotes(matching_files_main)
    # sys.exit(1)

    # Se arrivato qui allora può eseguire la conversione
    NoteConversion(combined_note_path) # deve prendere la nota combinata dal build

def ConversionAllNote(custom):
    global OUTPUT_DIR
    bank_dir = safe_path(SCRIPT_DIR, "..", "bank")
    collab_file = safe_path(bank_dir, COLLAB_FILE)
    global is_bank
    
    if os.path.exists(collab_file):
        is_bank = True
        
    if not is_bank:
        """
        comportamento di default in un vault classico
        - crea la cartella di build
        - ci inserisce la nota combinata
        - la converte nella cartella di build 
        """
        # Ottieni i file corrispondenti all'argomento
        print("Consistency check started...")
        matching_files_main = get_all_files_from_main(custom)
        matching_files_root = get_all_files_from_root()
        
        if not custom:
            checkInconsistency(matching_files_main, matching_files_root)
        print("Consistency check passed!")

        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
        os.chdir(safe_path(OUTPUT_DIR))
        
        # Verifica che il sistema abbia i prerequisiti necessari alla conversione
        CheckPreconditions()
        
        combined_note_path = CombineNotes(matching_files_main)

    else:
        """
        comportamento in una banca dati collaborativa
        - crea la cartella di build nei documenti del pc
        - ci inserisce la nota combinata in Documents/DocScript/build
        - ci copia gli assets in in Documents/DocScript/assets
        - ci copia i file di configurazione template e lua_filter in Documents/DocScript/config
        - ritorna alla cartella del vault copiando il risultato da Documents/DocScript/build
        """
        matching_files_main = []
        matching_files_main, collaborators = get_all_files_from_collab_main(custom)
        
        OUTPUT_DIR = safe_path(APPLICATION_DIR, BUILD_DIR_NAME)
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        os.chdir(OUTPUT_DIR)
        
        # No consistency check
        
        # Verifica che il sistema abbia i prerequisiti necessari alla conversione
        CheckPreconditions()
        
        combined_note_path = SearchAndCombineNotes(matching_files_main)
        
        # Copia la nota combinata nella cartella di build
        shutil.copy2(combined_note_path, OUTPUT_DIR / combined_note_path.name)
        
        # Copia gli assets nella cartella di build
        assets_dir = Path(os.path.join(APPLICATION_DIR, ASSETS_DIR_NAME)).resolve()
        CopyAssets(assets_dir, collaborators)
        
        # Copia dei template e lua_filter
        template_dir = Path(os.path.join(APPLICATION_DIR, CONFIG_DIR_NAME)).resolve()
        template_dir.mkdir(parents=True, exist_ok=True)
        
        if custom_teml_path == None:
            shutil.copy2(TEMPLATE_PATH, template_dir / TEMPLATE_NAME)
        else:
            shutil.copy2(custom_teml_path, template_dir / TEMPLATE_NAME) # copio il custom rinominandolo a default cosí nella funznione Note conversion rimane seplificato
        
        if custom_luaf_path == None:
            shutil.copy2(LUA_FILTER_PATH, template_dir / LUA_FILTER_NAME)
        else:
            shutil.copy2(custom_luaf_path, template_dir / LUA_FILTER_NAME)
        
        if custom_pandoc_opt_path == None:
            shutil.copy2(PANDOC_OPT_PATH, template_dir / PANDOC_OPT_NAME)
        else:
            shutil.copy2(custom_pandoc_opt_path, template_dir / PANDOC_OPT_NAME)
    
    # Se arrivato qui allora può eseguire la conversione
    NoteConversion(os.path.basename(combined_note_path)) # deve prendere la nota combinata dal build
    
    if is_bank:
        # Copia l'output nella cartella di build della banca dati
        MAKE_DIR.mkdir(parents=True, exist_ok=True)
        out_name = Path(OUTPUT_PATH).name
        shutil.copy2(Path(os.path.join(APPLICATION_DIR, BUILD_DIR_NAME, out_name)).resolve(), Path(MAKE_DIR).resolve())
        
        # Cancella la cartella di build temporanea
        for _ in range(3):
            try:
                shutil.rmtree(APPLICATION_DIR, onerror=remove_readonly)
                break
            except Exception as e:
                time.sleep(1)

def AddStartNewNote(note_path):
    """
    Aggiunge una nuova nota copiando il file void-notes.md e spostandolo nella posizione specificata.
    """
    
    if custom_new_note_path:
        starting_note = custom_new_note_path
    else:
        starting_note = NEW_NOTE_PATH
    
    # Verifica che il file template esista
    if not os.path.exists(starting_note):
        print(f"Errore: il file template '{starting_note}' non esiste.")
        sys.exit(1)
    
    # Percorso completo della nuova nota
    vault_path      = safe_path(SCRIPT_DIR, "..", "vault")
    new_note_path   = safe_path(vault_path, note_path)
    
    # Verifica che il macro-argomento esista
    macro_argomento_dir = safe_path(vault_path, note_path.split("/")[0])
    if not os.path.exists(macro_argomento_dir) or not os.path.isdir(macro_argomento_dir):
        print(f"Errore: il macro-argomento '{note_path.split('/')[0]}' non esiste. Crealo manualmente prima di aggiungere note.")
        sys.exit(1)
        
    # Verifica che il nome della nota sia valido
    note_name = os.path.basename(note_path)
    if not re.match(rf"^main\.{note_path.split('/')[0]}(?:\..+)?\.md$", note_name):
        print(f"Errore: il nome della nota '{note_name}' non è valido. Deve iniziare con 'main.macro-argomento1.' e terminare con '.md'.")
        sys.exit(1)

    # Copia il file template e lo rinomina
    try:
        with open(starting_note, "r", encoding="utf-8") as template_file:
            content = template_file.read()
        
        with open(new_note_path, "w", encoding="utf-8") as new_note_file:
            new_note_file.write(content)
        
        print(f"Nota creata con successo: {new_note_path}")
    except Exception as e:
        print(f"Errore durante la creazione della nota: {e}")
        sys.exit(1)

def NoteConversion(combined_note_path):    
    if is_bank:
        path_note   = safe_path(APPLICATION_DIR, BUILD_DIR_NAME, COMB_FILE_NAME)
        out_path    = safe_path(APPLICATION_DIR, BUILD_DIR_NAME, Path(OUTPUT_PATH).name)
        template    = safe_path(APPLICATION_DIR, CONFIG_DIR_NAME, TEMPLATE_NAME)    # Per banca dati condivisa ConversionAllNote() copia il file rinominandolo come l'originale di default
        lua_filter  = safe_path(APPLICATION_DIR, CONFIG_DIR_NAME, LUA_FILTER_NAME)  # Per banca dati condivisa ConversionAllNote() copia il file rinominandolo come l'originale di default
        default_opt = safe_path(APPLICATION_DIR, CONFIG_DIR_NAME, PANDOC_OPT_NAME)  # Per banca dati condivisa ConversionAllNote() copia il file rinominandolo come l'originale di default
    else:
        # Altrimenti converto normalmente nella cartella di build in quanto ho giá tutto in locale
        path_note   = safe_path(combined_note_path)
        out_path    = safe_path(OUTPUT_PATH)
        template    = safe_path(TEMPLATE_PATH)
        if custom_teml_path:
            template    = safe_path(custom_teml_path)
        lua_filter  = safe_path(LUA_FILTER_PATH)
        if custom_luaf_path:
            lua_filter  = safe_path(custom_luaf_path)
        default_opt  = safe_path(PANDOC_OPT_PATH)
        if custom_pandoc_opt_path:
            default_opt  = safe_path(custom_pandoc_opt_path)
        
    if isNetworkPath():
        # Eseguo prima la conversione in tex con pandoc
        out_path = out_path.with_suffix(".tex")
        
        command = f"pandoc \"{path_note}\" -o \"{out_path}\" --defaults=\"{default_opt}\" --template=\"{template}\" --lua-filter=\"{lua_filter}\" "
        
        print(f"Eseguo il comando: {command}")
        os.system(command)
        
        # Eseguo poi la conversione in pdf con latexmk
        subprocess.run(
            ["latexmk", "-xelatex", out_path.name],
            cwd=out_path.parent,    # la directory dove è stato creato il .tex1
            #shell=True
            check=True             # opzionale: solleva CalledProcessError se il comando fallisce
        )
        
        # Pulizia della cartella di build
        path = Path(out_path)
        folder = path.parent
        filename = path.stem  # es. 'file' da 'file.pdf'
        allowed = {f"{filename}.pdf", f"{filename}.tex"}

        for item in folder.iterdir():
            if item.is_file() and item.name.startswith(filename) and item.name not in allowed:
                print(f"Rimuovo: {item}")
                item.unlink()  # Cancella il file
        
    else:
        # Comando per la conversione pulita con pandoc
        command = f"pandoc \"{path_note}\" -o \"{out_path}\" --defaults=\"{default_opt}\" --template=\"{template}\" --lua-filter=\"{lua_filter}\" "
        
        # Esegui il comando
        print(f"Eseguo il comando: {command}")
        os.system(command)

def setup_argparse():
    """Configura l'argparse con gruppi mutuamente esclusivi"""    
    parser = argparse.ArgumentParser(
        prog="DocScript.py",
        description="DocScript - Conversione e gestione documentazione. Tips: genera un repo git vuoto e inserisci questo come un sottomodulo prima di lanciare un --init",
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio",
        add_help=False
    )

    # Gruppo 1: Operazioni singole (mutuamente esclusive fra loro, non accettano altri argomenti)
    group_standalone = parser.add_mutually_exclusive_group()
    group_standalone.add_argument("-i",     "--init",       action="store_true",        help="Inizializza un nuovo vault")
    group_standalone.add_argument("-ib",    "--init-bank",  action="store_true",        help="Inizializza una banca dati collaborativa")
    group_standalone.add_argument("-s",     "--start",          metavar="NOTE_NAME",    help="Crea una nuova nota")
    group_standalone.add_argument("-u",     "--update",     action="store_true",        help="Aggiorna la banca dati")
    group_standalone.add_argument("-h",     "--help",       action="store_true",        help="Mostra questo messaggio di aiuto")
    group_standalone.add_argument("-v",     "--version",    action="store_true",        help="Versione dello script")

    # Gruppo 2: Operazioni di conversione (mutuamente esclusive fra loro, ma accettano opzioni aggiuntive)
    group_conversion = parser.add_mutually_exclusive_group()
    group_conversion.add_argument("-a",     "--all",            metavar="OUTPUT",                           help="Converte tutte le note")
    group_conversion.add_argument("-g",     "--group",          nargs=2, metavar=("ARGUMENT", "OUTPUT"),    help="Converte un gruppo di note")
    group_conversion.add_argument("-n",     "--note",           nargs=2, metavar=("NOTE", "OUTPUT"),        help="Converte una singola nota")
    group_conversion.add_argument("-c",     "--custom",         metavar="OUTPUT",                           help="Conversione custom da file custom.md")

    # Gruppo 3: Opzioni aggiuntive (possono essere combinate con il gruppo 2)
    parser.add_argument("-y",   "--yaml",       metavar="YAML_NAME",        help="Applica un file YAML personalizzato diverso da quello nel main.md")
    parser.add_argument("-t",   "--template",   metavar="TEMPLATE_NAME",    help="Applica un file template.tex personalizzato diverso da quello di default")
    parser.add_argument("-l",   "--lua",        metavar="LUA_NAME",         help="Applica un file luafilter.lua personalizzato diverso da quello di default")
    parser.add_argument("-p",   "--pandoc",     metavar="PANDOC_NAME",      help="Applica un --metadata-file='PANDOC_NAME' diverso da quello di default")

    return parser

def validate_args(args):
    """Valida la coerenza degli argomenti"""
    # Se è un'operazione standalone, non deve avere altre opzioni
    standalone_ops = [args.init, args.init_bank, args.start, args.update, args.help, args.version]
    conversion_ops = [args.all, args.group, args.note, args.custom]

    # Conta quante operazioni standalone sono attive
    active_standalone = sum(1 for op in standalone_ops if op)

    # Se c'è un'operazione standalone attiva
    if active_standalone > 0:
        # Controlla che non ci siano operazioni di conversione
        active_conversion = sum(1 for op in conversion_ops if op)
        if active_conversion > 0:
            print("Errore: le operazioni -i, -ib, -s, -u, -h, -v non possono essere combinate con -a, -g, -n, -c")
            sys.exit(1)
        # Controlla che non ci siano opzioni aggiuntive
        if args.yaml or args.template:
            print("Errore: le operazioni -i, -ib, -s, -u, -h, -v non accettano opzioni aggiuntive")
            sys.exit(1)

    # Se non c'è nessuna operazione standalone, deve esserci almeno una di conversione
    # if active_standalone == 0:
    #     active_conversion = sum(1 for op in conversion_ops if op)
    #     if active_conversion == 0:
    #         print("Errore: deve essere specificata almeno un'operazione (-h, -a, -g, -n, -c, -i, -ib, -s, -u)")
    #         sys.exit(1)

## MAIN FUNCTION ##
def main():
    # Entro nella cartella build prima di eseguire il comando
    # Crea la directory di output se non esiste
    vault_path  = safe_path(SCRIPT_DIR, "..", "vault")
    bank_path   = safe_path(SCRIPT_DIR, "..", "bank")
    collab_path = safe_path(bank_path, COLLAB_FILE)
    
    global MAKE_DIR
    global OUTPUT_DIR
    
    global custom_teml_path, custom_luaf_path, custom_yaml_path, custom_pandoc_opt_path
    
    if os.path.exists(bank_path) or os.path.exists(vault_path):
        if not os.path.exists(collab_path):
            if os.path.exists(vault_path):
                build_dir = safe_path(OUTPUT_DIR)
                if not os.path.exists(build_dir):
                    os.makedirs(build_dir) # Entra nella cartella di build solo se esiste e se non é una banca dati
            os.chdir(safe_path(MAKE_DIR))
        else:
            # Aggiorno i path nel caso ci si trovi in una banca dati
            build_dir   = safe_path(bank_path, "build")
            OUTPUT_DIR  = build_dir
            MAKE_DIR    = OUTPUT_DIR
    
    global custom
    
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.help and not any([args.all, args.group, args.note, args.custom]):
        print(pyfiglet.figlet_format("Doc Script", font="slant"))
        parser.print_help()
        sys.exit(0)
        
    # Valida gli argomenti
    validate_args(args)

    # Operazioni standalone
    if args.init:
        print("Opzione --init selezionata. Creazione di un vault di partenza.")
        InitVault()

    elif args.init_bank:
        print("Opzione --init-bank selezionata. Creazione di una banca dati collaborativa.")
        InitBank()

    elif args.start:
        print(f"Opzione --start selezionata. Creazione della nuova nota: {args.start}")
        check_config_conversion_file()
        AddStartNewNote(args.start)

    elif args.update:
        print("Opzione --update selezionata. Lettura dei main.md dei collaboratori e costruzione del main.md complessivo.")
        UpdateBank()
    
    elif args.version:
        print("DocScript v"+PY_VERSION)

    # Operazioni di conversione (con opzioni aggiuntive opzionali)
    elif args.all:
        custom = False
        print("Opzione --all selezionata. Conversione di tutte le note.")
        # se non uscito per errori vari
        check_config_conversion_file()
        if args.yaml:
            print(f"  - Con yaml personalizzato: {args.template}")
            custom_yaml_path = add_new_yaml(args.yaml)
        if args.template:
            print(f"  - Con template personalizzato: {args.template}")
            custom_teml_path = add_new_teml(args.template)
        if args.lua:
            print(f"  - Con lua personalizzato: {args.lua}")
            custom_luaf_path = add_new_luaf(args.lua)
        if args.pandoc:
            print(f"  - Con pandoc opt personalizzato: {args.pandoc}")
            custom_pandoc_opt_path = add_new_yaml(args.pandoc)
        validate_output(args.all)
        ConversionAllNote(custom)
    
    elif args.group:
        if len(args.group) < 2:
            print("Errore: l'opzione --group richiede due argomenti: ARGUMENTO e OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        argomento, output = args.group
        validate_output(output)
        print(f"Opzione --group selezionata. Gruppo: {args.group}")
        # se non uscito per errori vari
        check_config_conversion_file()
        if args.yaml:
            print(f"  - Con yaml personalizzato: {args.template}")
            custom_yaml_path = add_new_yaml(args.yaml)
        if args.template:
            print(f"  - Con template personalizzato: {args.template}")
            custom_teml_path = add_new_teml(args.template)
        if args.lua:
            print(f"  - Con lua personalizzato: {args.lua}")
            custom_luaf_path = add_new_luaf(args.lua)
        if args.pandoc:
            print(f"  - Con pandoc opt personalizzato: {args.pandoc}")
            custom_pandoc_opt_path = add_new_yaml(args.pandoc)
        ConversionGroupNote(argomento)

    elif args.note:
        if len(args.note) < 2:
            print("Errore: l'opzione --note richiede due argomenti: NOTA e OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        nota, output = args.note
        validate_output(output)
        # se non uscito per errori vari
        check_config_conversion_file()
        print(f"Opzione --note selezionata. Nota: {nota}, Output: {output}")
        if args.yaml:
            print(f"  - Con yaml personalizzato: {args.template}")
            custom_yaml_path = add_new_yaml(args.yaml)
        if args.template:
            print(f"  - Con template personalizzato: {args.template}")
            custom_teml_path = add_new_teml(args.template)
        if args.lua:
            print(f"  - Con lua personalizzato: {args.lua}")
            custom_luaf_path = add_new_luaf(args.lua)
        if args.pandoc:
            print(f"  - Con pandoc opt personalizzato: {args.pandoc}")
            custom_pandoc_opt_path = add_new_yaml(args.pandoc)
        ConversionSingleNote(nota)

    elif args.custom:
        custom = True
        if not args.custom:
            print("Errore: l'opzione --custom richiede un argomento OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        validate_output(args.custom)
        print(f"Opzione --custom selezionata. Output: {args.custom}")
        # se non uscito per errori vari
        check_config_conversion_file()
        if args.yaml:
            print(f"  - Con yaml personalizzato: {args.template}")
            custom_yaml_path = add_new_yaml(args.yaml)
        if args.template:
            print(f"  - Con template personalizzato: {args.template}")
            custom_teml_path = add_new_teml(args.template)
        if args.lua:
            print(f"  - Con lua personalizzato: {args.lua}")
            custom_luaf_path = add_new_luaf(args.lua)
        if args.pandoc:
            print(f"  - Con pandoc opt personalizzato: {args.pandoc}")
            custom_pandoc_opt_path = add_new_yaml(args.pandoc)
        ConversionAllNote(custom)

    else:
        print(pyfiglet.figlet_format("Doc Script", font="slant"))
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()
    
    # todo: creare una funzione di Upgrade in modo da inizializzare di nuovo il vault con i nuovi file senza sovrascrivere quelli esistenti
