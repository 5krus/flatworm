# Internal imports.
from core.git_manager import git_manager as gm
from core.file_monitor import monitor_directory
from gui.config_window import open_config_window

# External imports.
import json
import os
import logging

def load_config():
    config_path = 'config/config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    else:
        return {}

def main():
    # Load config or prompt for user to set config, to be able to push to correct repo.
    config = load_config()
    while not config:
        open_config_window(config)
        config = load_config()

    # Initialize git_manager with provided config, to be able to push to correct repo.
    git_manager = gm(
        config['repo_path'],
        config['branch'],
        config['exclude_patterns']
    ) 

    # Start directory monitoring to find changes.
    monitor_directory(config['repo_path'], git_manager)

if __name__ == "__main__":
    logging.info("Flatworm started.")
    main()