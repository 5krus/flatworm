# Internal imports.
from core.git_manager import git_manager as gm
from core.file_monitor import monitor_directory
from gui.config_window import open_config_window

# External imports.
import json
import os
import logging
import time

if __name__ == "__main__":
    """
    Standard Initialisation.
    """

    # Start Flatworm and log startup information.
    print(f"Flatworm started at {time.strftime('%Y-%m-%d %H:%M:%S')}.")
    main()

def main():
    """
    Load configuration settings for repository and relevant auto-save branch such that files will be
    auto-commited to the correct part of the user codebase ( / repository ).

    Parameters
    ----------
    None : This function reads from a hard-coded file path, so no inputs are necessary.

    Returns
    -------
    None : This function saves the trained model to file, so no return is necessary.
    """

    # Load config or prompt for user to set config, to be able to push to correct repository and
    # branch set later.
    config = load_config()
    while not config: 
        open_config_window(config) 
        config = load_config() 

    # Initialize git_manager with provided config, to be able to push to correct repository and
    # branch set later.
    git_manager = gm(
        config['repo_path'],
        config['branch'],
        config['exclude_patterns']
    ) 

    # Start directory monitoring to find changes.
    monitor_directory(config['repo_path'], git_manager)

def load_config():
    """
    Load configuration settings for repository and relevant auto-save branch such that files will be
    auto-commited to the correct part of the user codebase ( / repository ).

    Parameters
    ----------
    None : This function reads from a hard-coded file path, so no inputs are necessary.

    Returns
    -------
    JSON : This function returns the obtained config file details, if they are found.
    None : This function returns nothing if the config file is not found.
    """

    # Obtain config details from file, after checking if file exists to avoid unnecessary errors.
    config_path = 'config/config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    else:
        return {}

def configure_logging():
    # Configure the logging system
    logging.basicConfig(
        level=logging.INFO,  # Set the log level
        format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.FileHandler('flatworm.log'),  # Log to a file
            logging.StreamHandler()  # Log to the console
        ]
    )
