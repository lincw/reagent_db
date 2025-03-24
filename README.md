# Reagent Database Application

A web-based tool to collect, search, and share experimental results for laboratory reagents, including ORFs (Open Reading Frames), plasmids, organisms, and freezer locations. The application supports portable mode with database storage on OneDrive for easier sharing across multiple computers.

## Quick Start

```bash
# Make scripts executable
bash prepare.sh

# Set up database with toy examples
./setup.sh

# Run the application
./run.sh
```

Then open your browser to http://127.0.0.1:5000

## Features

- **Search functionality**: Search by gene/ORF, plasmid, location, or organism
- **Add new entries**: Add new ORFs, plasmids, organisms, or freezer locations
- **Export data**: Export database contents to CSV files
- **Toy examples**: Pre-loaded with realistic laboratory samples

## Included Toy Examples

### Freezers
- 5 different freezers with various locations and temperatures (-80°C, -196°C, 4°C)

### Organisms
- 6 different organisms: E. coli (two strains), yeast, human cells, mouse, and fruit fly

### Plasmids
- 6 different plasmids: expression vectors, mammalian expression, yeast shuttle vectors, etc.

### ORFs (Genes)
- 8 different genes including:
  - Fluorescent proteins (GFP, mCherry)
  - Common marker genes (LacZ, GAPDH)
  - Human genes (p53)
  - CRISPR-Cas9
  - Yeast genes (ACT1, SNF1)

## Example Searches to Try

1. **Search by Gene/ORF**: "GFP", "p53"
2. **Search by Plasmid**: "pET", "Lenti"
3. **Search by Location**: "P01", "P05-F"
4. **Search by Organism**: "coli", "Homo"

## Project Structure

```
reagent_db_app/
├── app.py              # Main Flask application
├── exports/            # Directory for exported CSV files
├── insert_sample_data.py  # Script with toy examples
├── prepare.sh          # Makes scripts executable
├── reagent_db.sqlite   # SQLite database file
├── run.sh              # Runs the application
├── setup.sh            # Sets up the application with toy data
├── setup_db.py         # Initializes the database schema
└── templates/          # HTML templates
    ├── add_entry.html  # Form for adding entries
    └── index.html      # Main search interface
```
