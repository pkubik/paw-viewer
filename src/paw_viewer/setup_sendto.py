"""Setup script to create a Windows SendTo shortcut for paw.exe."""

import os
import sys
from pathlib import Path


def setup_sendto():
    """Create a shortcut to paw.exe in the Windows SendTo directory."""
    if sys.platform != "win32":
        print("This script is only for Windows systems.")
        return 1

    try:
        import win32com.client
    except ImportError:
        print("Error: pywin32 is required for creating shortcuts.")
        print("Install it with: pip install pywin32")
        return 1

    # Find the paw.exe location
    # The executable should be in the same directory as python.exe or in Scripts/
    python_dir = Path(sys.executable).parent
    paw_exe = python_dir / "Scripts" / "paw.exe"
    
    if not paw_exe.exists():
        # Try alternate location (direct in python dir)
        paw_exe = python_dir / "paw.exe"
    
    if not paw_exe.exists():
        print(f"Error: Could not find paw.exe")
        print(f"Searched in: {python_dir / 'Scripts' / 'paw.exe'}")
        print(f"        and: {python_dir / 'paw.exe'}")
        return 1

    # Get the SendTo directory
    sendto_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "SendTo"
    
    if not sendto_dir.exists():
        print(f"Error: SendTo directory not found: {sendto_dir}")
        return 1

    # Create the shortcut
    shortcut_path = sendto_dir / "Paw Viewer.lnk"
    
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = str(paw_exe)
        shortcut.WorkingDirectory = str(paw_exe.parent)
        shortcut.IconLocation = str(paw_exe)
        shortcut.Description = "Paw Viewer"
        shortcut.save()
        
        print(f"✓ Successfully created SendTo shortcut at: {shortcut_path}")
        print(f"  Target: {paw_exe}")
        print("\nYou can now right-click files and select 'Send to > Paw Viewer'")
        return 0
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return 1


def main():
    """Entry point for the setup script."""
    sys.exit(setup_sendto())


if __name__ == "__main__":
    main()
