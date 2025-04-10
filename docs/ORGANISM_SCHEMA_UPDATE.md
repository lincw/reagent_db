# Organism Schema Update

This document describes a critical schema change in the database model to properly link organisms with their corresponding ORFs.

## Problem Description

In the original database schema, the relationship between organisms and ORF sequences was defined as follows:

- `orf_sequence` table had an `orf_organism_id` field that referenced `organisms.organism_id`
- `organisms` table did not have an `orf_id` field to reference back to the ORFs

This made it difficult to:
1. Find which ORF a specific organism was associated with
2. Update the organism information based on ORF data
3. Maintain proper bidirectional relationships between these entities

## Solution

We have introduced a new field `orf_id` in the `organisms` table to create a bidirectional relationship between organisms and ORFs.

### Schema Changes

The updated organisms table now includes:

```sql
CREATE TABLE organisms (
    organism_id TEXT PRIMARY KEY,
    organism_name TEXT,
    organism_genus TEXT,
    organism_species TEXT,
    organism_strain TEXT,
    orf_id TEXT,
    FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
)
```

## How to Apply This Update

To update your existing database with this schema change, follow these steps:

1. **Create a backup of your database**:
   ```bash
   cp /path/to/reagent_db.sqlite /path/to/backup_$(date +%Y%m%d).sqlite
   ```

2. **Run the migration script**:
   ```bash
   python run_migration.py fix_organisms_schema
   ```

3. **Verify the migration was successful**:
   Check the Database Summary section on the homepage, which should now show the number of linked organisms.

4. **Fix any remaining data inconsistencies**:
   ```bash
   # First analyze the current state
   python utils/fix_orf_organism_links.py --analyze
   
   # Then apply fixes (after reviewing the analysis)
   python utils/fix_orf_organism_links.py --fix
   ```

## Verification

After applying the update, you should see:

1. A new "linked to ORFs" statistic under "Unique Organisms" in the Database Summary
2. Improved data consistency between the organisms and ORF tables
3. Better performance for queries that need to find the relationship between organisms and ORFs

## Troubleshooting

If you encounter issues during migration:

1. Restore from your backup
2. Check the database logs for specific error messages
3. Make sure there are no active connections to the database during migration
4. Contact the database administrator for assistance

