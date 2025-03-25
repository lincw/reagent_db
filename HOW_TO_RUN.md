# How to Run the Reagent Database Application

This is a simplified guide to running the Reagent Database application after cleanup.

## Step 1: Clean Up the Project (One-time operation)

To remove all unnecessary files and get a clean project structure:

```bash
python cleanup_all.py
```

This will remove redundant scripts, demo files, and clean up the project structure.

## Step 2: Run the Application

To start the Reagent Database application:

```bash
python run.py
```

Then access the application in your browser at:
```
http://127.0.0.1:5000
```

## Step 3: Using the Application

1. Search for reagents using the search box (e.g., search for "GFP" as a Gene/ORF)
2. View details by clicking on the reagent names in the search results
3. Add new entries using the "Add New Entry" button
4. Import/Export data as needed

## Troubleshooting

If you encounter issues:

1. Check the database with the diagnostic tool:
   ```bash
   python diagnostic.py
   ```

2. Reset the database if needed:
   ```bash
   python reset_db.py
   ```

## Project Structure After Cleanup

The application has a clean structure with:

- `app/` - Core application code
- `templates/` - HTML templates 
- `exports/` - Export destination
- `uploads/` - Upload destination
- Configuration files: `app_config.json` and `config.py`
- Main runner: `run.py`
- Database utilities: `setup_db.py` and `insert_sample_data.py`
- Troubleshooting tools: `diagnostic.py` and `reset_db.py`
