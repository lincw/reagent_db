#!/usr/bin/env python3
"""
Log viewer utility for the Reagent Database application.
This script shows the most recent log entries.
"""

import os
import sys
import datetime
import argparse

def get_latest_log_file():
    """Find the most recent log file in the logs directory"""
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        print("Logs directory not found. No logs have been created yet.")
        return None
    
    # Get all log files
    log_files = [f for f in os.listdir(logs_dir) if f.startswith('reagent_db_') and f.endswith('.log')]
    
    if not log_files:
        print("No log files found in the logs directory.")
        return None
    
    # Sort by modification time (most recent first)
    log_files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
    
    return os.path.join(logs_dir, log_files[0])

def view_log(log_file, lines=50, grep=None):
    """View the specified number of lines from the log file"""
    if not log_file:
        return
    
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    # Read the log file
    with open(log_file, 'r') as f:
        log_lines = f.readlines()
    
    # Filter lines if grep is specified
    if grep:
        log_lines = [line for line in log_lines if grep.lower() in line.lower()]
    
    # Get the last n lines
    log_lines = log_lines[-lines:]
    
    if not log_lines:
        print("No matching log entries found.")
        return
    
    # Print the log entries
    print(f"\n{'='*80}")
    print(f"Log file: {os.path.basename(log_file)}")
    print(f"Showing {len(log_lines)} entries{' matching: ' + grep if grep else ''}")
    print(f"{'='*80}\n")
    
    for line in log_lines:
        print(line.strip())

def list_available_logs():
    """List all available log files"""
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        print("Logs directory not found. No logs have been created yet.")
        return
    
    # Get all log files
    log_files = [f for f in os.listdir(logs_dir) if f.startswith('reagent_db_') and f.endswith('.log')]
    
    if not log_files:
        print("No log files found in the logs directory.")
        return
    
    # Sort by modification time (most recent first)
    log_files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
    
    print("\nAvailable log files:")
    print("==========================================")
    for i, log_file in enumerate(log_files):
        size = os.path.getsize(os.path.join(logs_dir, log_file)) / 1024  # KB
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(logs_dir, log_file)))
        print(f"{i+1}. {log_file} - {size:.1f} KB - Last modified: {mtime}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='View Reagent Database application logs')
    parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to show (default: 50)')
    parser.add_argument('-g', '--grep', type=str, help='Filter logs to lines containing this text')
    parser.add_argument('-f', '--file', type=str, help='Specific log file to view (use "-l" to list available logs)')
    parser.add_argument('-l', '--list', action='store_true', help='List available log files')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_logs()
        return
    
    # Determine which log file to view
    log_file = None
    if args.file:
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        log_file = os.path.join(logs_dir, args.file)
    else:
        log_file = get_latest_log_file()
    
    # View the log
    view_log(log_file, args.lines, args.grep)

if __name__ == "__main__":
    main()
