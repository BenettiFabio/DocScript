import argparse
import os
import re
import sys
import shutil
from pathlib import Path
import time
import stat
import pyfiglet
# import win32net # need pywin32
import subprocess

## DEFINES ##
NOTE_PATH = None
OUTPUT_PATH = None
TEMPORARY_DIR = "rusco"  # Macro per la cartella temporanea
TEMPLATE_NAME = "conversion-template.tex"  # Nome del template
LUA_FILTER_NAME = "graphic-template.lua"  # Nome del filtro Lua
COLLAB_FILE = "collaborator.md"
COMBINED_FILE_NAME = "combined_notes.md"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
TEMPLATE = Path(os.path.join(SCRIPT_DIR, TEMPLATE_NAME)).resolve()
LUA_FILTER = Path(os.path.join(SCRIPT_DIR, LUA_FILTER_NAME)).resolve()
MAKE_DIR = Path(os.path.join(SCRIPT_DIR, "..", "vault", "build")).resolve()
OUTPUT_DIR = MAKE_DIR


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
TEMPLATE = Path(os.path.join(SCRIPT_DIR, TEMPLATE_NAME)).resolve()
LUA_FILTER = Path(os.path.join(SCRIPT_DIR, LUA_FILTER_NAME)).resolve()
MAKE_DIR = Path(os.path.join(SCRIPT_DIR, "..", "vault", "build")).resolve()
OUTPUT_DIR = MAKE_DIR
HOME_DIR = Path.home()
APPLICATION_DIR = Path(os.path.join(HOME_DIR, "Documents", "DocuBank")).resolve()

service_flag = False # variabile per gestire varianti della stessa funzione nel comportamento normale o di servizio
custom = False # variabile per gestire la conversione di un file custom.md
is_bank = False

## FUNCTIONS ##
def convert_link_to_absolute(markdown_text, base_path):
    """
    Converte i link relativi Markdown in link assoluti mantenendo la sintassi Markdown.
    """
    base_path = Path(base_path).parent.resolve()

    def replacer(match):
        label = match.group(1)
        rel_path = match.group(2)
        abs_path = (base_path / rel_path).resolve()
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
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
            print(f"Assets copiati per {name} in {output_dir}")
        else:
            print(f"Attenzione: assets non trovati per {name} in {collab_assets_dir}")

def isNetworkPath():
    here = os.getcwd()
    return (here.startswith('\\\\') or not here.startswith('C:')) 

def to_unc_slash_path(windows_path: str) -> str:
    """
    Converte un path UNC di Windows con backslash (\\\\server\\share\\path)
    in un path UNC compatibile con strumenti esterni come pandoc (//server/share/path).
    """
    
    # Se inizia con \\ è un UNC path → rete
    if windows_path.startswith('\\\\'):
        
        # Rimuove eventuale prefisso \\?\ (che può apparire nei path Windows "lunghi")
        path_str = windows_path.replace('\\\\?\\', '')
        
        # ottengo tutti i drive di rete inseriti nel sistema
        result = subprocess.run("net use", capture_output=True, text=True, shell=True)
        lines = result.stdout.splitlines()
        mapped_drives = {}
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].endswith(":") and parts[1].startswith("\\\\"):
                drive_letter = parts[0]
                unc_path = parts[1]
                mapped_drives[drive_letter] = unc_path
        
        # Normalizza il path
        full_path = str(Path(path_str).resolve())
        normalized_path = full_path.replace("\\", "/")

        # Prova a sostituire con lettera di drive, se matcha
        for drive, unc in sorted(mapped_drives.items(), key=lambda x: len(x[1]), reverse=True):
            unc_norm = unc.replace("\\", "/")
            unc_parts = unc_norm.strip("/").split("/")
            full_parts = normalized_path.strip("/").split("/")
            
            try:
                # Trova la prima cartella condivisa
                idx = full_parts.index(unc_parts[-1])

                # Costruisci il path a partire dalla prima cartella trovata
                relative_parts = full_parts[idx + 1:]
                final_path = str(Path(drive + "/") / Path(*relative_parts)).replace("\\", "/")
                return final_path
            except ValueError:
                continue  # La cartella finale non è nel path completo, prova con il prossimo

        # Se non trovato, restituisco il path originale
        return windows_path # bypass
    else:
        return windows_path

