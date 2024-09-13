from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import logging

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, git_manager):
        self.git_manager = git_manager

    def on_any_event(self, event):
        if event.is_directory:
            return
        self.git_manager.schedule_commit = True

def monitor_directory(path, git_manager):
    event_handler = ChangeHandler(git_manager)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
            if git_manager.schedule_commit:
                git_manager.commit_and_push()
                git_manager.schedule_commit = False
    except KeyboardInterrupt:
        observer.stop()
    observer.join()