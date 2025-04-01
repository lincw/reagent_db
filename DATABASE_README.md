# Reagent Database Management Guide

This guide provides instructions for cleaning and importing data into the Reagent Database application.

## Database Structure

The database consists of the following tables:

- **freezer** - Stores information about freezers where samples are stored
- **organisms** - Stores information about biological organisms
- **plasmid** - Stores information about plasmids
- **orf_sequence** - Stores ORF sequence information
- **orf_position** - Stores the physical location of ORFs

## Setting Up a Clean Database

To reset the database and start with a clean installation:

```bash
# Create a clean, empty database (with backup of existing data)
python clean_db.py
```

This will:
1. Back up your existing database (if one exists)
2. Create a fresh, empty database with the correct schema
3. Verify that all tables are empty

## Importing Data

You have several options for importing data:

### 1. Using the Example Import Template

For testing or understanding the import process:

```bash
# Insert example data to test the database
python import_template.py
```

### 2. Importing from CSV Files

For importing bulk data:

```bash
# Import data from CSV files
python import_from_csv.py /path/to/csv/directory
```

The CSV directory should contain the following files:
- `freezers.csv`
- `organisms.csv`
- `plasmids.csv`
- `orf_sequences.csv`
- `orf_positions.csv`

Template CSV files are available in the `csv_templates` directory.

### 3. Using the Web UI

Once the database is set up, you can use the web interface to add, edit, and import data:

```bash
# Start the web server
python run.py
```

Then open a browser and navigate to: http://127.0.0.1:5000

## Best Practices

1. **Always back up your database** before making major changes
2. **Validate your CSV data** before import to ensure it's correctly formatted
3. **Test imports** on a small subset of data first
4. **Follow the correct order** when importing data:
   - Import freezers and organisms first
   - Then import plasmids
   - Then import ORF sequences
   - Finally import ORF positions (as they reference the other tables)

## Troubleshooting

If you encounter issues:

1. Check the application logs in the `logs` directory
2. Run the diagnostic tool to check database integrity:
   ```bash
   python diagnostic.py
   ```
3. Ensure your CSV files have the correct column headers and data formats
