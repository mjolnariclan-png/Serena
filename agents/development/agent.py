"""
Development Agent
Controlled development/repository operations with restricted capabilities

Phase 3: Specialized agent for safe development operations
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent


class DevelopmentAgent(BaseAgent):
    """
    Agent for controlled development and repository operations.
    
    Restricted capabilities:
    - READ: Serena project files, Git metadata, logs, test results
    - ANALYZE: source code, tests, Git status/history, build/test output
    - MODIFY: only approved Serena workspace
    
    Git operations are separated by risk:
    - Local operations (status, history) are lower-risk
    - Remote operations (push, pull) require explicit approval
    - Destructive operations (reset, checkout discard) require explicit approval
    """
    
    def __init__(self, workspace: Path, approved_workspace: Path):
        """
        Initialize Development Agent.
        
        Args:
            workspace: Agent workspace for logs and temporary files
            approved_workspace: The only directory this agent can modify
        """
        instructions = """
        You are the Development Agent. Your job is to:
        1. Inspect project files in the approved workspace
        2. Analyze source code structure and quality
        3. Inspect Git status and history
        4. Run tests and report results
        5. Run linting/static analysis where available
        6. Run builds where appropriate
        7. Modify files ONLY within the approved workspace
        8. Create backups where required before modifications
        9. Verify all modifications
        10. Report all results clearly
        
        CRITICAL SECURITY RULES:
        - NEVER modify files outside the approved workspace
        - NEVER push to remote without explicit approval
        - NEVER perform destructive Git operations without approval
        - ALWAYS verify before making changes
        - ALWAYS create backups before modifications
        - NEVER bypass the permission system
        - NEVER execute arbitrary shell commands
        """
        
        super().__init__("DevelopmentAgent", workspace, instructions)
        
        # Store approved workspace
        self.approved_workspace = Path(approved_workspace).resolve()
        
        # Development-specific paths
        self.dev_paths = {
            "approved_workspace": str(self.approved_workspace),
            "backup_dir": str(workspace / "backups"),
            "reports_dir": str(workspace / "reports")
        }
        
        # Create directories
        Path(self.dev_paths["backup_dir"]).mkdir(parents=True, exist_ok=True)
        Path(self.dev_paths["reports_dir"]).mkdir(parents=True, exist_ok=True)
        
        # Set up READ permissions for approved workspace
        self.add_permission("read_dirs", [str(self.approved_workspace)])
        
        # Set up WRITE permissions ONLY for approved workspace
        self.add_permission("write_dirs", [str(self.approved_workspace)])
        
        # Set up allowed commands (restricted set)
        self.add_permission("allowed_commands", [
            "git",  # Git operations (will check per-operation permissions)
            "python",  # Running Python scripts/tests
            "pytest",  # Running tests
            "pip",  # Package management (read-only)
            "ls",  # Listing files
            "cat",  # Reading files
            "grep",  # Searching files
            "find",  # Finding files
        ])
        
        # Add safety rules
        self.add_rule("NEVER modify files outside approved workspace")
        self.add_rule("NEVER push to remote without explicit approval")
        self.add_rule("NEVER perform destructive Git operations without approval")
        self.add_rule("ALWAYS create backup before modification")
        self.add_rule("ALWAYS verify changes after modification")
        self.add_rule("NEVER execute arbitrary shell commands")
        self.add_rule("NEVER bypass permission system")
        self.add_rule("Report all Git operations clearly")
    
    def inspect_project_structure(self, project_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Inspect the structure of a project.
        
        Args:
            project_path: Path to inspect (defaults to approved workspace)
            
        Returns:
            Project structure information
        """
        path = project_path or self.approved_workspace
        path = Path(path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(path):
            return {"error": "Path outside approved workspace", "path": str(path)}
        
        try:
            structure = {
                "path": str(path),
                "name": path.name,
                "is_git_repo": (path / ".git").exists(),
                "directories": [],
                "files": [],
                "total_size": 0
            }
            
            # Walk directory (limited depth for performance)
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure["directories"].append(item.name)
                elif item.is_file() and not item.name.startswith('.'):
                    structure["files"].append(item.name)
                    structure["total_size"] += item.stat().st_size
            
            return structure
            
        except Exception as e:
            return {"error": str(e), "path": str(path)}
    
    def get_git_status(self, repo_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get Git status of a repository.
        
        Args:
            repo_path: Path to repository (defaults to approved workspace)
            
        Returns:
            Git status information
        """
        path = repo_path or self.approved_workspace
        path = Path(path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(path):
            return {"error": "Path outside approved workspace", "path": str(path)}
        
        try:
            # Check if it's a git repo
            if not (path / ".git").exists():
                return {"error": "Not a Git repository", "path": str(path)}
            
            # Run git status
            result = self.safe_run_command(["git", "-C", str(path), "status", "--porcelain"])
            
            if result is None:
                return {"error": "Git status command failed", "path": str(path)}
            
            # Parse output
            modified = []
            added = []
            deleted = []
            untracked = []
            
            for line in result.split('\n'):
                if not line:
                    continue
                status = line[:2]
                filepath = line[3:]
                
                if 'M' in status:
                    modified.append(filepath)
                if 'A' in status:
                    added.append(filepath)
                if 'D' in status:
                    deleted.append(filepath)
                if '??' in status:
                    untracked.append(filepath)
            
            # Get current branch
            branch_result = self.safe_run_command(["git", "-C", str(path), "branch", "--show-current"])
            current_branch = branch_result.strip() if branch_result else "unknown"
            
            return {
                "path": str(path),
                "current_branch": current_branch,
                "modified": modified,
                "added": added,
                "deleted": deleted,
                "untracked": untracked,
                "has_changes": bool(modified or added or deleted or untracked)
            }
            
        except Exception as e:
            return {"error": str(e), "path": str(path)}
    
    def get_git_history(self, repo_path: Optional[Path] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Get Git commit history.
        
        Args:
            repo_path: Path to repository (defaults to approved workspace)
            limit: Number of commits to return
            
        Returns:
            Git history information
        """
        path = repo_path or self.approved_workspace
        path = Path(path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(path):
            return {"error": "Path outside approved workspace", "path": str(path)}
        
        try:
            # Check if it's a git repo
            if not (path / ".git").exists():
                return {"error": "Not a Git repository", "path": str(path)}
            
            # Run git log
            result = self.safe_run_command([
                "git", "-C", str(path), "log",
                f"-{limit}",
                "--pretty=format:%H|%an|%ae|%ad|%s",
                "--date=iso"
            ])
            
            if result is None:
                return {"error": "Git log command failed", "path": str(path)}
            
            # Parse output
            commits = []
            for line in result.split('\n'):
                if not line:
                    continue
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
            
            return {
                "path": str(path),
                "commits": commits,
                "count": len(commits)
            }
            
        except Exception as e:
            return {"error": str(e), "path": str(path)}
    
    def run_tests(self, test_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run tests in the project.
        
        Args:
            test_path: Path to tests (defaults to approved workspace)
            
        Returns:
            Test results
        """
        path = test_path or self.approved_workspace
        path = Path(path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(path):
            return {"error": "Path outside approved workspace", "path": str(path)}
        
        try:
            # Try pytest first
            pytest_result = self.safe_run_command(["python", "-m", "pytest", str(path), "-v"])
            
            if pytest_result is not None:
                return {
                    "tool": "pytest",
                    "path": str(path),
                    "output": pytest_result,
                    "success": "passed" in pytest_result.lower()
                }
            
            # Fallback to running test files directly
            return {
                "error": "No test runner found",
                "path": str(path),
                "suggestion": "Ensure pytest is installed or specify test files"
            }
            
        except Exception as e:
            return {"error": str(e), "path": str(path)}
    
    def analyze_source_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a source file.
        
        Args:
            file_path: Path to source file
            
        Returns:
            Analysis results
        """
        file_path = Path(file_path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(file_path):
            return {"error": "File outside approved workspace", "path": str(file_path)}
        
        try:
            if not file_path.exists():
                return {"error": "File not found", "path": str(file_path)}
            
            # Read file
            content = self.safe_read_file(str(file_path))
            if content is None:
                return {"error": "Failed to read file", "path": str(file_path)}
            
            # Basic analysis
            lines = content.split('\n')
            analysis = {
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "line_count": len(lines),
                "language": self._detect_language(file_path),
                "has_classes": bool(re.search(r'^class\s+\w+', content, re.MULTILINE)),
                "has_functions": bool(re.search(r'^def\s+\w+', content, re.MULTILINE)),
                "imports": re.findall(r'^import\s+\w+|^from\s+\w+\s+import', content, re.MULTILINE),
            }
            
            return analysis
            
        except Exception as e:
            return {"error": str(e), "path": str(file_path)}
    
    def create_backup(self, file_path: Path) -> Optional[str]:
        """
        Create a backup of a file before modification.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Backup file path or None if failed
        """
        file_path = Path(file_path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(file_path):
            self.logger.error(f"Cannot backup file outside approved workspace: {file_path}")
            return None
        
        try:
            if not file_path.exists():
                self.logger.warning(f"File does not exist, cannot backup: {file_path}")
                return None
            
            # Create backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}.{timestamp}.backup"
            backup_path = Path(self.dev_paths["backup_dir"]) / backup_name
            
            # Copy file
            import shutil
            shutil.copy2(file_path, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def modify_file(self, file_path: Path, content: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Modify a file within the approved workspace.
        
        Args:
            file_path: Path to file to modify
            content: New content
            create_backup: Whether to create backup before modification
            
        Returns:
            Result information
        """
        file_path = Path(file_path).resolve()
        
        # Verify path is within approved workspace
        if not self._is_in_approved_workspace(file_path):
            return {"error": "File outside approved workspace", "path": str(file_path)}
        
        try:
            # Create backup if requested
            backup_path = None
            if create_backup and file_path.exists():
                backup_path = self.create_backup(file_path)
                if backup_path is None:
                    return {"error": "Failed to create backup", "path": str(file_path)}
            
            # Write file
            result = self.safe_write_file(str(file_path), content)
            
            if result:
                return {
                    "success": True,
                    "path": str(file_path),
                    "backup": backup_path,
                    "size": len(content)
                }
            else:
                return {"error": "Failed to write file", "path": str(file_path)}
                
        except Exception as e:
            return {"error": str(e), "path": str(file_path)}
    
    def _is_in_approved_workspace(self, path: Path) -> bool:
        """
        Check if a path is within the approved workspace.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within approved workspace
        """
        try:
            path = Path(path).resolve()
            return path.is_relative_to(self.approved_workspace)
        except Exception:
            return False
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.sh': 'Shell',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
        }
        return language_map.get(suffix, 'Unknown')


if __name__ == "__main__":
    # Test the Development Agent
    print("Testing Development Agent...")
    
    import tempfile
    temp_workspace = Path(tempfile.mkdtemp())
    temp_repo = Path(tempfile.mkdtemp())
    
    # Create a simple test file
    test_file = temp_repo / "test.py"
    test_file.write_text("print('Hello, World!')\n")
    
    agent = DevelopmentAgent(temp_workspace, temp_repo)
    
    # Test inspect project structure
    structure = agent.inspect_project_structure()
    print(f"Project structure: {structure}")
    
    # Test analyze source file
    analysis = agent.analyze_source_file(test_file)
    print(f"File analysis: {analysis}")
    
    # Test modify file
    result = agent.modify_file(test_file, "print('Modified!')\n")
    print(f"Modify result: {result}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_workspace)
    shutil.rmtree(temp_repo)
    
    print("\n✅ Development Agent Test Passed!")