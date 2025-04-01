#!/usr/bin/env python3
"""
Comprehensive cleanup script for the Reagent DB project
- Removes temporary and unnecessary files
- Organizes database utilities into a tools directory
- Cleans up pycache files
- Ensures correct directory structure
"""

import os
import shutil
import sys

# Files to be removed completely
FILES_TO_REMOVE = [
    '.DS_Store',              # macOS system file
    'check_tables.py',        # Temporary diagnostic script
    'test_query.py',          # Temporary diagnostic script
    'test_import.py',         # Testing script
    'cleanup_project.py',     # Simple cleanup script (replaced by this one)
]

# Python cache directories to clean
CACHE_DIRS = [
    '__pycache__',
]

# Files to move to a 'utils' directory
UTIL_FILES = [
    'clean_db.py',
    'import_from_csv.py',
    'import_template.py',
    'reset_db.py',
    'diagnostic.py',
    'debug_run.py',
    'view_logs.py',
]

def ensure_directory(path):
    """Ensure a directory exists, create if it doesn't"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    return path

def cleanup_project():
    """Remove unnecessary files and organize the project"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Track operations
    removed_files = []
    moved_files = []
    
    # 1. Ensure necessary directories exist
    utils_dir = ensure_directory(os.path.join(base_dir, 'utils'))
    ensure_directory(os.path.join(base_dir, 'exports'))
    ensure_directory(os.path.join(base_dir, 'uploads'))
    ensure_directory(os.path.join(base_dir, 'logs'))
    
    # 2. Remove specific files
    for file_name in FILES_TO_REMOVE:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # 3. Move utility files to utils directory
    for file_name in UTIL_FILES:
        source_path = os.path.join(base_dir, file_name)
        dest_path = os.path.join(utils_dir, file_name)
        
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, dest_path)
                os.remove(source_path)
                moved_files.append((source_path, dest_path))
                print(f"Moved: {source_path} -> {dest_path}")
            except Exception as e:
                print(f"Error moving {file_name}: {e}")
    
    # 4. Clean Python cache directories
    for root, dirs, files in os.walk(base_dir):
        for dir_name in list(dirs):
            if dir_name in CACHE_DIRS:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Cleaned cache directory: {dir_path}")
                except Exception as e:
                    print(f"Error cleaning {dir_path}: {e}")
    
    # 5. Create a launcher script in the utils directory
    launcher_path = os.path.join(utils_dir, 'launch.py')
    with open(launcher_path, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Launcher script for Reagent Database utilities
"""
import os
import sys
import importlib.util
import subprocess

def run_script(script_name):
    """Run a Python script from the utils directory"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    
    if not os.path.exists(script_path):
        print(f"Error: Script {script_name} not found!")
        return False
    
    # Add parent directory to path to ensure imports work
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Execute the script
    print(f"Running {script_name}...")
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("script", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'main'):
            module.main()
        return True
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def show_menu():
    """Show menu of available utilities"""
    print("\\n===== REAGENT DATABASE UTILITIES =====\\n")
    print("1. Run application")
    print("2. Clean database (reset to empty)")
    print("3. Reset database (with sample data)")
    print("4. Import from CSV")
    print("5. Diagnostic tool")
    print("6. View logs")
    print("7. Debug mode")
    print("0. Exit")
    
    choice = input("\\nEnter your choice (0-7): ")
    
    if choice == '1':
        # Run the main application
        app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'run.py')
        subprocess.run([sys.executable, app_path])
    elif choice == '2':
        run_script('clean_db.py')
    elif choice == '3':
        run_script('reset_db.py')
    elif choice == '4':
        run_script('import_from_csv.py')
    elif choice == '5':
        run_script('diagnostic.py')
    elif choice == '6':
        run_script('view_logs.py')
    elif choice == '7':
        run_script('debug_run.py')
    elif choice == '0':
        print("Exiting...")
        return
    else:
        print("Invalid choice. Please try again.")
    
    # Show menu again
    input("\\nPress Enter to continue...")
    show_menu()

if __name__ == "__main__":
    show_menu()
''')
    print(f"Created launcher script: {launcher_path}")
    
    # 6. Update the README to reflect project cleanup
    readme_path = os.path.join(base_dir, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'a') as f:
            f.write('''

## Project Structure After Cleanup

The project has been reorganized for better maintainability:

- `app/` - Core application code
- `templates/` - HTML templates
- `exports/` - Export destination
- `uploads/` - Upload destination
- `logs/` - Application logs
- `utils/` - Utility scripts for maintenance
- `csv_templates/` - Templates for data import

## Utility Scripts

Maintenance utilities have been moved to the `utils/` directory:

- `utils/clean_db.py` - Reset the database to a clean, empty state
- `utils/reset_db.py` - Reset the database with sample data
- `utils/diagnostic.py` - Check database integrity
- `utils/import_from_csv.py` - Import data from CSV files
- `utils/view_logs.py` - View application logs
- `utils/debug_run.py` - Run the app in debug mode

You can access all utilities through the launcher:

```bash
python utils/launch.py
```

''')
        print(f"Updated README file: {readme_path}")
    
    return (removed_files, moved_files)

def main():
    """Run the cleanup process"""
    print("\n===== REAGENT DATABASE PROJECT CLEANUP =====\n")
    
    # Confirm with user
    print("This will reorganize the project by:")
    print("1. Removing unnecessary files")
    print("2. Moving utility scripts to a 'utils' directory")
    print("3. Cleaning Python cache files")
    print("4. Updating documentation")
    confirm = input("\nContinue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Cleanup cancelled")
        return
    
    # Run cleanup
    removed_files, moved_files = cleanup_project()
    
    # Report results
    print("\n===== CLEANUP RESULTS =====")
    print(f"- Removed {len(removed_files)} unnecessary files")
    print(f"- Moved {len(moved_files)} utility files to the utils directory")
    print("\nThe project has been successfully reorganized!")
    print("You can now use 'python utils/launch.py' to access all utilities.")

if __name__ == "__main__":
    main()
