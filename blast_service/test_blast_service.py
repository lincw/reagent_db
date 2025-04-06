#!/usr/bin/env python
"""
Test script for the BLAST service.
This script helps verify that the BLAST service is working correctly.
"""

import requests
import json
import sys
import os

# Default URL for the BLAST service
SERVICE_URL = 'http://localhost:5001'

def check_service_status():
    """Check if the BLAST service is running and available."""
    try:
        response = requests.get(f"{SERVICE_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n✅ BLAST service is online")
            
            if data.get('blast_installed', False):
                print("✅ BLAST+ tools are installed")
            else:
                print("❌ BLAST+ tools are NOT installed")
            
            if data.get('blast_db_exists', False):
                print("✅ BLAST database exists")
                dbs = data.get('databases', [])
                if dbs:
                    print(f"   Available databases: {', '.join(dbs)}")
            else:
                print("❌ No BLAST database found")
                
            return True
        else:
            print(f"\n❌ Service returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"\n❌ Error connecting to BLAST service: {str(e)}")
        return False

def create_test_database():
    """Create a small test BLAST database."""
    # Example sequence data (small test dataset)
    sequences = [
        {
            'id': 'test1',
            'name': 'Test Sequence 1',
            'organism': 'Test Organism',
            'sequence': 'ATGGCGTGCATGCTAGCTAGCTGATCGATCGATCGATCGATCGATCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTGATCG'
        },
        {
            'id': 'test2',
            'name': 'Test Sequence 2',
            'organism': 'Test Organism',
            'sequence': 'ATGGCGTGCATGCTAGCTAACTGATCGATCGAACGATCGATCGATCGATCGTAGCTAGCCAGCTAGCTAGCTATCTAGCTGATCG'
        }
    ]
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/create_db_from_sequences",
            data={
                'db_name': 'test_db',
                'db_type': 'nucl',
                'sequences': json.dumps(sequences)
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                print("\n✅ Test database created successfully")
                return True
            else:
                print(f"\n❌ Failed to create test database: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Service returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"\n❌ Error connecting to BLAST service: {str(e)}")
        return False

def run_test_blast_search():
    """Run a test BLAST search against the test database."""
    # Query that should match our test sequences
    query = 'ATGGCGTGCATGCTAG'
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/blast",
            data={
                'sequence': query,
                'program': 'blastn',
                'evalue': '10',
                'max_hits': '10',
                'db_name': 'test_db'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                results = data.get('results', [])
                if results:
                    print(f"\n✅ BLAST search successful! Found {len(results)} hits")
                    for hit in results:
                        print(f"   Hit: {hit['orf_id']} - Score: {hit['bit_score']:.1f} - E-value: {hit['evalue']:.2e}")
                else:
                    print("\n⚠️ BLAST search successful but no hits found")
                return True
            else:
                print(f"\n❌ BLAST search failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Service returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"\n❌ Error connecting to BLAST service: {str(e)}")
        return False

def main():
    """Main function to run all tests."""
    print("=== BLAST Service Test ===")
    print(f"Using service URL: {SERVICE_URL}")
    
    # Check if service is running
    if not check_service_status():
        print("\n❌ BLAST service is not available. Please start the service and try again.")
        sys.exit(1)
    
    # Create test database
    if not create_test_database():
        print("\n❌ Failed to create test database. Please check the logs for more information.")
        sys.exit(1)
    
    # Run test BLAST search
    if not run_test_blast_search():
        print("\n❌ Failed to run test BLAST search. Please check the logs for more information.")
        sys.exit(1)
    
    print("\n✅ All tests passed! The BLAST service is working correctly.")

if __name__ == '__main__':
    # Check if a custom URL was provided
    if len(sys.argv) > 1:
        SERVICE_URL = sys.argv[1]
    # Also check environment variable
    SERVICE_URL = os.environ.get('BLAST_SERVICE_URL', SERVICE_URL)
    
    main()
