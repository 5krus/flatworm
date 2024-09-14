from git import Repo
import time
import logging

class git_manager:
    def __init__(self, repo_path, branch, exclude_patterns):
        self.repo_path = repo_path
        self.branch = branch
        self.exclude_patterns = exclude_patterns
        self.repo = Repo(repo_path)
        self.ensure_branch_exists()

    def ensure_branch_exists(self):
        # Check if the branch exists locally
        if self.branch not in self.repo.heads:
            logging.info(f"Branch '{self.branch}' does not exist locally. Creating it.")
            # Create the branch and switch to it
            self.repo.git.checkout('-b', self.branch)
        else:
            # Checkout to the branch
            self.repo.git.checkout(self.branch)

        # Check if the branch exists on the remote
        origin = self.repo.remote(name='origin')
        remote_branches = origin.refs
        if f'origin/{self.branch}' not in [ref.name for ref in remote_branches]:
            logging.info(f"Branch '{self.branch}' does not exist on the remote. Pushing it.")
            # Push the branch to the remote
            origin.push(self.branch)
        else:
            logging.info(f"Branch '{self.branch}' already exists on the remote.")

    def commit_and_push(self):
        try:
            self.repo.git.add(all=True)

            # Exclude specific patterns, but only if there are valid patterns
            if self.exclude_patterns:
                for pattern in self.exclude_patterns:
                    if pattern.strip():  # Check for non-empty patterns
                        # Check if there are files matching the pattern in the index
                        matching_files = self.repo.git.ls_files(pattern).splitlines()
                        if matching_files:  # Only attempt to remove if there are matches
                            self.repo.git.rm('-r', '--cached', pattern)
                        else:
                            logging.info(f"No files matching pattern '{pattern}' are tracked by git.")

            commit_message = f"Auto-commit on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            self.repo.index.commit(commit_message)
            origin = self.repo.remote(name='origin')
            # Ensure branch tracking is set correctly
            self.repo.git.push('--set-upstream', origin.name, self.branch)
            logging.info("Changes pushed successfully.")
        except Exception as e:
            logging.error(f"\nError in commit/push:\n{e}")