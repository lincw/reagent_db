# Reagent Database Application - Fixed Version

## Issues Fixed

1. **Removed Unnecessary Components**
   - Removed the ReagentDB_Demo and ReagentDB_Portable directories
   - Cleaned up project structure

2. **Fixed Link Navigation**
   - Detail view links now work correctly by ensuring proper string ID handling
   - Fixed column name mismatch in SQL queries (freezer_temp → freezer_condition)
   - Routes accept string IDs instead of integer IDs
   - All SQL queries explicitly cast IDs to strings for consistency

3. **Fixed Template Issues**
   - Created a base.html template
   - All templates now extend from the base template
   - Settings page now displays correctly
   - Updated templates to use correct column names

## How to Run the Application

1. **Run the diagnostic tool first to check for issues**:
   ```bash
   python diagnostic.py
   ```
   This will verify that the database is properly set up and queries are working.

2. **If issues are found, reset the database**:
   ```bash
   python reset_db.py
   ```
   This will create a fresh database with sample data.

3. **Start the application**:
   ```bash
   python run.py
   ```

4. **Access the application** in your browser:
   ```
   http://127.0.0.1:5000
   ```

## Search Example

1. In the search box, select "Gene/ORF" as the search type
2. Enter "GFP" in the search term field
3. Click "Search"
4. In the results, click on the "GFP" link to view ORF details

## Troubleshooting

If you encounter SQL errors:

1. **Column name issues**: We've fixed the column name mismatch (freezer_temp → freezer_condition)
2. **Reset database**: If issues persist, run `python reset_db.py` to get a fresh start
3. **Clear browser cache**: Sometimes old JavaScript can cause issues
4. **Restart Flask server**: Stop and restart the application with `python run.py`

## Database Structure 

The application uses SQLite with the following tables:

- **freezer**: Stores freezer information (freezer_id, freezer_location, freezer_condition, freezer_date)
- **organisms**: Stores organism information
- **plasmid**: Stores plasmid information
- **orf_sequence**: Stores Open Reading Frame sequences
- **orf_position**: Links ORFs to physical locations (plate/well)

Important note: The freezer table has a `freezer_condition` column that contains temperature information (e.g., "-20°C"), not a separate `freezer_temp` column as was incorrectly referenced in some code.

## Additional Tools

- **diagnostic.py**: Database checker to verify structure and data
- **reset_db.py**: Reset to a fresh database with sample data
- **fix_app.py**: Fix all known issues in the application

## Development

If you need to modify the application:

1. Routes are in `app/routes/` directory
2. Templates are in the `templates/` directory
3. Database operations are defined in `setup_db.py`
4. Sample data is defined in `insert_sample_data.py`

## Database Backup

The `reset_db.py` script automatically creates backups in a `db_backups` directory before resetting. If you need to restore a backup, simply copy it back to the main application directory and rename it to `reagent_db.sqlite`.