def DeleteTempFile(temp_file_path):
    try:
        os.remove(temp_file_path)
    except Exception as e:
        print(f"Errore durante l'eliminazione del file temporaneo: {e}")
        sys.exit(1)

def MoveToCorrectPath(output_path):
    # Sposta il file di output nella cartella corretta
    try:
        print(f"Sposto il file{OUTPUT_PATH} in {output_path}")
        shutil.move(OUTPUT_PATH, os.path.join(output_path, OUTPUT_PATH.name))
        print(f"File di output spostato in: {os.path.join(output_path, OUTPUT_PATH.name)}")
    except Exception as e:
        print(f"Errore durante lo spostamento del file di output: {e}")
        sys.exit(1)

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

def CheckPreconditions():
    """
    Verifica che il sistema abbia i prerequisiti necessari per la conversione.
    Controlla se xelatex e pandoc sono installati e disponibili nel PATH.
    """
    
    # Controlla se xelatex è nel PATH
    if os.system("where xelatex >nul 2>nul") != 0:
        print("Errore: xelatex non installato o non nel PATH.")
        sys.exit(1)
    else:
        print("xelatex installato.")

    # Controlla se pandoc è nel PATH
    if os.system("where pandoc >nul 2>nul") != 0:
        print("Errore: pandoc non installato o non nel PATH.")
        sys.exit(1)
    else:
        print("pandoc installato.")

    # Controlla se i font GNU FreeFonts sono installati
    if os.system('fc-list | findstr /i "FreeSerif FreeSans FreeMono" >nul 2>nul') != 0:
        print("Errore: i font GNU FreeFonts non sono installati.")
        sys.exit(1)
    else:
        print("Font GNU FreeFonts installati.")

def get_all_files_from_main(custom):
    """
    Legge il file main.md (o custom.md) e restituisce una lista di tutti i file .md referenziati.
    """
    # Percorso del file main.md o custom.md
    main_md_path = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve())))
    if (custom):
        main_md_path = os.path.join(main_md_path, "custom.md")
    else:
        main_md_path = os.path.join(main_md_path, "main.md")

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
    bank_dir = Path(to_unc_slash_path(str(os.path.join(SCRIPT_DIR, "..", "bank"))))
    if custom:
        main_md_path = Path(os.path.join(bank_dir, "custom.md")).resolve()
    else:
        main_md_path = Path(os.path.join(bank_dir, "main.md")).resolve()
    collab_file = Path(os.path.join(bank_dir, COLLAB_FILE)).resolve()

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

    return matching_files, collaborators
    
def get_files_for_argument_from_main(argomento):
    """
    Legge il file main.md e restituisce una lista di file che corrispondono all'argomento specificato.
    """
    # Percorso del file main.md
    main_md_path = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "vault", "main.md")).resolve())))

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
            start_idx = line.find("(") + 1
            end_idx = line.find(")")
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
    root_vault_path = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve())))
    matched_files = []

    for root, dirs, files in os.walk(root_vault_path):
        # Escludi le directory non volute
        dirs[:] = [d for d in dirs if d not in ('assets', 'build')]

        for file in files:
            if file.endswith(".md"):
                if file == "main.md" or file == "custom.md":
                    continue
                full_path = os.path.join(root, file)
                matched_files.append(full_path)

    return matched_files

