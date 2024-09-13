import json
import os
from core.git_manager import GitManager  # Correctly import GitManager
from core.file_monitor import monitor_directory
from gui.config_window import open_config_window
import logging

def load_config():
    config_path = 'config/config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    else:
        return {}

def main():
    # Load or prompt for configuration
    config = load_config()
    if not config:
        open_config_window(config)
        config = load_config()

    # Initialize GitManager with the config
    git_manager = GitManager(
        config['repo_path'],
        config['branch'],
        config['exclude_patterns']
    )

    # Start directory monitoring
    monitor_directory(config['repo_path'], git_manager)

if __name__ == "__main__":
    logging.info("Auto Git started.")
    main()