"""
Script to run a specific migration on the database
"""

import sys
import importlib.util
import os

def run_migration(migration_name):
    if not migration_name:
        print("Error: Please specify a migration name")
        print("Usage: python run_migration.py <migration_name>")
        print("Available migrations:")
        list_migrations()
        return False
    
    # Check if the migration exists
    migration_path = os.path.join('migrations', f'{migration_name}.py')
    if not os.path.exists(migration_path):
        print(f"Error: Migration '{migration_name}' not found")
        print("Available migrations:")
        list_migrations()
        return False
    
    # Import the migration module
    spec = importlib.util.spec_from_file_location(migration_name, migration_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    # Run the migration
    if hasattr(migration_module, 'migrate'):
        print(f"Running migration: {migration_name}")
        success = migration_module.migrate()
        if success:
            print(f"Migration '{migration_name}' completed successfully")
            return True
        else:
            print(f"Migration '{migration_name}' failed")
            return False
    else:
        print(f"Error: Migration '{migration_name}' does not have a migrate() function")
        return False

def list_migrations():
    # List all Python files in the migrations directory
    migration_dir = 'migrations'
    if not os.path.exists(migration_dir):
        print("No migrations directory found")
        return
    
    migrations = []
    for filename in os.listdir(migration_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            migrations.append(os.path.splitext(filename)[0])
    
    if not migrations:
        print("No migrations found")
        return
    
    for migration in sorted(migrations):
        print(f"  - {migration}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please specify a migration name")
        print("Usage: python run_migration.py <migration_name>")
        print("Available migrations:")
        list_migrations()
        sys.exit(1)
    
    migration_name = sys.argv[1]
    success = run_migration(migration_name)
    sys.exit(0 if success else 1)
