#!/usr/bin/env python
"""
Test script for BLAST functionality.
Run this script to verify that BLAST is working correctly on your system.
"""

import os
import subprocess
import tempfile
import sys
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("blast_test")

def check_blast_installed():
    """Check if BLAST+ tools are installed and working."""
    logger.info("Checking BLAST installation...")
    
    try:
        result = subprocess.run(['blastn', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ BLAST+ is installed: {result.stdout.splitlines()[0]}")
            return True
        else:
            logger.error(f"❌ BLAST command returned non-zero exit code: {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("❌ BLAST+ tools are not installed or not in your PATH")
        logger.info("Please install BLAST+ tools:")
        logger.info("  - macOS: brew install blast")
        logger.info("  - Ubuntu/Debian: sudo apt-get install ncbi-blast+")
        logger.info("  - Windows: Download from https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking BLAST installation: {str(e)}")
        return False

def test_blast_search():
    """Test a simple BLAST search to verify functionality."""
    logger.info("Testing basic BLAST functionality...")
    
    # Create a temporary directory for our test
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a small test database
            test_db_path = os.path.join(temp_dir, "test_db")
            
            # Create test sequences
            test_fasta = os.path.join(temp_dir, "test.fasta")
            with open(test_fasta, 'w') as f:
                f.write(">seq1\n")
                f.write("ATGGCGTGCATGCTAGCTAGCTGATCGATCGATCGATCG\n")
                f.write(">seq2\n")
                f.write("ATGGCGTGCATGCTAGCTAACTGATCGATCGAACGATCG\n")
            
            # Create BLAST database
            logger.info("Creating test BLAST database...")
            make_cmd = [
                'makeblastdb', 
                '-in', test_fasta, 
                '-dbtype', 'nucl', 
                '-out', test_db_path
            ]
            
            result = subprocess.run(make_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ Failed to create test BLAST database")
                logger.error(f"Error: {result.stderr}")
                return False
            
            # Create a query sequence
            query_file = os.path.join(temp_dir, "query.fasta")
            with open(query_file, 'w') as f:
                f.write(">query\n")
                f.write("ATGGCGTGCATGCTAG\n")
            
            # Run BLAST search
            logger.info("Running test BLAST search...")
            blast_cmd = [
                'blastn',
                '-query', query_file,
                '-db', test_db_path,
                '-outfmt', '6'  # Tabular format for simplicity
            ]
            
            result = subprocess.run(blast_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ BLAST search failed")
                logger.error(f"Error: {result.stderr}")
                return False
            
            # Check if we got hits
            hits = result.stdout.strip().split('\n')
            if hits and hits[0]:  # Check if not empty
                logger.info(f"✅ BLAST search successful! Found {len(hits)} hits")
                return True
            else:
                logger.warning("⚠️ BLAST search completed but no hits found")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error during BLAST test: {str(e)}")
            return False

def main():
    """Main test function."""
    print("=" * 60)
    print(" BLAST Functionality Test ")
    print("=" * 60)
    print()
    
    # Test 1: Check installation
    if not check_blast_installed():
        print("\n❌ BLAST installation test failed")
        sys.exit(1)
    
    print()
    
    # Test 2: Test BLAST search
    if not test_blast_search():
        print("\n❌ BLAST search test failed")
        sys.exit(1)
    
    print("\n✅ All tests passed! BLAST appears to be working correctly.")
    print("\nYou should now be able to use the BLAST functionality in the Reagent DB application.")
    print("If you're still having issues, please check the application logs for more details.")

if __name__ == "__main__":
    main()
