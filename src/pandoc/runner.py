import os
import subprocess
import sys
from pathlib import Path

from src.utils import (
    is_network_path,
    normalize_unc_path,
    safe_path,
)

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
            print("Error: xelatex not installed or not in PATH.")
            sys.exit(1)
        else:
            print("xelatex installed.")

    if sys.platform.startswith("linux"):
        if os.system("which xelatex > /dev/null") != 0:
            print("Error: xelatex not installed or not in PATH.")
            sys.exit(1)
        else:
            print("xelatex installed.")

    if sys.platform.startswith("win"):
        if os.system("where pandoc >nul 2>nul") != 0:
            print("Error: pandoc not installed or not in PATH.")
            sys.exit(1)
        else:
            print("pandoc installed.")

    if sys.platform.startswith("linux"):
        if os.system("which pandoc > /dev/null") != 0:
            print("Error: pandoc not installed or not in PATH.")
            sys.exit(1)
        else:
            print("pandoc installed.")

    if sys.platform.startswith("win"):
        if (
            os.system(
                'fc-list | findstr /i "FreeSerif FreeSans FreeMono" >nul 2>nul')
            != 0
        ):
            print("Error: GNU FreeFonts not installed.")
            sys.exit(1)
        else:
            print("GNU FreeFonts installed.")

    if sys.platform.startswith("linux"):
        if os.system("locate Free .ttf | grep /usr/share/fonts/TTF/ > /dev/null") != 0:
            print(
                "Error: GNU FreeFonts not installed "
                "in /usr/share/fonts/TTF ."
            )
            sys.exit(1)
        else:
            print("GNU FreeFonts installed.")


def execute_pandoc(
    tmpl: str,
    luaf: str,
    pndo: str,
    src: Path,
    dst: Path,
    d_v: str,  # dir vault
    d_a: str,  # dir assets
    d_b: str,  # dir build finale
) -> None:
    """
    Convert the src path: vault/build/combined_notes.md,
    to a destination using template and files passed
    Write the document in dst path: vault/build/
    """

    # Entrer the Build Directory
    os.chdir(d_b)

    print("conversion Started, wait please...")

    if is_network_path():
        # Run the first Tex converson with pandoc
        tex_path = safe_path(dst).with_suffix(".tex")

        command = (
            f'pandoc "{str(normalize_unc_path(str(src)))}"'
            f' -o "{str(normalize_unc_path(str(tex_path)))}"'
            f' --defaults="{str(normalize_unc_path(str(pndo)))}"'
            f' --template="{str(normalize_unc_path(str(tmpl)))}"'
            f' --lua-filter="{str(normalize_unc_path(str(luaf)))}"'
        )

        print(f"run the command: {command}")
        os.system(command)

        # Run the second conversion in pdf with latexmk
        subprocess.run(
            ["latexmk", "-xelatex", tex_path.name],
            cwd=tex_path.parent,  # the dir of the .tex
            # shell=True
            check=True,  # optional: rise CalledProcessError if command fails
        )

        # Clean the build dir
        folder = tex_path.parent
        filename = tex_path.stem  # es. 'file' from 'file.tex'
        allowed = {f"{filename}.pdf", f"{filename}.tex"}

        for item in folder.iterdir():
            if (
                item.is_file()
                and item.name.startswith(filename)
                and item.name not in allowed
            ):
                print(f"remove: {item}")
                item.unlink()  # Delete the file

    else:
        # Clean conversion with pandoc
        try:
            cmd = [
                "pandoc",
                str(normalize_unc_path(str(src))),
                "--pdf-engine=xelatex",
                "-o",
                str(normalize_unc_path(str(dst))),
                "--template",
                str(normalize_unc_path(str(tmpl))),
                "--lua-filter",
                str(normalize_unc_path(str(luaf))),
                "--defaults",
                str(normalize_unc_path(str(pndo))),
                "--resource-path",
                str(normalize_unc_path(d_v)),
                "--resource-path",
                str(normalize_unc_path(d_a)),
                "--resource-path",
                str(normalize_unc_path(d_b)),
            ]

            print("run the command: \n")
            cmd_str = " ".join(cmd)
            print(cmd_str)

            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )

        except subprocess.CalledProcessError as e:
            print("STDOUT:")
            print(e.stdout)

            print("STDERR:")
            print(e.stderr)

            raise
