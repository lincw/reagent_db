# Creating a Demonstration Package

This folder contains scripts to create a fully portable demonstration package of the Reagent Database application.

## What is the Demo Package?

The demo package is:
- A **self-contained** version of the application
- Includes **sample data** for demonstration
- Requires **only Python** to run (no database server needed)
- Can be shared with colleagues who can run it on their own computers
- Includes simple launch scripts for Windows and macOS/Linux

## Creating the Demo Package

### On Windows:
1. Double-click `create_demo_package.bat`
2. Wait for the process to complete
3. Look for the `ReagentDB_Demo` folder in the parent directory

### On macOS or Linux:
1. Open Terminal in this directory
2. Run: `chmod +x create_demo_package.sh` (to make the script executable)
3. Run: `./create_demo_package.sh`
4. Look for the `ReagentDB_Demo` folder in the parent directory

## Sharing the Demo

To share the demo with colleagues:
1. Zip the entire `ReagentDB_Demo` folder
2. Share the zip file
3. Tell colleagues to extract the zip and follow the instructions in the README file

## Demo Package Contents

The demo package includes:
- All application code
- Sample database with pre-populated data
- Launch scripts for different operating systems
- Detailed README with usage instructions

## Requirements for Running the Demo

Recipients of the demo package will need:
- Python 3.6 or higher installed
- Basic knowledge of running batch files (Windows) or shell scripts (macOS/Linux)
- About 50MB of disk space
