import os
import shutil
import subprocess
import textwrap
from pathlib import Path

###############
# Description #
###############
"""
Generic all-rounded function
"""


def to_unc_slash_path(windows_path: str) -> str:
    """
    Convert a UNC Windows path with backslash (\\\\server\\share\\path)
    in a compatible path with external instruments like pandoc (//server/share/path).
    """

    # If start with \\ it is an UNC path -> network path
    if windows_path.startswith("\\\\"):

        # Remove (if exists) the prefix \\?\ (that may be used in long Windows path)
        path_str = windows_path.replace("\\\\?\\", "")

        # Read all the network drive in the system
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

        # Fix the path
        full_path = str(Path(path_str).resolve())
        normalized_path = full_path.replace("\\", "/")

        # Try to replace the drive letter (e.g. G:/) if matches
        for drive, unc in sorted(
            mapped_drives.items(), key=lambda x: len(x[1]), reverse=True
        ):
            unc_norm = unc.replace("\\", "/")
            unc_parts = unc_norm.strip("/").split("/")
            full_parts = normalized_path.strip("/").split("/")

            try:
                # Find the first shared drive
                idx = full_parts.index(unc_parts[-1])

                # Build the path starting of the first directory found
                relative_parts = full_parts[idx + 1 :]
                resolved_drive_path = Path(drive + "/") / Path(*relative_parts)
                return str(resolved_drive_path).replace("\\", "/")

            except ValueError:
                continue  # The final dir is not in the complete path

        # If does not exists, return the original path
        return windows_path  # bypass
    return windows_path


def safe_path(*args: str | Path) -> Path:
    """
    Built and convert a path from an UNC/slash path
    - if 1 param: apply a simple conversion on the Path/str already built
    - if N params: create a path with os.path.join, resolve, and at least convert
    """
    # Direct conversion
    if len(args) == 1:
        return Path(to_unc_slash_path(str(args[0])))

    # join - resolve - convert
    joined_path = os.path.join(*(str(a) for a in args))
    resolved_path = Path(joined_path).resolve()
    return Path(to_unc_slash_path(str(resolved_path)))


def copy_dir_recursive(src: str | Path, dst: str | Path) -> None:
    """
    Recursively copies the contents of a `src` directory to `dst`,
    preserving the structure and copying only files that differ
    in size or timestamp.

    Args:
        src (str): source directory path
        dst (str): destination directory path (create if does not exists)
    """
    src = str(src)
    dst = str(dst)
    if not os.path.exists(src):
        raise FileNotFoundError(f"La directory sorgente non esiste: {src}")

    for root, _, files in os.walk(src):
        relative_path = os.path.relpath(root, src)
        target_dir = os.path.join(dst, relative_path)
        os.makedirs(target_dir, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_dir, file)

            # If the destination file exists, check dimension and timestamp
            if os.path.exists(dest_file):
                src_stat = os.stat(src_file)
                dst_stat = os.stat(dest_file)

                same_size = src_stat.st_size == dst_stat.st_size
                same_mtime = int(src_stat.st_mtime) == int(dst_stat.st_mtime)

                if same_size and same_mtime:
                    # File identico -> salta copia
                    continue

            # Copy file and metadatas
            shutil.copy2(src_file, dest_file)


def write_file(fileName: str | Path, content: str) -> None:
    fileName = str(fileName)
    content = textwrap.dedent(content)

    with open(fileName, "w") as f:
        f.write(content)
