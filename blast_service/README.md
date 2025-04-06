# BLAST Service for Reagent DB

This is a standalone microservice for running BLAST searches, designed to work with the Reagent DB application.

## Overview

The BLAST service provides a RESTful API for:
- Creating and managing BLAST databases
- Running BLAST searches
- Retrieving and formatting results

This service is isolated from the main application to prevent issues with empty pages and improve stability.

## Running the Service

### Using Docker (Recommended)

The easiest way to run the BLAST service is using Docker:

```bash
# From the parent directory containing the docker-compose.yml file
docker-compose up -d blast
```

This will build and start the BLAST service container.

### Running Directly

If you prefer to run the service directly:

1. Install BLAST+ tools for your operating system:
   - macOS: `brew install blast`
   - Ubuntu/Debian: `sudo apt-get install ncbi-blast+`
   - Windows: Download from [NCBI website](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/)

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the service:
   ```bash
   python app.py
   ```

The service will start on port 5001 by default.

## API Endpoints

### Status Check

```
GET /status
```

Returns the current status of the BLAST service, including whether BLAST+ is installed and if any databases exist.

### Create Database from FASTA File

```
POST /create_db
```

Parameters:
- `file`: FASTA format file (multipart/form-data)
- `db_name`: Name for the database (optional)
- `db_type`: Database type, either 'nucl' (nucleotide) or 'prot' (protein)

### Create Database from Sequences

```
POST /create_db_from_sequences
```

Parameters:
- `sequences`: JSON array of sequence objects, each with `id`, `name`, `organism`, and `sequence` fields
- `db_name`: Name for the database (optional)
- `db_type`: Database type, either 'nucl' (nucleotide) or 'prot' (protein)

### Run BLAST Search

```
POST /blast
```

Parameters:
- `sequence`: Query sequence
- `program`: BLAST program to use ('blastn', 'blastp', 'blastx', 'tblastn', 'tblastx')
- `evalue`: E-value threshold
- `max_hits`: Maximum number of hits to return
- `db_name`: Database to search against

### List Databases

```
GET /list_dbs
```

Returns a list of all available BLAST databases.

### Delete Database

```
DELETE /delete_db/<db_name>
```

Deletes the specified BLAST database.

## Security Considerations

This service is designed to be used internally and should not be exposed to the public internet without additional security measures.

## Troubleshooting

If you encounter issues:

1. Check if BLAST+ tools are installed correctly:
   ```bash
   blastn -version
   ```

2. Verify the service is running:
   ```bash
   curl http://localhost:5001/status
   ```

3. Check the logs for error messages.