def get_files_for_argument_from_root(argomento):
    """
    Legge tutti i file nel vault e restituisce una lista di file che corrispondono all'argomento specificato.
    """
    # Percorso del file main.md
    root_vault_path = Path(to_unc_slash_path(str(Path(os.path.join("..", "vault")))))
    matched_files = []

    # Pattern da cercare nel nome del file
    pattern = re.compile(rf'^main\.{re.escape(argomento)}\..*\.md$')

    for root, dirs, files in os.walk(root_vault_path):
        # Escludi le directory non volute
        dirs[:] = [d for d in dirs if d not in ('assets', 'build')]

        for file in files:
            if file == "main.md" or file == "custom.md":
                continue
            if file.endswith(".md") and pattern.match(file):
                full_path = os.path.join(root, file)
                matched_files.append(full_path)
    
    return matched_files

def SearchAndCombineNotes(matching_files):
    """
    Combina le note corrispondenti in un unico file .md, rimuovendo l'header specificato.
    """
    combined_file_path_temp = Path(os.path.join(MAKE_DIR, COMBINED_FILE_NAME))
    combined_file_path =  Path(to_unc_slash_path(str(combined_file_path_temp.resolve())))
    
    # Crea la directory di output se non esiste
    if not os.path.exists(MAKE_DIR):
        os.makedirs(MAKE_DIR)

    vault_dir = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve())))
    with open(combined_file_path, "w", encoding="utf-8") as combined_md_file:
        for file in matching_files:
            file_path = os.path.join(vault_dir, file)
            if os.path.exists(file_path):
                # Ottieni il contenuto senza header
                filtered_lines = RemoveHeaderFromFile(file_path)

                # Scrivi il contenuto filtrato nel file combinato
                combined_md_file.writelines(filtered_lines)
                combined_md_file.write("\n")
            else:
                print(f"Avviso: il file '{file}' non è stato trovato e sarà ignorato.")

    print(f"File combinato creato: {combined_file_path}")
    return combined_file_path

def CombineNotes(matching_files):
    """
    Combina le note corrispondenti in un unico file .md, rimuovendo l'header specificato.
    """
    combined_file_path_temp = Path(os.path.join(MAKE_DIR, COMBINED_FILE_NAME))
    combined_file_path = Path(to_unc_slash_path(str(combined_file_path_temp.resolve())))

    # Crea la directory di output se non esiste
    if not os.path.exists(MAKE_DIR):
        os.makedirs(MAKE_DIR)

    vault_dir = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve())))
    
    with open(combined_file_path, "w", encoding="utf-8") as combined_md_file:
        for file in matching_files:
            file_path = os.path.join(vault_dir, file)
            if os.path.exists(file_path):
                # Ottieni il contenuto senza header
                filtered_lines = RemoveHeaderFromFile(file_path)

                # Scrivi il contenuto filtrato nel file combinato
                combined_md_file.writelines(filtered_lines)
                combined_md_file.write("\n")
            else:
                print(f"Avviso: il file '{file}' non è stato trovato e sarà ignorato.")

    print(f"File combinato creato: {combined_file_path}")
    return combined_file_path

