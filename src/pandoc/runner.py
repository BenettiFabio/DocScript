import os
import sys
from pathlib import Path

###############
# Description #
###############
"""
The contents of this file are all the functions
that describe the behavior of pandoc env
"""


def check_precondition() -> None:
    """
    Verify if the system meets the necessary prerequisites for conversion.
    Check whether xelatex and pandoc are installed and available in your PATH.
    """

    if sys.platform.startswith("win"):
        if os.system("where xelatex >nul 2>nul") != 0:
            print("Errore: xelatex non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("xelatex installato.")

    if sys.platform.startswith("linux"):
        if os.system("which xelatex > /dev/null") != 0:
            print("Errore: xelatex non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("xelatex installato.")

    if sys.platform.startswith("win"):
        if os.system("where pandoc >nul 2>nul") != 0:
            print("Errore: pandoc non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("pandoc installato.")

    if sys.platform.startswith("linux"):
        if os.system("which pandoc > /dev/null") != 0:
            print("Errore: pandoc non installato o non nel PATH.")
            sys.exit(1)
        else:
            print("pandoc installato.")

    if sys.platform.startswith("win"):
        if (
            os.system('fc-list | findstr /i "FreeSerif FreeSans FreeMono" >nul 2>nul')
            != 0
        ):
            print("Errore: i font GNU FreeFonts non sono installati.")
            sys.exit(1)
        else:
            print("Font GNU FreeFonts installati.")

    if sys.platform.startswith("linux"):
        if os.system("locate Free .ttf | grep /usr/share/fonts/TTF/ > /dev/null") != 0:
            print(
                "Errore: i font GNU FreeFonts non "
                "sono installati in /usr/share/fonts/TTF ."
            )
            sys.exit(1)
        else:
            print("Font GNU FreeFonts installati.")


def execute_pandoc(
    tmpl: str | None, luaf: str | None, pndo: str | None, src: Path, dst: Path
) -> None:
    """
    Convert che src path: vault/build/combined_notes.md,
    to a destination using template and files passed
    Write the document in dst path: vault/build/s
    """
    print("conversion started")
    print(f"execute dst = {dst}")
    print(f"execute src = {src}")
    print(f"execute tmpl= {tmpl}")  # todo : ricorda di valutare i casi None
    print(f"execute luaf= {luaf}")
    print(f"execute pndo= {pndo}")

    # if is_bank:
    #     print("is bank, ricoda di copiare i file dentro la cartella decuments")
    # else:
    #     # Converto normalmente nella cartella di build in
    #     # quanto ho giá tutto in locale

    #     template = safe_path(TEMPLATE_PATH)
    #     if cfgCstmPath.custom_teml_path:
    #         template = cfgCstmPath.custom_teml_path

    #     lua_filter = safe_path(LUA_FILTER_PATH)
    #     if cfgCstmPath.custom_luaf_path:
    #         lua_filter = cfgCstmPath.custom_luaf_path

    #     default_opt = safe_path(PANDOC_OPT_PATH)
    #     if cfgCstmPath.custom_pandoc_opt_path:
    #         default_opt = cfgCstmPath.custom_pandoc_opt_path

    # if isNetworkPath():
    #     # Eseguo prima la conversione in tex con pandoc
    #     dst = out_pdstadstth.with_suffix(".tex")

    #     command = f'pandoc "{src}" -o "{dst}" --defaults="{default_opt}"
    #               --template="{template}" --lua-filter="{lua_filter}"
    #               --pdf-engine=xelatex'

    #     print(f"Eseguo il comando: {command}")
    #     os.system(command)

    #     # Eseguo poi la conversione in pdf con latexmk
    #     subprocess.run(
    #         ["latexmk", "-xelatex", dst.name], cwd=dst.parent, shell=True
    #     )

    #     # Pulizia della cartella di build
    #     folder = dst.parent
    #     filename = dst.stem  # es. 'file' da 'file.pdf'
    #     allowed = {f"{filename}.pdf", f"{filename}.tex"}

    #     for item in folder.iterdir():
    #         if (
    #             item.is_file()
    #             and item.name.startswith(filename)
    #             and item.name not in allowed
    #         ):
    #             print(f"Rimuovo: {item}")
    #             item.unlink()  # Cancella il file

    # else:
    #     # Comando per la conversione pulita con pandoc
    #     command = f'pandoc "{src}" -o "{dst}" --defaults="{default_opt}"
    #     --template="{template}" --lua-filter="{lua_filter}"
    #     --pdf-engine=xelatex'

    #     # Esegui il comando
    #     print(f"Eseguo il comando: {command}")
    #     os.system(command)
