import os
import json
import datetime
import uuid
from typing import Dict, Any
import logging

try:
    import git
    HAS_GIT_PYTHON = True
except ImportError:
    HAS_GIT_PYTHON = False

class GitAuditLogger:
    """
    Sovereign Write-Adapter.
    Writes audit logs to a local file and immediately commits them to a local Git repository.
    Enforces the "Git-as-Backend" architecture.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.log_dir = os.path.join(repo_path, "audit_logs")
        self.logger = logging.getLogger("sovereign_git_logger")
        
        # Ensure log directory exists
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except OSError as e:
            print(f"Server Warning: Could not create audit log directory {self.log_dir}: {e}")

        # Initialize or Connect to Git Repo
        if HAS_GIT_PYTHON:
            try:
                try:
                    self.repo = git.Repo(self.repo_path)
                except git.exc.InvalidGitRepositoryError:
                    print(f"Notice: {repo_path} is not a valid git repo. logs will be written but not committed until `git init` is run.")
                    self.repo = None
            except Exception as e:
                 print(f"Git Initialization Warning: {e}")
                 self.repo = None
        else:
            print("Warning: `GitPython` not installed. Git features disabled. Logs will only be written to disk.")
            self.repo = None

    def write_entry(self, entry: Dict[str, Any]) -> str:
        """
        Writes a single log entry to the daily log file and commits it.
        Returns the Git Commit Hash (or None if git failed).
        """
        
        # 1. Determine File Path (Daily Rotation)
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        filename = f"audit_{today}.jsonl"
        filepath = os.path.join(self.log_dir, filename)
        
        # 2. Append to File
        try:
            with open(filepath, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"CRITICAL: Failed to write to audit log file: {e}")
            return None

        # 3. Git Commit
        commit_hash = None
        if self.repo:
            try:
                # Add the specific file
                self.repo.index.add([filepath])
                
                # Commit with metadata
                event_id = entry.get("event_id", "unknown")
                outcome = entry.get("outcome", "unknown")
                msg = f"Audit: {outcome} [Event: {event_id}]"
                
                commit = self.repo.index.commit(msg)
                commit_hash = commit.hexsha
                
            except Exception as e:
                print(f"Git Commit Failed: {e}")
                
        return commit_hash
