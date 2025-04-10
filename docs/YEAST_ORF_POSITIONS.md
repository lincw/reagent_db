# Yeast ORF Positions

This document describes the updated yeast ORF position functionality, which now supports both AD (Activation Domain) and DB (DNA Binding Domain) position types.

## Background

In yeast two-hybrid (Y2H) systems, proteins can be fused to either:
- **AD (Activation Domain)** - Activates transcription when brought into proximity with a promoter
- **DB (DNA Binding Domain)** - Binds to a specific DNA sequence in the promoter region

Tracking both AD and DB plasmids is essential for comprehensive yeast two-hybrid screening and analysis.

## Database Schema Updates

The `yeast_orf_position` table has been updated to include a `position_type` column:

```sql
CREATE TABLE yeast_orf_position (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orf_id TEXT,
    plate TEXT,
    well TEXT,
    position_type TEXT DEFAULT 'AD',  -- New column
    FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
)
```

## How to Apply the Update

To add the `position_type` column to your database:

1. Run the migration script:
   ```bash
   python run_migration.py update_yeast_orf_position
   ```

2. Verify the migration by checking the Database Summary section on the homepage, which should now show both AD and DB counts.

## Importing Yeast ORF Positions

### CSV Format

The updated CSV format for importing yeast ORF positions now includes the position_type column:

```
orf_id,plate,well,position_type
ORF001,Yeast Plate A,A1,AD
ORF002,Yeast Plate B,B5,DB
ORF003,Yeast Plate C,C3,AD
```

The `position_type` column should contain either "AD" or "DB". If not specified, it defaults to "AD".

### Import Tool

A new utility script is available for importing yeast ORF positions:

```bash
python utils/import_yeast_positions.py path/to/your/csv_file.csv
```

Options:
- `--dry-run`: Validate the file without making any changes to the database
- `--no-validate`: Skip ORF ID validation (useful for importing positions for ORFs that will be added later)

Example:
```bash
# Validate the file without importing
python utils/import_yeast_positions.py data/yeast_positions.csv --dry-run

# Import the positions
python utils/import_yeast_positions.py data/yeast_positions.csv
```

## Database Summary

The Database Summary section now shows:
- Total yeast ORF positions
- Breakdown of AD and DB positions

This helps researchers quickly see the distribution of yeast positions in the database.

## Search Results

When searching for ORFs, the results now display both AD and DB positions with appropriate labeling. This makes it easier to identify different types of yeast constructs available for each ORF.

## Migration from Old Format

If you have existing yeast ORF position data without the position type specified, the migration will automatically set all existing positions to "AD" by default. If you need to update some positions to "DB", you can:

1. Export your current yeast positions
2. Modify the CSV to add the position_type column
3. Clear the existing positions (optional)
4. Re-import the updated CSV
