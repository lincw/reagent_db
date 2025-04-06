# BLAST Search Functionality for Reagent Database

This document explains how to set up and use the BLAST (Basic Local Alignment Search Tool) functionality in the Reagent Database application.

## New Architecture: Separate BLAST Service

The BLAST functionality now uses a separate microservice architecture to solve issues with empty pages and improve reliability:

1. A dedicated BLAST service runs independently from the main application
2. The main application communicates with the BLAST service via API calls
3. The BLAST service handles all interactions with the BLAST+ command-line tools

This separation ensures that any issues with BLAST searches won't affect the main application's stability.

## Setup Requirements

### Option 1: Using Docker (Recommended)

The easiest way to run both the main application and the BLAST service is using Docker Compose:

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f
```

Docker automatically installs BLAST+ tools in the BLAST service container.

### Option 2: Manual Setup

If you prefer to run the services directly:

1. Install BLAST+ command-line tools:
   - macOS: `brew install blast`
   - Ubuntu/Debian: `sudo apt-get install ncbi-blast+`
   - Windows: Download from [NCBI website](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/)

2. Start the BLAST service:
   ```bash
   cd blast_service
   pip install -r requirements.txt
   python app.py
   ```

3. Configure the main application to use the BLAST service:
   - Set the `BLAST_SERVICE_URL` environment variable to point to your BLAST service
   - Example: `export BLAST_SERVICE_URL=http://localhost:5001`

4. Start the main application as usual:
   ```bash
   python run.py
   ```

## How It Works

1. The separate BLAST service maintains its own BLAST database, created from the sequences in the Reagent DB.
2. When a user submits a sequence for BLAST search, the main application:
   - Sends the search request to the BLAST service
   - The BLAST service runs the search and returns formatted results
   - The main application displays these results to the user

## Updating the BLAST Database

The BLAST database is automatically created when the first BLAST search is performed. If you've added new sequences to the database and want to update the BLAST database, you can:

1. Click the "Update BLAST Database" button on the BLAST search page
2. This sends a request to the BLAST service to rebuild its database with the latest sequences

## Using BLAST Search

The BLAST search interface remains the same as before:

### Sequence Types
- For **nucleotide sequences** (DNA), use A, T, G, C
- For **protein sequences** (amino acids), use the standard single-letter codes (A, R, N, D, etc.)

### BLAST Programs
- **blastn**: Nucleotide query → Nucleotide database (DNA to DNA)
- **blastp**: Protein query → Protein database (protein to protein)
- **blastx**: Translated nucleotide query → Protein database (DNA to protein)
- **tblastn**: Protein query → Translated nucleotide database (protein to DNA)
- **tblastx**: Translated nucleotide query → Translated nucleotide database (DNA to DNA, translated to protein)

### Search Parameters
- **E-value threshold**: Lower values are more stringent (fewer matches, higher confidence)
- **Maximum hits**: Limits the number of results returned

## Troubleshooting

If you encounter issues with the BLAST search functionality:

1. Check if the BLAST service is running:
   - Visit `http://localhost:5001/status` in your browser
   - Look for `"status": "online"` in the response

2. Check if the BLAST database exists:
   - The status endpoint will include `"blast_db_exists": true` if a database is available
   - If not, try clicking the "Update BLAST Database" button

3. Check the logs of both services:
   - Docker Compose: `docker-compose logs -f`
   - Direct: Check the terminal where each service is running

4. Common issues:
   - BLAST service unreachable: Ensure the BLAST service is running and the URL is correctly configured
   - Empty results: Make sure the query sequence is valid and the BLAST database contains sequences
   - Error messages: Check the application logs for specific error details
