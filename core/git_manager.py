from git import Repo
import time
import logging
import os

class git_manager:
    def __init__(self, repo_path, branch, exclude_patterns):
        """
        Standard Initialisation.
        """

        # Initialize git_manager with provided config details.
        self.repo_path = repo_path
        self.branch = branch
        self.exclude_patterns = exclude_patterns
        self.repo = Repo(repo_path)

        # Set a flag to schedule a commit as false by default to avoid empty commits.
        self.schedule_commit = False
        self.ensure_branch_exists()

    def ensure_branch_exists(self):
        """
        Check whether desired auto-commit branch exists locally (create if not), and switch to it.
        Also, check whether the desired auto-commit branch exists on the remote (create it if not)

        Parameters
        ----------
        None : As the branch and repo are already known, this function requires no further inputs.

        Returns
        -------
        None : This functon creates the branches locally and remotely if needed; nothing to return.
        """

        # Ensure we're on the correct branch for auto-commiting purposes.
        if self.repo.active_branch.name != self.branch:

            # Check if the branch exists locally; create it if not.
            if self.branch not in self.repo.heads:

                # Create the branch and switching to it for auto-commit to proceed.
                logging.info(f"Branch '{self.branch}' does not exist locally. Creating it.")
                self.repo.git.checkout('-b', self.branch)

            else:

                # Checkout to the branch as it exists locally, for auto-commit to proceed.
                self.repo.git.checkout(self.branch)

            # Log successful switch to specified auto-commit branch for future debugging.
            logging.info(f"Switched to '{self.branch}' branch.")

        # A branch can exist locally while not existing remotely, so it is useful to ensure that it
        # exists on the remote as well. Thus, this check ensures that it does.
        origin = self.repo.remote(name='origin')
        remote_branches = [ref.remote_head for ref in origin.refs]
        if self.branch not in remote_branches:

            # Push the branch to the remote to ensure local and remote environments are compatible.
            logging.info(f"Branch '{self.branch}' does not exist on the remote. Pushing it.")
            origin.push(self.branch)

        else:
            logging.info(f"Branch '{self.branch}' exists on the remote.")

    def commit_and_push(self):
        """
        Commits and pushes changes to the specified auto-save branch.

        If uncommitted changes are found, this function performs the following steps:
        1. Creates a temporary commit on the current branch to capture these changes.
        2. Switches to the specified auto-save branch and updates it with remote changes.
        3. Cherry-picks the temporary commit onto it.
        4. Excludes files matching specified patterns (e.g., '*.log') from the commit.
        5. Commits and pushes the changes to the remote repository on the auto-save branch.
        6. Switches back to the original branch.
        7. Resets the original branch to remove the temporary commit, restoring the uncommitted
           changes to their prior state.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        try:
            # Save current branch name to be able to return to it after auto-committing.
            current_branch = self.repo.active_branch.name

            # Check for uncommitted changes.
            if self.repo.is_dirty(untracked_files=True):
                logging.info("Uncommitted changes detected.")

                # Stage all changes to store and later commit them.
                self.repo.git.add(A=True)

                # Create a temporary commit on the current branch.
                temp_commit = self.repo.index.commit("Temporary commit for auto-save.")

                # Switch to the provided auto-save branch to make changes to it.
                self.repo.git.checkout(self.branch)

                # Pull latest changes from the remote auto-save branch.
                try:
                    self.repo.git.pull('origin', self.branch, '--rebase')
                    logging.info(f"Pulled latest changes from remote branch '{self.branch}'.")
                except Exception as pull_error:
                    logging.error(f"Error pulling remote changes: {pull_error}")
                    # Handle pull errors if necessary.

                # Cherry-pick the temporary commit onto the provided auto-save branch.
                try:
                    self.repo.git.cherry_pick(temp_commit.hexsha)
                except Exception as cherry_pick_error:
                    error_message = str(cherry_pick_error)
                    if "The previous cherry-pick is now empty" in error_message:
                        # Cherry-pick resulted in an empty commit; skip it.
                        logging.info("Cherry-pick resulted in an empty commit. Skipping.")
                        self.repo.git.cherry_pick('--skip')
                    else:
                        # Abort the cherry-pick if there was an error.
                        logging.error(f"Cherry-pick failed: {cherry_pick_error}")
                        self.repo.git.cherry_pick('--abort')
                        # Switch back to the original branch.
                        self.repo.git.checkout(current_branch)
                        # Reset the temporary commit.
                        self.repo.git.reset('HEAD~1')
                        logging.info("Restored uncommitted changes on the original branch " +
                                     "after cherry-pick failure.")
                        return  # Exit the method to avoid further errors.

                # Exclude specific file patterns (e.g., "*.log"), if any.
                if self.exclude_patterns:
                    for pattern in self.exclude_patterns:
                        if pattern.strip():
                            matching_files = self.repo.git.ls_files(pattern).splitlines()
                            if matching_files:
                                self.repo.git.rm('-r', '--cached', pattern)
                            else:
                                logging.info(f"No files matching pattern '{pattern}' are tracked.")

                # Commit the changes onto the provided auto-save branch.
                commit_message = f"Auto-commit on {time.strftime('%Y-%m-%d %H:%M:%S')}."
                self.repo.index.commit(commit_message)

                # Push to remote.
                origin = self.repo.remote(name='origin')
                try:
                    self.repo.git.push('--set-upstream', origin.name, self.branch)
                    logging.info(f"Auto-committed changes to {self.branch}.")
                except Exception as push_error:
                    logging.error(f"Error pushing to remote: {push_error}")
                    # Handle push errors if necessary.
                    # You might want to pull again or abort. 

                # Switch back to the original branch to restore its prior state.
                self.repo.git.checkout(current_branch)

                # Reset the temporary commit to restore uncommitted changes.
                self.repo.git.reset('HEAD~1')
                logging.info("Restored uncommitted changes on the original branch.")
                logging.info(f"## Changes found, committed, and pushed.")

        except Exception as e:
            logging.error(f"\nError in commit/push:\n{e}")