import os
import shutil
import sys


def setup_hooks():
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the source of hook files (the 'hooks' folder inside 'dev/')
    hooks_source_dir = os.path.join(current_script_dir, "hooks")

    # dev/ -> requirements/ -> DocScript/ -> MyDocumentation/
    requirements_dir = os.path.dirname(current_script_dir)
    submodule_root_dir = os.path.dirname(requirements_dir)
    main_project_dir = os.path.dirname(submodule_root_dir)

    # Define the destination path inside the main project's .git
    git_hooks_dest = os.path.join(
        main_project_dir, ".git", "modules", "DocScript", "hooks"
    )

    print("--- Git Hooks configuration for DocScript submodule ---")
    print(f"Hooks source: {hooks_source_dir}")
    print(f"Git destination: {git_hooks_dest}\n")

    # Verify that the source 'hooks/' folder exists
    if not os.path.exists(hooks_source_dir):
        print(f"Error: Hooks source folder not found at:\n   {hooks_source_dir}")
        sys.exit(1)

    # Verify that the Git destination folder exists
    if not os.path.exists(git_hooks_dest):
        print(f"Error: Git destination folder not found at:\n   {git_hooks_dest}")
        print("Ensure the submodule is initialized in the main project.")
        sys.exit(1)

    # Find all files in the source hooks/ folder
    hooks_to_install = [
        f
        for f in os.listdir(hooks_source_dir)
        if os.path.isfile(os.path.join(hooks_source_dir, f))
    ]

    if not hooks_to_install:
        print("No hook files found to install in the source folder.")
        sys.exit(0)

    # Copy files and set permissions
    for hook_name in hooks_to_install:
        source_path = os.path.join(hooks_source_dir, hook_name)
        dest_path = os.path.join(git_hooks_dest, hook_name)

        try:
            # Copy the file, overwriting previous versions
            shutil.copy2(source_path, dest_path)
            print(f"Copied: {hook_name}")

            # On Unix systems (Linux/macOS), Git requires hooks to be executable
            if os.name != "nt":
                current_permissions = os.stat(dest_path).st_mode
                os.chmod(dest_path, current_permissions | 0o111)
                print(f"   -> Execution permissions set for {hook_name}")

        except Exception as e:
            print(f"Error copying {hook_name}: {e}")

    print("\nSetup complete! Submodule hooks are ready.")


if __name__ == "__main__":
    setup_hooks()
