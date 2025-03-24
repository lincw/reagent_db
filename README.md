# Reagent Database Application

A comprehensive tool for managing laboratory reagents, ORFs, plasmids, and more.

## Directory Structure

This application is organized into several components:

- **Main Application**: The core files for the application
  - `app/`: Core application code
  - `templates/`: HTML templates
  - `config.py`: Configuration settings
  - `run.py`: Main application launcher

- **Portable Version** (`/portable`): Files to create a portable version that stores data on OneDrive
  - Creates a version that can be used across multiple computers with the database in cloud storage

- **Demo Creator** (`/demo_maker`): Tools to create a self-contained demo with sample data
  - Perfect for sharing with colleagues who want to see the application in action

## Running the Application

### Normal Mode
```
python run.py
```

### Creating a Portable Version
1. Go to the `portable` folder
2. Run `make_portable.bat` (Windows) or `./make_portable.sh` (macOS/Linux)

### Creating a Demo Version to Share
1. Go to the `demo_maker` folder
2. Run `create_demo_package.bat` (Windows) or `./create_demo_package.sh` (macOS/Linux)
3. Share the resulting `ReagentDB_Demo` folder with colleagues

## Features

- Search and filter reagents by various criteria
- View detailed information about ORFs, plasmids, freezers, and organisms
- Navigate between related items using clickable links
- Import and export data
- Configure storage location (local or cloud-based)
