#!/usr/bin/env python3
"""
Clean up the Reagent DB project by removing temporary and unnecessary files
"""

import os
import shutil
import sys

# Files to be removed
FILES_TO_REMOVE = [
    '.DS_Store',              # macOS system file
    'check_tables.py',        # Temporary diagnostic script
    'test_query.py',          # Temporary diagnostic script
    'test_import.py',         # Testing script
]

# Temporary directories to clean (but not remove)
DIRS_TO_CLEAN = [
    '__pycache__',            # Python cache files
]

def cleanup_project():
    """Remove temporary and unnecessary files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Keep track of what was removed
    removed_files = []
    
    # Remove specific files
    for file_name in FILES_TO_REMOVE:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # Clean pycache directories
    for root, dirs, files in os.walk(base_dir):
        for dir_name in dirs:
            if dir_name in DIRS_TO_CLEAN:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Cleaned directory: {dir_path}")
                except Exception as e:
                    print(f"Error cleaning {dir_path}: {e}")
    
    return removed_files

def main():
    """Run the cleanup process"""
    print("\n===== PROJECT CLEANUP =====\n")
    
    # Confirm with user
    print("This will remove temporary and unnecessary files from the project.")
    confirm = input("Continue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Cleanup cancelled")
        return
    
    # Run cleanup
    removed_files = cleanup_project()
    
    if removed_files:
        print(f"\nSuccessfully removed {len(removed_files)} unnecessary files!")
    else:
        print("\nNo files were removed.")

if __name__ == "__main__":
    main()
