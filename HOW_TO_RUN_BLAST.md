# How to Run the BLAST Service

This guide explains how to set up and run the BLAST service for Reagent DB.

## Option 1: Using Docker (Recommended)

The easiest way to get started is using Docker Compose to run both the main application and the BLAST service:

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1. Open a terminal and navigate to the project directory:
   ```bash
   cd /path/to/reagent_db_app
   ```

2. Start both services:
   ```bash
   docker-compose up -d
   ```

3. Check if the services are running:
   ```bash
   docker-compose ps
   ```

4. View logs:
   ```bash
   docker-compose logs -f
   ```

5. Access the application:
   - Main application: http://localhost:5000
   - BLAST service status: http://localhost:5001/status

6. To stop the services:
   ```bash
   docker-compose down
   ```

## Option 2: Manual Setup

If you prefer to run the services without Docker:

### Prerequisites
- Python 3.6 or higher
- BLAST+ command-line tools

### Installing BLAST+

#### macOS
```bash
brew install blast
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ncbi-blast+
```

#### Windows
1. Download the installer from [NCBI website](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/)
2. Run the installer and follow the instructions
3. Make sure the installation directory is added to your system PATH

### Steps

1. Start the BLAST service:
   ```bash
   cd /path/to/reagent_db_app/blast_service
   pip install -r requirements.txt
   python app.py
   ```

2. In a new terminal, start the main application:
   ```bash
   cd /path/to/reagent_db_app
   pip install -r requirements.txt
   export BLAST_SERVICE_URL=http://localhost:5001  # Unix/macOS
   # or
   set BLAST_SERVICE_URL=http://localhost:5001     # Windows
   python run.py
   ```

3. Access the application:
   - Main application: http://localhost:5000
   - BLAST service status: http://localhost:5001/status

## Testing the BLAST Service

A test script is provided to verify that the BLAST service is working correctly:

```bash
cd /path/to/reagent_db_app/blast_service
python test_blast_service.py
```

This script will:
1. Check if the BLAST service is running
2. Create a small test database
3. Run a test BLAST search

If all tests pass, you'll see a success message.

## Troubleshooting

### BLAST Service Not Starting

- Check if BLAST+ is installed:
  ```bash
  blastn -version
  ```
  
- Verify port 5001 is available:
  ```bash
  lsof -i :5001  # Unix/macOS
  netstat -ano | findstr :5001  # Windows
  ```

### Database Creation Issues

- Check the BLAST service logs for specific errors
- Ensure the BLAST service has write permissions to its directories

### Empty BLAST Results

1. Verify the BLAST database exists:
   - Check http://localhost:5001/list_dbs
   
2. Make sure your query sequence is valid

3. Try updating the BLAST database:
   - Click "Update BLAST Database" in the web interface
   
4. Check if there are sequences in the database:
   - Use the SQLite browser to verify orf_sequence table has entries

### Connection Issues

If the main application can't connect to the BLAST service:

1. Verify the BLAST service is running
2. Check that the BLAST_SERVICE_URL is set correctly
3. Make sure no firewall is blocking the connection

## Restarting Services

If you need to restart the services:

### Docker:
```bash
docker-compose restart
```

### Manual:
Stop both processes (Ctrl+C) and start them again.

## Getting Help

If you continue to experience issues:

1. Check the logs for both services
2. Look at the specific error messages
3. Contact the system administrator

Remember that the separate BLAST service architecture helps isolate problems, so even if BLAST searches aren't working, the main application should still function normally for other tasks.
