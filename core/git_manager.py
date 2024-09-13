from git import Repo
import time
import logging

class GitManager:
    def __init__(self, repo_path, branch, exclude_patterns):
        self.repo_path = repo_path
        self.branch = branch
        self.exclude_patterns = exclude_patterns
        self.repo = Repo(repo_path)

    def commit_and_push(self):
        try:
            self.repo.git.add(all=True)

            # Exclude specific patterns, but only if there are valid patterns
            if self.exclude_patterns:
                for pattern in self.exclude_patterns:
                    if pattern.strip():  # Check for non-empty patterns
                        self.repo.git.rm('-r', '--cached', pattern)

            commit_message = f"Auto-commit on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            self.repo.index.commit(commit_message)
            origin = self.repo.remote(name='origin')
            origin.push(self.branch)
            logging.info("Changes pushed successfully.")
        except Exception as e:
            logging.error(f"Error in commit/push: {e}")