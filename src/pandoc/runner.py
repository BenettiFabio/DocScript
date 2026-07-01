import os
import shutil
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

SUPPORTED_OUTPUT_EXTENSIONS = (".pdf", ".tex", ".docx", ".odt")
SUPPORTED_OUTPUT_EXTENSIONS_TEXT = ".pdf, .tex, .docx, or .odt."


def _run_logged_command(
    command: list[str],
    *,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Print the command before executing it and run it with the same options."""
    print("run the command:")
    if cwd:
        print(f"cwd: {cwd}")
    for item in command:
        print(f"  {item}")
    print()

    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


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
    to a destination using template and files passed.
    Write the document in dst path: vault/build/.
    Supports .pdf, .tex, .docx and .odt outputs.
    """

    out_path = safe_path(dst)
    output_ext = out_path.suffix.lower()

    if output_ext not in SUPPORTED_OUTPUT_EXTENSIONS:
        raise ValueError(
            f"Unsupported output extension '{out_path.suffix}'. "
            f"Use {SUPPORTED_OUTPUT_EXTENSIONS_TEXT}"
        )

    # Entrer the Build Directory
    os.chdir(d_b)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("conversion Started, wait please...")

    tex_path = out_path.with_suffix(".tex")

    try:
        if is_network_path():
            cmd = [
                "pandoc",
                str(normalize_unc_path(str(src))),
                "-o",
                str(normalize_unc_path(str(tex_path))),
                "--defaults",
                str(normalize_unc_path(str(pndo))),
                "--template",
                str(normalize_unc_path(str(tmpl))),
                "--lua-filter",
                str(normalize_unc_path(str(luaf))),
                "--resource-path",
                str(normalize_unc_path(d_v)),
                "--resource-path",
                str(normalize_unc_path(d_a)),
                "--resource-path",
                str(normalize_unc_path(d_b)),
            ]

            _run_logged_command(cmd)

            if output_ext == ".pdf":
                _run_logged_command(
                    ["latexmk", "-xelatex", tex_path.name],
                    cwd=str(tex_path.parent),
                )
                generated_pdf = tex_path.with_suffix(".pdf")
                if generated_pdf.exists() and generated_pdf != out_path:
                    shutil.copy2(generated_pdf, out_path)

            elif output_ext in {".docx", ".odt"}:
                _run_logged_command(
                    [
                        "pandoc",
                        str(normalize_unc_path(str(tex_path))),
                        "-o",
                        str(normalize_unc_path(str(out_path))),
                    ]
                )

            elif output_ext == ".tex" and tex_path != out_path:
                shutil.copy2(tex_path, out_path)

            # Clean the build dir
            folder = tex_path.parent
            filename = tex_path.stem  # es. 'file' from 'file.tex'
            allowed = {
                out_path.name,
                *[f"{filename}{ext}" for ext in SUPPORTED_OUTPUT_EXTENSIONS],
            }

            for item in folder.iterdir():
                if (
                    item.is_file()
                    and item.name.startswith(filename)
                    and item.name not in allowed
                ):
                    print(f"remove: {item}")
                    item.unlink()  # Delete the file

        else:
            cmd = [
                "pandoc",
                str(normalize_unc_path(str(src))),
                "-o",
                str(normalize_unc_path(str(out_path))),
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

            if output_ext == ".pdf":
                cmd.insert(2, "--pdf-engine=xelatex")

            _run_logged_command(cmd)

    except subprocess.CalledProcessError as e:
        print("STDOUT:")
        print(e.stdout)

        print("STDERR:")
        print(e.stderr)

        raise
