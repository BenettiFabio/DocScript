import argparse
import os
import re
import sys
import shutil
from pathlib import Path

## DEFINES ##
NOTE_PATH = None
OUTPUT_PATH = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory dello script
TEMPLATE = os.path.join(SCRIPT_DIR, "conversion-template.tex")
LUA_FILTER = os.path.join(SCRIPT_DIR, "graphic-template.lua")
MAKE_DIR = os.path.join(SCRIPT_DIR, "..", "vault", "build")
OUTPUT_DIR = MAKE_DIR

custom = False # variabile per gestire la conversione di un file custom.md

## FUNCTIONS ##
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
    main_md_path = None
    if (custom):
        main_md_path = os.path.join("..", "custom.md")
    else:
        main_md_path = os.path.join("..", "main.md")

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

def get_files_for_argument_from_main(argomento):
    """
    Legge il file main.md e restituisce una lista di file che corrispondono all'argomento specificato.
    """
    # Percorso del file main.md
    main_md_path = os.path.join("..", "main.md")

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
    root_vault_path = os.path.join("..")
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
    root_vault_path = os.path.join("..", "vault")
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

def CombineNotes(matching_files):
    """
    Combina le note corrispondenti in un unico file .md, rimuovendo l'header specificato.
    """
    combined_file_path_temp = Path(os.path.join(MAKE_DIR, "combined_notes.md"))
    combined_file_path = combined_file_path_temp.resolve()

    # Crea la directory di output se non esiste
    if not os.path.exists(MAKE_DIR):
        os.makedirs(MAKE_DIR)

    with open(combined_file_path, "w", encoding="utf-8") as combined_md_file:
        for file in matching_files:
            file_path = os.path.join("..", file)
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
    normalized_actual_list = [
        os.path.relpath(path, os.path.join("..")).replace("\\", "/")
        for path in matching_files_root
    ]
    
    main_set = set(matching_files_main)
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

    return filtered_lines

##############################
## FUNCTIONS FOR CONVERSION ##
##############################
def InitVault():
    """
    Inizializza la struttura del vault copiando i file e le cartelle necessarie.
    """
    parent_dir = Path(os.path.join(SCRIPT_DIR, "..")).resolve()
    vault_dir = Path(os.path.join(parent_dir, "vault")).resolve()
    template_dir = Path(os.path.join(SCRIPT_DIR, "templates", "init-vault")).resolve()
    setup_dir = Path(os.path.join(SCRIPT_DIR, "templates", "setup-vault")).resolve()

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
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Verifica che il sistema abbia i requisiti necessari alla conversione    
    CheckPreconditions()

    # Ottieni il contenuto senza header
    filtered_lines = RemoveHeaderFromFile(NOTE_PATH)

    # Scrivi il contenuto filtrato in un file temporaneo
    temp_file_path = os.path.join(MAKE_DIR, "temp_note.md")
    with open(temp_file_path, "w", encoding="utf-8") as temp_file:
        temp_file.writelines(filtered_lines)

    # Esegui la conversione sul file temporaneo
    NoteConversion(temp_file_path)

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
    matching_files_main = []
    matching_files_root = []
    # Ottieni i file corrispondenti all'argomento
    matching_files_main = get_all_files_from_main(custom)
    matching_files_root = get_all_files_from_root()
    
    if not custom:
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

def AddStartNewNote(note_path):
    """
    Aggiunge una nuova nota copiando il file void-notes.md e spostandolo nella posizione specificata.
    """
    # Percorso del file template
    template_path = os.path.join(SCRIPT_DIR, "templates", "void-notes.md")
    
    # Verifica che il file template esista
    if not os.path.exists(template_path):
        print(f"Errore: il file template '{template_path}' non esiste.")
        sys.exit(1)
    
    # Percorso completo della nuova nota
    new_note_path = Path(os.path.join("..", note_path)).resolve()
    
    # Verifica che non esista già una nota con lo stesso nome
    if os.path.exists(new_note_path):
        print(f"Errore: esiste già una nota con il nome '{note_path}'.")
        sys.exit(1)

    # Verifica che il macro-argomento esista
    macro_argomento_dir = Path(os.path.join("..", note_path.split("/")[0])).resolve()
    print(macro_argomento_dir)
    if not os.path.exists(macro_argomento_dir) or not os.path.isdir(macro_argomento_dir):
        print(f"Errore: il macro-argomento '{note_path.split('/')[0]}' non esiste. Crealo manualmente prima di aggiungere note.")
        sys.exit(1)
        
    # Verifica che il nome della nota sia valido
    note_name = os.path.basename(note_path)
    if not re.match(rf"^main\.{note_path.split('/')[0]}\..*\.md$", note_name):
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
        
    note_name = combined_note_path
    path_note = os.path.basename(note_name)
    
    # Comando per la conversione
    command = f"pandoc \"{path_note}\" -o \"{OUTPUT_PATH}\" --toc --toc-depth=3 --template=\"{TEMPLATE}\" --lua-filter=\"{LUA_FILTER}\" --listings --pdf-engine=xelatex"
    #command = f"pandoc \"{path_note}\" -o \"{OUTPUT_PATH}\" --template=\"{TEMPLATE}\" --lua-filter=\"{LUA_FILTER}\" --listings --pdf-engine=xelatex"
    
    # Esegui il comando
    print(f"Eseguo il comando: {command}")
    os.system(command)

## MAIN FUNCTION ##
def main():
    # Entro nella cartella build prima di eseguire il comando
    # Crea la directory di output se non esiste
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    os.chdir(MAKE_DIR)
    global custom
    
    # Creazione del parser
    parser = argparse.ArgumentParser(
        prog="make.py",
        description="Make script per gestire la conversione di note in PDF. Tips: genera un repo git vuoto e inserisci questo come un sottomodulo prima di lanciare un --init",
        epilog="Freeware Licence 2025 Fabio. Maintainer: BenettiFabio"
    )
    # Aggiunta delle opzioni
    parser.add_argument("-i", "--init",     action="store_true",                         help="Inizializza la struttura del vault in modo che sia consistente per il make.py")
    parser.add_argument("-a", "--all",                  metavar="OUTPUT",                help="Converte tutto il repository in un unico file di output, usando il main.md come ordinamento")
    parser.add_argument("-g", "--group",    nargs=2,    metavar=("ARGOMENTO", "OUTPUT"), help="Converte un macro-argomento specificato in un file di output, usando main.md come ordinamento")
    parser.add_argument("-n", "--note",     nargs=2,    metavar=("NOTA", "OUTPUT"),      help="Converte una nota specificata in un file di output")
    parser.add_argument("-s", "--start",                metavar="NOTE_PATH",             help="Aggiunge una nuova nota specificata in NOTE_PATH")
    parser.add_argument("-c", "--custom",               metavar="OUTPUT",                help="Converte tutte le note incluse nel file custom.md in un file di output")

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
        
    else:
        print("Errore: nessuna opzione valida selezionata.")
        parser.print_help()

if __name__ == "__main__":
    main()