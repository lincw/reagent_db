#!/usr/bin/env python3
"""
Script to create a portable package of the Reagent Database application
that can be moved to any location and run from there.
"""

import os
import sys
import shutil
import platform
from pathlib import Path

def create_portable_package():
    # Get the base directory of the application
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Create a portable directory
    portable_dir = os.path.join(base_dir, "ReagentDB_Portable")
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)
    
    # Files and directories to copy
    to_copy = [
        "app",
        "templates",
        "config.py",
        "run.py",
        "setup_db.py"
    ]
    
    # Copy necessary files
    for item in to_copy:
        src = os.path.join(base_dir, item)
        dst = os.path.join(portable_dir, item)
        
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    
    # Create empty directories
    for directory in ["uploads", "exports"]:
        os.makedirs(os.path.join(portable_dir, directory), exist_ok=True)
    
    # Copy portable launcher scripts
    shutil.copy2(os.path.join(script_dir, "run_portable.bat"), portable_dir)
    shutil.copy2(os.path.join(script_dir, "run_portable.sh"), portable_dir)
    
    # Make the shell script executable
    os.chmod(os.path.join(portable_dir, "run_portable.sh"), 0o755)
    
    # Copy README and requirements
    shutil.copy2(os.path.join(script_dir, "README.md"), portable_dir)
    shutil.copy2(os.path.join(script_dir, "requirements.txt"), portable_dir)
    
    # Create app_config.json with OneDrive enabled
    config_content = '''{
    "db_path": "reagent_db.sqlite",
    "use_onedrive": true,
    "onedrive_path": "",
    "debug": true,
    "port": 5000
}'''
    with open(os.path.join(portable_dir, "app_config.json"), 'w') as f:
        f.write(config_content)
    
    # Create a quick start guide
    create_quickstart_guide(portable_dir)
    
    print(f"Portable package created at: {portable_dir}")
    print("You can now copy this folder to any location, including external drives or cloud storage.")
    print("To run the application, use run_portable.bat (Windows) or run_portable.sh (macOS/Linux).")

def create_quickstart_guide(portable_dir):
    quickstart = '''# ReagentDB Portable Quick Start Guide

## Running the Application

### On Windows:
Double-click `run_portable.bat`

### On macOS or Linux:
Open Terminal in this directory and run:
```
./run_portable.sh
```

## Accessing the Application
Once running, open your web browser and go to:
```
http://localhost:5000
```

## Database Location
The database will be stored in your OneDrive folder under `ReagentDB/reagent_db.sqlite`
'''
    with open(os.path.join(portable_dir, "QUICKSTART.md"), 'w') as f:
        f.write(quickstart)

if __name__ == "__main__":
    create_portable_package()
