import os
import sys

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
