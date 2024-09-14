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
                print(f"Branch '{self.branch}' does not exist locally...\n" +
                             f"Creating it at {time.strftime('%Y-%m-%d %H:%M:%S')}.")
                self.repo.git.checkout('-b', self.branch)

            else:

                # Checkout to the branch as it exists locally, for auto-commit to proceed.
                self.repo.git.checkout(self.branch)

            # Log successful switch to specified auto-commit branch for future debugging.
            print(f"Switched to '{self.branch}' branch at " +
                         f"{time.strftime('%Y-%m-%d %H:%M:%S')}.")

        # A branch can exist locally while not existing remotely, so it is useful to ensure that it
        # exists on the remote as well. Thus, this check ensures that it does.
        origin = self.repo.remote(name='origin')
        remote_branches = [ref.remote_head for ref in origin.refs]
        if self.branch not in remote_branches:

            # Push the branch to the remote to ensure local and remote environments are compatible.
            print(f"Branch '{self.branch}' does not exist on the remote...\n" +
                         f"Pushing it at {time.strftime('%Y-%m-%d %H:%M:%S')}.")
            origin.push(self.branch)

        else:
            print(f"Branch '{self.branch}' exists on the remote.")

    def commit_and_push(self):
        """
        Commits and pushes changes to the specified auto-save branch.

        If uncommitted changes are found, this function performs the following steps:
        1. Creates a temporary commit on the current branch to capture these changes.
        2. Switches to the specified auto-save branch and cherry-picks the temporary commit onto it.
        3. Excludes files matching specified patterns (e.g., '*.log') from the commit.
        4. Commits and pushes the changes to the remote repository on the auto-save branch.
        5. Switches back to the original branch.
        6. Resets the original branch to remove the temporary commit, restoring the uncommitted
           changes to their prior state.

        Parameters
        ----------
        None : As the branch and repo are already known, this function requires no further inputs.

        Returns
        -------
        None : Commits are made to remote repository; there is nothing to return.
        """

        try:
            # Save current branch name to be able to return to it after auto-commting.
            current_branch = self.repo.active_branch.name

            # Check for uncommitted changes.
            if self.repo.is_dirty(untracked_files=True):
                print("Uncommitted changes detected.")

                print("test 1")

                # Stage all changes to store and later commit them.
                self.repo.git.add(A=True)

                print("test 2")

                # Create a temporary commit on the current branch such that it can be returned to
                # later after auto-commiting to provided personal branch.
                temp_commit = self.repo.index.commit("Temporary commit for auto-save.")

                print("test 3")

                # Switch to the provided auto-save branch to make changes to it.
                self.repo.git.checkout(self.branch)

                print("test 4")

                # Cherry-pick the temporary commit onto provided auto-save branch.
                self.repo.git.cherry_pick(temp_commit.hexsha)

                print("test 5")

                # Exclude specific file patterns (e.g. "*.log"), if any.
                if self.exclude_patterns:
                    for pattern in self.exclude_patterns:
                        if pattern.strip():
                            matching_files = self.repo.git.ls_files(pattern).splitlines()
                            if matching_files:
                                self.repo.git.rm('-r', '--cached', pattern)
                            else:
                                print(f"No files matching pattern '{pattern}' are tracked.")

                print("test 6")

                # Commit the changes onto the provided auto-save branch.
                commit_message = f"Auto-commit on {time.strftime('%Y-%m-%d %H:%M:%S')}."
                self.repo.index.commit(commit_message)

                print("test 7")

                # Push to remote.
                origin = self.repo.remote(name='origin')
                self.repo.git.push('--set-upstream', origin.name, self.branch)
                print(f"Auto-commited changes to {self.branch} at " +
                             f"{time.strftime('%Y-%m-%d %H:%M:%S')}.")

                # Switch back to the original branch to restore its prior state.
                self.repo.git.checkout(current_branch)

                # Reset the temporary commit to restore uncommitted changes.
                self.repo.git.reset('HEAD~1')
                print("Restored uncommitted changes on the original branch.")

            else:
                print("No uncommitted changes to commit.")

        except Exception as e:
            logging.error(f"\nError in commit/push:\n{e}")