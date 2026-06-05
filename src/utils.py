import os
import re
import shutil
import stat
import subprocess
import textwrap
import time
from collections.abc import Callable
from pathlib import Path

###############
# Description #
###############
"""
Generic all-rounded function
"""


def is_network_path() -> bool:
    """
    It understands whether it is in a shared folder on a network path or a local folder
    in Windows. For Linux this distinction is irrelevant.
    """

    is_windows = os.name == "nt"

    # ====== WIN ======
    if is_windows:
        here = os.getcwd()
        return here.startswith("\\\\") or not here.startswith("C:")

    # ====== UNIX ======
    return False


def normalize_unc_path(windowsPath: str) -> str:
    """
    Convert a UNC Windows path with backslash (\\\\server\\share\\path)
    in a compatible path with external instruments like pandoc (//server/share/path).
    """

    windows_path = windowsPath

    # Read all the network disk drive into the system
    result = subprocess.run(
        "net use", capture_output=True, text=True, shell=True)
    lines = result.stdout.splitlines()
    mapped_drives = {}

    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].endswith(":") and parts[1].startswith("\\\\"):
            drive_letter = parts[0]
            unc_path = parts[1]
            mapped_drives[drive_letter] = unc_path

    # Normalize the path preserving the original casing for the returned path.
    normalized_path = Path(windows_path).resolve().as_posix()
    path_parts = normalized_path.strip("/").split("/")
    path_parts_lower = [part.lower() for part in path_parts]

    # Try to change the entry point with the founded letter if match.
    # Compare case-insensitively, but rebuild the returned path using the
    # original casing already present in the input path.
    for drive, unc in sorted(
        mapped_drives.items(), key=lambda x: len(x[1]), reverse=True
    ):
        unc_norm = unc.replace("\\", "/")
        unc_parts = unc_norm.strip("/").split("/")

        try:
            idx = path_parts_lower.index(unc_parts[-1].lower())

            # Build the path starting from the first folder found.
            relative_parts = path_parts[idx + 1:]
            final_path = Path(drive + "/") / Path(*relative_parts)

            return str(final_path).replace("\\", "/")
        except ValueError:
            continue  # The final folder is not in the full path, try the next one
    # If not found it would still fail, I return the original path
    return windows_path  # bypass


def to_unix_path(rawPath: str) -> str:
    """
    Converts a path from Windows/UNC to a valid POSIX path.

    If the path is already POSIX (starts with '/' or is relative),
    it returns it unchanged.

    • Backslash → slash
    • Removes any '\\\\?\\' or '\\\\' (UNC) prefixes.
    • If the path contains a drive letter (e.g., 'C:\\folder'),
    it changes to '/c/folder' (lowercase) – only
    when running on Linux.
    """

    raw_path = rawPath

    is_windows = os.name == "nt"

    # Remove extra prefix
    if raw_path.startswith("\\\\?\\"):
        raw_path = raw_path[4:]  # remove '\\?\'

    # ====== WIN ======
    if is_windows:
        # If starts with \\ it is an UNC path → network
        if raw_path.startswith("\\\\"):
            return normalize_unc_path(raw_path)
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


def safe_path(*parts: str | Path) -> Path:
    """
    Built and convert a path from an UNC/slash path
    - if 1 param: apply a simple conversion on the Path/str already built
    - if N params: create a path with os.path.join, resolve, and at least convert
    """

    if len(parts) == 1:
        p = parts[0]
        # string or other: normalize
        return Path(to_unix_path(str(p)))

    # more than one components → join, then normalize
    joined = os.path.join(*parts)
    return Path(to_unix_path(joined))


def remove_dir(target: Path, retries: int = 3, delay: float = 1.0) -> None:
    """
    Removes a directory tree, retrying on failure (e.g. Windows locks).
    Forces read-only files to be writable before deletion.
    """

    def _force_write(func: Callable[..., None], path: str, _exc: object) -> None:
        os.chmod(path, stat.S_IWRITE)
        func(path)

    for attempt in range(retries):
        try:
            shutil.rmtree(target, onerror=_force_write)
            return
        except Exception as exc:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"Warning: impossibile remove '{target}': {exc}")


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
        raise FileNotFoundError(f"Error: The directory {src}, does not exist")

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
    """
    Write the specified file name with a content passed
    """
    fileName = str(fileName)
    content = textwrap.dedent(content)

    with open(fileName, "w") as f:
        f.write(content)


def should_skip_dir(dirPath: str, BLACKLIST: list[str]) -> bool:
    """
    Check if specified dir need to be excluded from a dirs scan
    """
    dir_path = str(dirPath)
    return dir_path in BLACKLIST


def should_skip_file(filePath: str, BLACKLIST: list[str]) -> bool:
    """
    Check if specified file need to be excluded from a files scan
    """
    file_name = os.path.basename(filePath)
    return file_name in BLACKLIST


def convert_link_to_absolute(markdownText: str, base_path: str) -> str:
    """
    Convert relative Markdown links in `markdownText` to absolute paths
    based on `base_path` and return the transformed line.
    """
    base_dir = Path(base_path).parent.resolve()

    def replacer(match: re.Match[str]) -> str:
        label = match.group(1)
        rel_path = match.group(2)
        abs_path = (base_dir / rel_path).resolve()
        return f"[{label}]({abs_path})"

    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    return pattern.sub(replacer, markdownText).replace("\\", "/")
