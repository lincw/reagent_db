# Reagent Database Application - Explanation

## Overview

This application serves as a laboratory reagent database management system, allowing researchers to track and search for Open Reading Frames (ORFs), plasmids, organisms, and freezer locations. The application provides a web-based interface for data management and search functionality.

## Architecture

The application follows a standard web application architecture:

1. **Backend**: Flask (Python web framework)
2. **Database**: SQLite (Local file-based database)
3. **Frontend**: HTML, JavaScript, and Bootstrap CSS framework

## Database Structure

The database schema consists of five related tables:

1. **freezer**: Stores information about freezer locations and conditions
   - Primary key: `freezer_id`

2. **organisms**: Stores information about biological organisms
   - Primary key: `organism_id`

3. **plasmid**: Stores information about plasmids
   - Primary key: `plasmid_id`

4. **orf_sequence**: Stores detailed information about ORF sequences
   - Primary key: `orf_id`
   - Foreign key: `orf_organism_id` references `organisms(organism_id)`

5. **orf_position**: Stores physical location information for ORFs
   - Primary key: `id` (auto-increment)
   - Foreign keys:
     - `orf_id` references `orf_sequence(orf_id)`
     - `freezer_id` references `freezer(freezer_id)`
     - `plasmid_id` references `plasmid(plasmid_id)`

These relationships allow for complex queries, such as finding all ORFs for a particular organism or finding all plasmids containing a specific ORF.

## Key Features

### Search Functionality

The application supports searching by:

1. **Gene/ORF**: Search by gene name or annotation
   - Results include sequence details and position information

2. **Plasmid**: Search by plasmid name or description
   - Results include associated ORFs

3. **Location**: Search by plate and well location
   - Results include ORF and freezer details

4. **Organism**: Search by organism name, genus, or species
   - Results include associated ORFs

### Data Entry

The application provides forms for adding new:

1. **ORFs**: Including sequence information and position details
2. **Plasmids**: Including type and expression organism
3. **Organisms**: Including taxonomic information
4. **Freezers**: Including location and condition information

### Data Export

The application can export all database tables to CSV files, which can be shared with colleagues or imported into other systems.

## Implementation Details

### Backend (app.py)

- Initializes the SQLite database and creates tables if they don't exist
- Provides API endpoints for:
  - Searching the database
  - Adding new entries
  - Exporting data
  - Retrieving reference data (organisms, plasmids, freezers)

### Frontend (HTML/JavaScript)

- **index.html**: Main search interface
  - Search form
  - Results display
  - Export button

- **add_entry.html**: Data entry interface
  - Dynamically shows different forms based on entry type
  - Populates dropdowns with reference data from the database

### Supporting Scripts

- **insert_sample_data.py**: Inserts sample data for testing
- **export_data.py**: Exports database data to CSV files
- **setup.sh**: Sets up the application with dependencies and sample data
- **run.sh**: Runs the application

## Usage Flow

1. User visits the homepage and selects a search type
2. User enters a search term and submits the form
3. Backend processes the search query against the database
4. Results are displayed in a tabular format
5. User can view detailed information about results
6. User can add new entries or export data as needed

## Extension Points

The application can be extended in several ways:

1. **Authentication**: Add user authentication for secure access
2. **File Attachments**: Allow attaching files (e.g., sequence files, images)
3. **Advanced Search**: Implement more complex search criteria
4. **Data Visualization**: Add charts or graphs for data visualization
5. **Batch Import/Export**: Support for bulk data operations
6. **API Integration**: Connect to external databases (e.g., GenBank, UniProt)

## Running the Application

1. Run `./setup.sh` to install dependencies and initialize the database with sample data
2. Run `./run.sh` to start the application
3. Open your browser and navigate to http://127.0.0.1:5000
