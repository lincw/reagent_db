# CSV Templates for Reagent Database Import

This directory contains template CSV files that can be used to import data into the Reagent Database application.

## Files

- `freezers.csv` - Template for freezer data
- `organisms.csv` - Template for organism data
- `plasmids.csv` - Template for plasmid data
- `orf_sequences.csv` - Template for ORF sequence data
- `orf_positions.csv` - Template for ORF position data

## How to Use

1. Edit these CSV files to add your data
2. Run the import script to import your data into the database

```
python import_from_csv.py /path/to/csv/directory
```

## CSV File Formats

### freezers.csv
- `freezer_id`: Unique identifier for the freezer
- `freezer_location`: Location of the freezer
- `freezer_condition`: Condition of the freezer (e.g., temperature)
- `freezer_date`: Date the freezer was installed or recorded

### organisms.csv
- `organism_id`: Unique identifier for the organism
- `organism_name`: Name of the organism
- `organism_genus`: Genus of the organism
- `organism_species`: Species of the organism
- `organism_strain`: Strain of the organism

### plasmids.csv
- `plasmid_id`: Unique identifier for the plasmid
- `plasmid_name`: Name of the plasmid
- `plasmid_type`: Type of plasmid
- `plasmid_express_organism`: Organism the plasmid is expressed in
- `plasmid_description`: Description of the plasmid

### orf_sequences.csv
- `orf_id`: Unique identifier for the ORF
- `orf_name`: Name of the ORF
- `orf_annotation`: Annotation of the ORF
- `orf_sequence`: DNA sequence of the ORF
- `orf_with_stop`: Whether the sequence includes a stop codon (1=yes, 0=no)
- `orf_open`: Whether the sequence is an open reading frame (1=yes, 0=no)
- `orf_organism_id`: Identifier of the organism this ORF is from
- `orf_length_bp`: Length of the ORF in base pairs
- `orf_entrez_id`: Entrez Gene ID
- `orf_ensembl_id`: Ensembl ID
- `orf_uniprot_id`: UniProt ID
- `orf_ref_url`: Reference URL

### orf_positions.csv
- `orf_id`: Identifier of the ORF
- `plate`: Plate identifier
- `well`: Well identifier
- `freezer_id`: Identifier of the freezer where the sample is stored
- `plasmid_id`: Identifier of the plasmid
- `orf_create_date`: Date the position was created or recorded
