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

The application logs will be saved to the `logs` directory instead of being displayed in the terminal. To view logs, use the log viewer utility:

```bash
# View the latest logs (last 50 lines)
python view_logs.py

# View more lines
python view_logs.py -n 100

# Search for specific log entries
python view_logs.py -g "error"

# List all available log files
python view_logs.py -l
```

## Step 3: Using the Application

1. **Search for reagents**: Use the search box on the homepage (e.g., search for "GFP" as a Gene/ORF)
2. **Batch Search**: Use the Batch Search feature to look up multiple genes at once
3. **View details**: Click on reagent names in search results to see detailed information
4. **External databases**: For genes, use the external links to access Entrez, UniProt, and Ensembl databases
5. **Add new entries**: Use the "Add New Entry" button to add individual records
6. **Import/Export data**: Use the Import and Export features for bulk data management

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
