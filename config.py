"""
Configuration file for the Reagent Database application
Allows the database to be stored on OneDrive or other cloud storage locations
"""

import os
import json
import platform
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    # Default local database path (relative to the application directory)
    'db_path': 'reagent_db.sqlite',
    
    # OneDrive integration settings
    'use_onedrive': False,
    'onedrive_path': '',
    
    # Application settings
    'debug': True,
    'port': 5000
}

# Path to the configuration file
CONFIG_FILE = 'app_config.json'

def get_onedrive_path():
    """
    Automatically detect OneDrive path based on the operating system
    Returns None if OneDrive cannot be detected
    """
    system = platform.system()
    home = str(Path.home())
    
    if system == 'Windows':
        # Common OneDrive paths on Windows
        onedrive_paths = [
            os.path.join(home, 'OneDrive'),
            os.path.join(home, 'OneDrive - Company Name')  # Adjust for your organization
        ]
    elif system == 'Darwin':  # macOS
        onedrive_paths = [
            os.path.join(home, 'OneDrive'),
            os.path.join(home, 'Library', 'CloudStorage', 'OneDrive-Personal'),
            os.path.join(home, 'Library', 'Mobile Documents', 'com~apple~CloudDocs', 'OneDrive'),
            os.path.join(home, 'Library', 'CloudStorage', 'OneDrive-Business')
        ]
    elif system == 'Linux':
        onedrive_paths = [
            os.path.join(home, 'OneDrive')
        ]
    else:
        return None
    
    # Return the first valid OneDrive path
    for path in onedrive_paths:
        if os.path.exists(path) and os.path.isdir(path):
            return path
    
    return None

def load_config():
    """Load configuration from file or create default if not exists"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, CONFIG_FILE)
    
    # If config file exists, load it
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Ensure all required keys are present
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        # Create default config
        config = DEFAULT_CONFIG.copy()
        
        # Try to detect OneDrive path
        onedrive_path = get_onedrive_path()
        if onedrive_path:
            config['onedrive_path'] = onedrive_path
        
        # Save the default configuration
        save_config(config)
        return config

def save_config(config):
    """Save configuration to file"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, CONFIG_FILE)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_db_path():
    """Get the database path based on configuration"""
    config = load_config()
    
    if config['use_onedrive'] and config['onedrive_path']:
        # Use OneDrive path
        db_dir = os.path.join(config['onedrive_path'], 'ReagentDB')
        
        # Ensure the directory exists
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
            except Exception as e:
                print(f"Error creating directory in OneDrive: {e}")
                # Fall back to local database
                return os.path.join(os.path.dirname(os.path.abspath(__file__)), config['db_path'])
        
        return os.path.join(db_dir, 'reagent_db.sqlite')
    else:
        # Use local database
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), config['db_path'])
