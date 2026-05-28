import os
import shutil
import sys


def setup_hooks():
    # 1. Trova la cartella dove risiede questo script Python (DocScript/requirements/dev/)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Definisci la sorgente dei file di hook (la cartella 'hooks' che sta dentro 'dev/')
    hooks_source_dir = os.path.join(current_script_dir, 'hooks')

    # 3. Risali l'alberatura per trovare il Progetto Principale (MyDocumentation)
    # dev/ -> requirements/ -> DocScript/ -> MyDocumentation/
    requirements_dir = os.path.dirname(current_script_dir)
    submodule_root_dir = os.path.dirname(requirements_dir)
    main_project_dir = os.path.dirname(submodule_root_dir)

    # 4. Definisci il percorso di destinazione dentro il .git del progetto principale
    git_hooks_dest = os.path.join(
        main_project_dir, '.git', 'modules', 'DocScript', 'hooks')

    print(f"--- Configurazione Git Hooks per il sottomodulo DocScript ---")
    print(f"Sorgente hook: {hooks_source_dir}")
    print(f"Destinazione Git: {git_hooks_dest}\n")

    # Verifica che la cartella sorgente 'hooks/' esista
    if not os.path.exists(hooks_source_dir):
        print(
            f"Errore: Non ho trovato la cartella sorgente degli hook in:\n   {hooks_source_dir}")
        sys.exit(1)

    # Verifica che la cartella Git di destinazione esista
    if not os.path.exists(git_hooks_dest):
        print(
            f"Errore: Non ho trovato la cartella Git di destinazione in:\n   {git_hooks_dest}")
        print("Assicurati che il sottomodulo sia inizializzato nel progetto principale.")
        sys.exit(1)

    # 5. Trova tutti i file nella cartella sorgente hooks/
    hooks_to_install = [f for f in os.listdir(
        hooks_source_dir) if os.path.isfile(os.path.join(hooks_source_dir, f))]

    if not hooks_to_install:
        print("Nessun file di hook trovato da installare nella cartella sorgente.")
        sys.exit(0)

    # 6. Copia i file e imposta i permessi
    for hook_name in hooks_to_install:
        source_path = os.path.join(hooks_source_dir, hook_name)
        dest_path = os.path.join(git_hooks_dest, hook_name)

        try:
            # Copia il file sovrascrivendo eventuali versioni precedenti
            shutil.copy2(source_path, dest_path)
            print(f"Copiato: {hook_name}")

            # Su sistemi Unix (Linux/macOS), Git richiede che gli hook siano eseguibili
            if os.name != 'nt':
                current_permissions = os.stat(dest_path).st_mode
                os.chmod(dest_path, current_permissions | 0o111)
                print(
                    f"   -> Permessi di esecuzione impostati per {hook_name}")

        except Exception as e:
            print(f"Errore durante la copia di {hook_name}: {e}")

    print("\nSetup completato! Gli hook del sottomodulo sono pronti.")


if __name__ == "__main__":
    setup_hooks()
