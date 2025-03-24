# Running the Reagent Database Application

Due to compatibility issues with pandas on Python 3.12, I've created a simplified version of the application that doesn't depend on pandas. Follow these steps to run the application:

## Setup Instructions

1. Make the setup script executable:
   ```bash
   chmod +x simple_setup.sh
   ```

2. Run the simplified setup script:
   ```bash
   ./simple_setup.sh
   ```
   This will:
   - Install Flask (the only required dependency)
   - Create the SQLite database
   - Insert sample data
   - Make the run.sh script executable

3. Run the application:
   ```bash
   ./run.sh
   ```

4. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Troubleshooting

If you encounter any issues:

1. Check if Flask is installed:
   ```bash
   pip list | grep Flask
   ```
   If not installed, run:
   ```bash
   pip install flask
   ```

2. Ensure the database was created:
   ```bash
   ls -la reagent_db.sqlite
   ```
   If it doesn't exist, you can manually create it:
   ```bash
   python -c "from app_simple import init_db; init_db()"
   ```

3. Ensure the sample data was inserted:
   ```bash
   python insert_sample_data.py
   ```

4. If you get permission errors when running the scripts:
   ```bash
   chmod +x *.sh
   ```

## Application Structure

- `app_simple.py`: The main Flask application
- `templates/`: Directory containing HTML templates
- `reagent_db.sqlite`: SQLite database file
- `insert_sample_data.py`: Script to insert sample data

### Features

- Search for genes/ORFs, plasmids, organisms, and locations
- Add new entries to the database
- Export data to CSV files