def checkInconsistency(matching_files_main, matching_files_root):
    """
    Controlla che tutti i file effettivi siano referenziati nel main.
    Se mancano delle note nel main, stampa un errore con i file mancanti.
    I percorsi vengono normalizzati per il confronto.
    """
    # Filtra i file per escludere quelli nella cartella temporanea
    filtered_matching_files_root = [
        Path(path).name for path in matching_files_root
        if not path.startswith(f"{TEMPORARY_DIR}/") and not Path(path).name.startswith("main.rusco.")
    ]

    normalized_actual_list = [
        # os.path.relpath(path, os.path.join("..")).replace("\\", "/")
        Path(path).name for path in filtered_matching_files_root
    ]
    
    normalized_main_list = [
        # os.path.relpath(path, os.path.join("..")).replace("\\", "/")
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
    filtered_lines = []
    for line in lines:
        if "<!-- /code_chunk_output -->" in line:
            content_started = True
            continue
        if content_started:
            filtered_lines.append(line)

    # Se l'header non è stato trovato, restituisci l'intero contenuto
    if not content_started:
        print(f"Avviso: header non trovato nel file '{file_path}'. Restituisco il contenuto completo.")
        return lines

    return filtered_lines

##############################
## FUNCTIONS FOR CONVERSION ##
##############################
def InitBank():
    print("Inizializzazione della banca dati collaborativa...")
    parent_dir = Path(os.path.join(SCRIPT_DIR, "..")).resolve()
    template_dir = Path(os.path.join(SCRIPT_DIR, "templates", "init-bank")).resolve()
    collab_file = Path(os.path.join(parent_dir, COLLAB_FILE)).resolve()
    bank_dir = Path(os.path.join(parent_dir, "bank")).resolve()
    vault_dir = Path(os.path.join(parent_dir, "vault")).resolve()
    
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
        
        # Copia il contenuto della cartella init-bank nella cartella superiore
        for root, dirs, files in os.walk(template_dir):
            relative_path = os.path.relpath(root, template_dir)
            target_dir = os.path.join(bank_dir, relative_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(target_dir, file)
                shutil.copy(src_file, dest_file)
        print(f"Struttura del banca dati costruita con successo")
        print(f"Per iniziare compila il file {COLLAB_FILE} con i tuoi collaboratori.")
        print(f"Successivamente lancia un -u (--update) per aggiornare il file main.md")
        print(f"Enjoy working with you team mates! <3")
        
    except Exception as e:
        print(f"Errore durante l'inizializzazione: {e}")
        sys.exit(1)

def InitVault():
    """
    Inizializza la struttura del vault copiando i file e le cartelle necessarie.
    """
    parent_dir = Path(os.path.join(SCRIPT_DIR, "..")).resolve()
    vault_dir = Path(os.path.join(parent_dir, "vault")).resolve()
    template_dir = Path(os.path.join(SCRIPT_DIR, "templates", "init-vault")).resolve()
    setup_dir = Path(os.path.join(SCRIPT_DIR, "templates", "setup-vault")).resolve()
    bank_dir = Path(os.path.join(parent_dir, "bank")).resolve()

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

        # Copia il contenuto della cartella init-vault nella cartella 'vault'
        for root, dirs, files in os.walk(template_dir):
            relative_path = os.path.relpath(root, template_dir)
            target_dir = os.path.join(vault_dir, relative_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(target_dir, file)
                # Rinomina init-main.md in main.md durante la copia
                if file == "init-main.md":
                    dest_file = os.path.join(target_dir, "main.md")
                shutil.copy(src_file, dest_file)
        print(f"Struttura del Vault costruita con successo")

        # Copia tutto il contenuto della cartella setup-vault fuori dalla cartella 'vault'
        for root, dirs, files in os.walk(setup_dir):
            relative_path = os.path.relpath(root, setup_dir)
            target_dir = os.path.join(parent_dir, relative_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(target_dir, file)
                shutil.copy(src_file, dest_file)
        print(f"File di setup per VSCode copiati con successo")
        
        print(f"Enjoy your new vault! <3 ")
    
    except Exception as e:
        print(f"Errore durante la costruzione del Vault: {e}")
        sys.exit(1)

def UpdateBank():
    print("Aggiornamento della banca dati collaborativa...")
    bank_dir = Path(os.path.join(SCRIPT_DIR, "..", "bank")).resolve()
    collab_file = os.path.join(bank_dir, COLLAB_FILE)
    main_bank_path = os.path.join(bank_dir, "main.md")
    if not os.path.exists(collab_file):
        print(f"Errore: il file '{collab_file}' non esiste.")
        sys.exit(1)

    # Check del file collaborator.md
    with open(collab_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    collaborator = None
    errors = []
    collab_mainmd = []  # Lista di tuple (nome, path_mainmd)
    for line in lines:
        line = line.strip()
        if line.startswith("##"):
            collaborator = line[2:].strip()
        # Cerca link markdown a main.md
        match = re.search(r'\[.*?\]\((.*?main\.md)\)', line)
        if match:
            main_md_path = os.path.join("..", match.group(1))
            if not os.path.exists(Path(to_unc_slash_path(str(main_md_path)))):
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

def ConversionSingleTikzNote(nota):
    global NOTE_PATH
    NOTE_PATH = None  # Inizializza come None per indicare che non è stato trovato
    # Directory di partenza
    asset_path = os.path.join("..", "assets")	

    # Cerca il file nelle sottocartelle di assets, escludendo tutto che non sia .md
    for root, dirs, files in os.walk(asset_path):
        # Cerca il file .md corrispondente
        for file in files:
            if file == nota and file.endswith(".md"):
                NOTE_PATH = Path(os.path.join(root, file)).resolve()
                break
        if NOTE_PATH:
            break
    
    # Se non trovato
    if not NOTE_PATH:
        print(f"Errore: il file '{nota}' non è stato trovato negli assets.")
        sys.exit(1)

    # Verifica che il file si trovi nel percorso corretto
    relative_path = os.path.relpath(NOTE_PATH, os.path.join("..", "assets")).replace("\\", "/")
    if not re.match(r"^[^/]+/pdfs/tikz-pdfs/.*\.md$", relative_path):
        print(f"Errore: il file '{relative_path}' non si trova nel percorso corretto. Deve essere in 'assets/macro-argomento/pdfs/tikz-pdfs'.")
        sys.exit(1)
    
    # Se la nota é presente nel punto corretto allora la cartella esiste per forza non la creo    
    output_path = Path(os.path.join(NOTE_PATH, "..", "..")).resolve()
    
    # Verifica che il sistema abbia i requisiti necessari alla conversione    
    CheckPreconditions()

    # Ottieni il contenuto senza header
    filtered_lines = RemoveHeaderFromFile(NOTE_PATH)

    # Scrivi il contenuto filtrato in un file temporaneo
    temp_file_path = os.path.join(MAKE_DIR, COMBINED_FILE_NAME)
    with open(temp_file_path, "w", encoding="utf-8") as temp_file:
        temp_file.writelines(filtered_lines)

    # Esegui la conversione sul file temporaneo
    NoteConversion(temp_file_path)
    
    # Elimina il file temporaneo
    DeleteTempFile(temp_file_path)
    MoveToCorrectPath(output_path)

def ConversionSingleNote(nota):
    global NOTE_PATH
    NOTE_PATH = None  # Inizializza come None per indicare che non è stato trovato

    # Directory di partenza
    vault_path = os.path.join("..")

    # Cerca il file nelle sottocartelle di vault, escludendo assets/ e build/
    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in ["assets", "build"]]

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
    if not os.path.exists(Path(to_unc_slash_path(str(OUTPUT_DIR)))):
        os.makedirs(Path(to_unc_slash_path(str(OUTPUT_DIR))))
    
    # Verifica che il sistema abbia i requisiti necessari alla conversione    
    CheckPreconditions()

    # Ottieni il contenuto senza header
    filtered_lines = RemoveHeaderFromFile(NOTE_PATH)

    # Scrivi il contenuto filtrato in un file temporaneo
    temp_file_path = os.path.join(MAKE_DIR, COMBINED_FILE_NAME)
    temp_file_path = Path(to_unc_slash_path(str(temp_file_path)))
    with open(temp_file_path, "w", encoding="utf-8") as temp_file:
        temp_file.writelines(filtered_lines)

    # Esegui la conversione sul file temporaneo
    NoteConversion(temp_file_path)
        
    # Elimina il file temporaneo
    try:
        os.remove(temp_file_path)
    except Exception as e:
        print(f"Errore durante l'eliminazione del file temporaneo: {e}")

def ConversionGroupNote(argomento):
    # Ottieni i file corrispondenti all'argomento
    matching_files_main = get_files_for_argument_from_main(argomento)
    matching_files_root = get_files_for_argument_from_root(argomento)
    
    checkInconsistency(matching_files_main, matching_files_root)

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
    bank_dir = os.path.join(SCRIPT_DIR, "..", "bank") 
    collab_file = os.path.join(bank_dir, COLLAB_FILE)
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
        matching_files_main = []
        matching_files_root = []
        matching_files_main = get_all_files_from_main(custom)
        matching_files_root = get_all_files_from_root()
        
        if not custom:
            checkInconsistency(matching_files_main, matching_files_root)
            
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
        os.chdir(Path(to_unc_slash_path(str(OUTPUT_DIR))))
        
        # Verifica che il sistema abbia i prerequisiti necessari alla conversione
        CheckPreconditions()
        
        combined_note_path = CombineNotes(matching_files_main)

    else:
        """
        comportamento in una banca dati collaborativa
        - crea la cartella di build nei documenti del pc
        - ci inserisce la nota combinata in Documents/DocuBank/build
        - ci copia gli assets in in Documents/DocuBank/assets
        - ci copia i file template e lua_filter in Documents/DocuBank/template
        """
        matching_files_main = []
        matching_files_main, collaborators = get_all_files_from_collab_main(custom)
        
        OUTPUT_DIR = Path(os.path.join(APPLICATION_DIR, "build")).resolve()
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
        assets_dir = Path(os.path.join(APPLICATION_DIR, "assets")).resolve()
        CopyAssets(assets_dir, collaborators)
        
        # Copia dei template e lua_filter
        template_dir = Path(os.path.join(APPLICATION_DIR, "templates")).resolve()
        template_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATE, template_dir / TEMPLATE_NAME)
        shutil.copy2(LUA_FILTER, template_dir / LUA_FILTER_NAME)
        
    # Se arrivato qui allora può eseguire la conversione
    NoteConversion(os.path.basename(combined_note_path)) # deve prendere la nota combinata dal build
    
    if is_bank:
        # Copia l'output nella cartella di build della banca dati
        MAKE_DIR.mkdir(parents=True, exist_ok=True)
        out_name = Path(OUTPUT_PATH).name
        shutil.copy2(Path(os.path.join(APPLICATION_DIR, "build", out_name)).resolve(), Path(MAKE_DIR).resolve())
        
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
    # Percorso del file template
    template_path = Path(to_unc_slash_path(str(os.path.join(SCRIPT_DIR, "templates", "void-notes.md"))))
    
    # Verifica che il file template esista
    if not os.path.exists(template_path):
        print(f"Errore: il file template '{template_path}' non esiste.")
        sys.exit(1)
    
    # Percorso completo della nuova nota
    vault_path = Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve()
    new_note_path = Path(to_unc_slash_path(str(Path(os.path.join(vault_path, note_path)).resolve())))
    
    # Verifica che non esista già una nota con lo stesso nome
    if os.path.exists(new_note_path):
        print(f"Errore: esiste già una nota con il nome '{note_path}'.")
        sys.exit(1)

    # Verifica che il macro-argomento esista
    macro_argomento_dir = Path(to_unc_slash_path(str(Path(os.path.join(vault_path, note_path.split("/")[0])).resolve())))
    print(macro_argomento_dir)
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
        with open(template_path, "r", encoding="utf-8") as template_file:
            content = template_file.read()
        
        with open(new_note_path, "w", encoding="utf-8") as new_note_file:
            new_note_file.write(content)
        
        print(f"Nota creata con successo: {new_note_path}")
    except Exception as e:
        print(f"Errore durante la creazione della nota: {e}")
        sys.exit(1)

def NoteConversion(combined_note_path):
    
    if is_bank:
        # - esegui il comando pandoc in locale da quella cartella temponanea
        # - sposta l'output dalla build temp a quella effettiva di rete da cui é stato lanciato il comando
        path_note = Path(os.path.join(APPLICATION_DIR, "build", COMBINED_FILE_NAME)).resolve()
        out_path = Path(os.path.join(APPLICATION_DIR, "build", Path(OUTPUT_PATH).name)).resolve()
        template = Path(os.path.join(APPLICATION_DIR, "templates", TEMPLATE_NAME)).resolve()
        lua_filter = Path(os.path.join(APPLICATION_DIR, "templates", LUA_FILTER_NAME)).resolve()
    else:
        # Altrimenti converto normalmente nella cartella di build in quanto sono giá offline
        path_note = Path(to_unc_slash_path(str(combined_note_path)))
        out_path = Path(to_unc_slash_path(str(OUTPUT_PATH)))
        template = Path(to_unc_slash_path(str(TEMPLATE)))
        lua_filter = Path(to_unc_slash_path(str(LUA_FILTER)))
        
    if isNetworkPath():
        # Eseguo prima la conversione in tex con pandoc
        out_path = out_path.with_suffix(".tex")
        if not service_flag:
            command = f"pandoc \"{path_note}\" -o \"{out_path}\" --toc --toc-depth=3 --template=\"{template}\" --lua-filter=\"{lua_filter}\" --listings --pdf-engine=xelatex"
        else:
            command = f"pandoc \"{path_note}\" -o \"{out_path}\" --template=\"{template}\" --lua-filter=\"{lua_filter}\" --listings --pdf-engine=xelatex"
        
        print(f"Eseguo il comando: {command}")
        os.system(command)
        
        # Eseguo poi la conversione in pdf con latexmk
        subprocess.run(
            ["latexmk", "-xelatex", out_path.name],
            cwd=out_path.parent,
            shell=True
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
        if not service_flag:
            command = f"pandoc \"{path_note}\" -o \"{out_path}\" --toc --toc-depth=3 --template=\"{template}\" --lua-filter=\"{lua_filter}\" --listings --pdf-engine=xelatex"
        else:
            command = f"pandoc \"{path_note}\" -o \"{out_path}\" --template=\"{template}\" --lua-filter=\"{lua_filter}\" --listings --pdf-engine=xelatex"
        
        # Esegui il comando
        print(f"Eseguo il comando: {command}")
        os.system(command)


## MAIN FUNCTION ##
def main():
    # Entro nella cartella build prima di eseguire il comando
    # Crea la directory di output se non esiste
    vault_path = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "vault")).resolve())))
    bank_path = Path(to_unc_slash_path(str(Path(os.path.join(SCRIPT_DIR, "..", "bank")).resolve())))
    collab_path = Path(to_unc_slash_path(str(Path(os.path.join(bank_path, COLLAB_FILE)).resolve())))
    
    global MAKE_DIR
    global OUTPUT_DIR
    
    if os.path.exists(bank_path) or os.path.exists(vault_path):
        if not os.path.exists(collab_path):
            if os.path.exists(vault_path):
                build_dir = Path(to_unc_slash_path(str(OUTPUT_DIR)));
                if not os.path.exists(build_dir):
                    os.makedirs(build_dir) # Entra nella cartella di build solo se esiste e se non é una banca dati
            os.chdir(Path(to_unc_slash_path(str(MAKE_DIR))))
        else:
            # Aggiorno i path nel caso ci si trovi in una banca dati
            build_dir = Path(os.path.join(bank_path, "build")).resolve()
            OUTPUT_DIR = build_dir
            MAKE_DIR = OUTPUT_DIR
    
    global custom
    
    # Creazione del parser
    parser = argparse.ArgumentParser(
        prog="make.py",
        description="Make script per gestire la conversione di note in PDF. Tips: genera un repo git vuoto e inserisci questo come un sottomodulo prima di lanciare un --init",
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio",
        add_help=False
    )
    # Aggiunta delle opzioni
    parser.add_argument("-i", "--init",         action="store_true",                            help="Inizializza la struttura del vault in modo che sia consistente per il make.py")
    parser.add_argument("-a", "--all",                      metavar="OUTPUT",                   help="Converte tutto il repository in un unico file di output, usando il main.md come ordinamento")
    parser.add_argument("-g", "--group",        nargs=2,    metavar=("ARGOMENTO", "OUTPUT"),    help="Converte un macro-argomento specificato in un file di output, usando main.md come ordinamento")
    parser.add_argument("-n", "--note",         nargs=2,    metavar=("NOTA", "OUTPUT"),         help="Converte una nota specificata in un file di output")
    parser.add_argument("-s", "--start",                    metavar="NOTE_PATH",                help="Aggiunge una nuova nota specificata in NOTE_PATH")
    parser.add_argument("-c", "--custom",                   metavar="OUTPUT",                   help="Converte tutte le note incluse nel file custom.md in un file di output")
    parser.add_argument("-nt", "--note-tikz",   nargs=2,    metavar=("NOTA", "OUTPUT"),         help="Converte una nota specificata considerandola come un file TikZ -> output in assets/")
    parser.add_argument("-ib", "--init-bank",   action="store_true",                            help="Inizializza vault-bank per la gestione condivisa delle note con collaboratori")
    parser.add_argument("-u",  "--update",      action="store_true",                            help="Aggiorna il file main.md della banca dati, necessaria inizializzazione con -ib")
    parser.add_argument("-h",  "--help",        action="store_true",                            help="Stampa l'help ed esce")

    # Parsing degli argomenti
    args = parser.parse_args()

    # Gestione delle opzioni
    if args.all:
        if not args.all:
            print("Errore: l'opzione --all richiede un argomento OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        validate_output(args.all)
        print(f"Opzione --all selezionata. Output: {args.all}")
        # Inizio conversione
        ConversionAllNote(custom)
        
    elif args.group:
        if len(args.group) < 2:
            print("Errore: l'opzione --group richiede due argomenti: ARGOMENTO e OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        argomento, output = args.group
        validate_output(output)
        print(f"Opzione --group selezionata. Argomento: {argomento}, Output: {output}")
        # Inizio conversione
        ConversionGroupNote(argomento)
        
    elif args.note:
        if len(args.note) < 2:
            print("Errore: l'opzione --note richiede due argomenti: NOTA e OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        nota, output = args.note
        validate_output(output)
        print(f"Opzione --note selezionata. Nota: {nota}, Output: {output}")
        # Inizio conversione
        ConversionSingleNote(nota)
    
    elif args.note_tikz:
        global service_flag
        if len(args.note_tikz) < 2:
            print("Errore: l'opzione --note-tikz richiede due argomenti: NOTA e OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        nota, output = args.note_tikz
        validate_output(output)
        print(f"Opzione --note selezionata. Nota: {nota}, Output: {output}")
        # Inizio conversione
        service_flag = True
        ConversionSingleTikzNote(nota)
        
    elif args.start:
        print(f"Opzione --start selezionata. Creazione della nuova nota: {args.start}")
        AddStartNewNote(args.start)
        
    elif args.custom:
        custom = True
        if not args.custom:
            print("Errore: l'opzione --custom richiede un argomento OUTPUT (in formato .pdf o .tex).")
            sys.exit(1)
        validate_output(args.custom)
        print(f"Opzione --custom selezionata. Output: {args.custom}")
        # Inizio conversione
        ConversionAllNote(custom)
        
    elif args.init:
        print(f"Opzione --init selezionata. Creazione di un vault di partenza.")
        InitVault()
        
    elif args.init_bank:
        print(f"Opzione --init-bank selezionata. Creazione di una banca dati collaborativa.")
        InitBank()
        
    elif args.update:
        print(f"Opzione --update selezionata. Lettura dei main.md dei collaboratori e costruzione del main.md complessivo.")
        UpdateBank()
        
    elif args.help:
        print(pyfiglet.figlet_format("DocuBank", font="slant"))
        parser.print_help()
        sys.exit(0)
    else:
        print(pyfiglet.figlet_format("DocuBank", font="slant"))
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()