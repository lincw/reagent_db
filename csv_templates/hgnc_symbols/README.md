# HGNC Approved Symbol Import

This directory contains template files for importing HGNC approved symbols for human genes.

## Files

- `hgnc_symbol_template.csv` - Template for HGNC approved symbol data

## Usage

1. Prepare your CSV file with the following columns:
   - `orf_id`: The ORF ID from the database
   - `hgnc_approved_symbol`: The HGNC approved symbol for the gene

2. Run the import script:
   ```
   python import_hgnc_symbols.py path/to/your/hgnc_symbols.csv
   ```

## Notes

- This import only applies to human genes (Homo sapiens)
- The ORF IDs must already exist in the database
- HGNC symbols will be searchable alongside the regular gene names
- For human genes, both the HGNC symbol and original name will be displayed in search results
