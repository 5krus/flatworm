# External imports.
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import logging

# Custom event handler for file system changes.
class ChangeHandler(FileSystemEventHandler):
    def __init__(self, git_manager):
        # Initialize with a reference to a git_manager instance.
        self.git_manager = git_manager

    # Called on any event (file creation, modification, deletion, or directory changes)
    def on_any_event(self, event):
        # Handle file events and directory rename/move events
        # 'event.is_directory' being True indicates a directory event
        # We want to ignore creation of directory events if the direcotry is empty.
        if event.is_directory and not event.event_type in ['moved', 'renamed', 'deleted']:
            return

        # Set a flag to schedule a commit.
        self.git_manager.schedule_commit = True

# Function to monitor a directory for changes. 
def monitor_directory(path, git_manager):
    # Create an event handler and pass the git_manager instance.
    event_handler = ChangeHandler(git_manager)

    # Create an Observer to watch for file system changes.
    observer = Observer()

    # Set up the observer to monitor the given path recursively.
    observer.schedule(event_handler, path, recursive=True)

    # Start the observer.
    observer.start()
    try:
        # Run indefinitely.
        while True:
            # Sleep for a short time to reduce CPU usage.
            time.sleep(1)

            # If a commit is scheduled, commit and push the changes.
            if git_manager.schedule_commit:
                git_manager.commit_and_push()

                # Reset the flag after committing.
                git_manager.schedule_commit = False
                logging.info("Changes found, committed and pushed.")

    except KeyboardInterrupt:
        # Stop the observer if a keyboard interrupt is received.
        observer.stop()

    # Wait for the observer to finish.
    observer.join()