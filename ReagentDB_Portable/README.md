# Portable Experimental Results Sharing Tool

This is a portable version of the Experimental Results Sharing Tool that can store its database on OneDrive for easy synchronization across different devices.

## Creating a Portable Package

To create a fully portable package that you can copy anywhere:

1. On Windows: Run `make_portable.bat`
2. On macOS/Linux: Run `./make_portable.sh`

This will create a `ReagentDB_Portable` folder in the parent directory that contains everything needed to run the application from any location.

## Setup and Usage

### Storing Database on OneDrive

The application is configured to automatically detect your OneDrive folder and store the database there. This allows you to:

1. Access the same database from multiple computers
2. Keep your data backed up automatically
3. Share the database with colleagues (if you use a shared OneDrive folder)

The database will be stored in a folder called `ReagentDB` in your OneDrive.

### Running the Application

#### On Windows:
Double-click the `run_portable.bat` file. This will:
- Check if Python is installed
- Install required dependencies
- Start the application

#### On macOS or Linux:
1. Open Terminal
2. Navigate to the application directory
3. Make the script executable (if needed): `chmod +x run_portable.sh`
4. Run the script: `./run_portable.sh`

### First Run

On the first run, the application will:
1. Create the `ReagentDB` folder in your OneDrive if it doesn't exist
2. Initialize a new database if one doesn't exist
3. Start the web interface

### Accessing the Application

Once running, open your web browser and go to:
```
http://localhost:5000
```

## Troubleshooting

### OneDrive Not Detected

If your OneDrive location is not automatically detected:

1. Open the `app_config.json` file
2. Set the `onedrive_path` value to your OneDrive folder path:
   - Windows example: `C:\\Users\\YourUsername\\OneDrive`
   - macOS example: `/Users/YourUsername/Library/CloudStorage/OneDrive-Personal`
   - Linux example: `/home/YourUsername/OneDrive`

### Database Not Syncing

1. Ensure OneDrive is properly set up and syncing on your computer
2. Check if the `ReagentDB` folder exists in your OneDrive
3. Verify that the `use_onedrive` setting is set to `true` in `app_config.json`
