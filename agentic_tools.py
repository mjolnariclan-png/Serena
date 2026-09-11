"""
Agentic Tools for Serena
This module provides safe, controlled tools that the agentic harness can use
to perform operations on the user's system.
"""

import os
import shutil
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys


class AgenticTools:
    """
    A collection of safe tools for agentic operations.
    All operations include safety checks and logging.
    """
    
    def __init__(self, base_path: str = None, safe_mode: bool = True):
        """
        Initialize agentic tools with safety constraints.
        
        Args:
            base_path: Base directory for file operations (defaults to current directory)
            safe_mode: If True, requires confirmation for dangerous operations
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.safe_mode = safe_mode
        self.operation_log = []
        
    def _log_operation(self, operation: str, details: str, success: bool = True):
        """Log an operation for audit trail."""
        log_entry = {
            "operation": operation,
            "details": details,
            "success": success,
            "timestamp": str(os.times())
        }
        self.operation_log.append(log_entry)
        print(f"[Agentic Log] {operation}: {details} - {'SUCCESS' if success else 'FAILED'}")
    
    # ==================== FILE OPERATIONS ====================
    
    def list_files(self, directory: str = None, pattern: str = "*") -> List[str]:
        """
        List files in a directory with optional pattern matching.
        
        Args:
            directory: Directory to list (defaults to base_path)
            pattern: Glob pattern for filtering (e.g., "*.txt", "*.py")
            
        Returns:
            List of file paths
        """
        try:
            target_dir = Path(directory) if directory else self.base_path
            if not target_dir.exists():
                self._log_operation("list_files", f"Directory not found: {target_dir}", False)
                return []
            
            files = list(target_dir.glob(pattern))
            file_list = [str(f) for f in files if f.is_file()]
            self._log_operation("list_files", f"Found {len(file_list)} files matching '{pattern}' in {target_dir}")
            return file_list
        except Exception as e:
            self._log_operation("list_files", f"Error: {str(e)}", False)
            return []
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read file contents safely.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File contents as string, or None if failed
        """
        try:
            target_file = Path(file_path)
            if not target_file.exists():
                self._log_operation("read_file", f"File not found: {target_file}", False)
                return None
            
            # Security check: don't read sensitive files
            sensitive_extensions = ['.pem', '.key', '.env', '.secret']
            if target_file.suffix.lower() in sensitive_extensions and self.safe_mode:
                self._log_operation("read_file", f"Blocked sensitive file: {target_file}", False)
                return None
            
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self._log_operation("read_file", f"Read {len(content)} characters from {target_file}")
            return content
        except Exception as e:
            self._log_operation("read_file", f"Error: {str(e)}", False)
            return None
    
    def write_file(self, file_path: str, content: str, create_dirs: bool = True) -> bool:
        """
        Write content to a file safely.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            create_dirs: Create parent directories if they don't exist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            target_file = Path(file_path)
            
            # Create parent directories if requested
            if create_dirs:
                target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_operation("write_file", f"Wrote {len(content)} characters to {target_file}")
            return True
        except Exception as e:
            self._log_operation("write_file", f"Error: {str(e)}", False)
            return False
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """
        Rename or move a file.
        
        Args:
            old_path: Current file path
            new_path: New file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            old_file = Path(old_path)
            new_file = Path(new_path)
            
            if not old_file.exists():
                self._log_operation("rename_file", f"Source file not found: {old_file}", False)
                return False
            
            old_file.rename(new_file)
            self._log_operation("rename_file", f"Renamed {old_file} to {new_file}")
            return True
        except Exception as e:
            self._log_operation("rename_file", f"Error: {str(e)}", False)
            return False
    
    def delete_file(self, file_path: str, require_confirmation: bool = True) -> Tuple[bool, str]:
        """
        Delete a file with safety checks.
        
        Args:
            file_path: Path to the file to delete
            require_confirmation: If True, this is a dangerous operation requiring approval
            
        Returns:
            Tuple of (success, message)
        """
        try:
            target_file = Path(file_path)
            
            if not target_file.exists():
                return False, f"File not found: {target_file}"
            
            if require_confirmation and self.safe_mode:
                return False, f"CONFIRMATION REQUIRED: Delete {target_file}? This operation requires user approval."
            
            target_file.unlink()
            self._log_operation("delete_file", f"Deleted {target_file}")
            return True, f"Successfully deleted {target_file}"
        except Exception as e:
            self._log_operation("delete_file", f"Error: {str(e)}", False)
            return False, f"Error deleting file: {str(e)}"
    
    def create_directory(self, dir_path: str) -> bool:
        """
        Create a directory.
        
        Args:
            dir_path: Path to the directory to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            target_dir = Path(dir_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            self._log_operation("create_directory", f"Created directory: {target_dir}")
            return True
        except Exception as e:
            self._log_operation("create_directory", f"Error: {str(e)}", False)
            return False
    
    def organize_files(self, source_dir: str = None, target_dir: str = "organized") -> str:
        """
        Organize files by extension into subdirectories.
        
        Args:
            source_dir: Directory to organize (defaults to base_path)
            target_dir: Target directory for organized files
            
        Returns:
            Summary of organization results
        """
        try:
            source = Path(source_dir) if source_dir else self.base_path
            target = Path(target_dir)
            
            if not source.exists():
                return f"Source directory not found: {source}"
            
            # Create target directory
            target.mkdir(parents=True, exist_ok=True)
            
            # Get all files
            files = [f for f in source.glob("*") if f.is_file()]
            organized_count = 0
            
            for file in files:
                # Skip if already in target
                if target in file.parents:
                    continue
                
                # Create extension-based subdirectory
                ext = file.suffix.lower().lstrip('.')
                if not ext:
                    ext = "no_extension"
                
                ext_dir = target / ext
                ext_dir.mkdir(exist_ok=True)
                
                # Move file
                new_path = ext_dir / file.name
                file.rename(new_path)
                organized_count += 1
            
            self._log_operation("organize_files", f"Organized {organized_count} files from {source} to {target}")
            return f"Organized {organized_count} files into {target}"
        except Exception as e:
            self._log_operation("organize_files", f"Error: {str(e)}", False)
            return f"Error organizing files: {str(e)}"
    
    # ==================== SYSTEM OPERATIONS ====================
    
    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Run a system command with timeout and safety checks.
        
        Args:
            command: Command to run
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Dangerous command check
            dangerous_commands = ['rm -rf', 'del /f', 'format', 'shutdown', 'reboot']
            if any(dangerous in command.lower() for dangerous in dangerous_commands) and self.safe_mode:
                self._log_operation("run_command", f"Blocked dangerous command: {command}", False)
                return False, "DANGEROUS COMMAND BLOCKED: This command requires explicit user approval."
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout if result.stdout else result.stderr
            success = result.returncode == 0
            
            self._log_operation("run_command", f"Executed: {command} (exit code: {result.returncode})", success)
            return success, output
        except subprocess.TimeoutExpired:
            self._log_operation("run_command", f"Command timed out: {command}", False)
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            self._log_operation("run_command", f"Error: {str(e)}", False)
            return False, f"Error running command: {str(e)}"
    
    def get_system_info(self) -> Dict:
        """
        Get basic system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            info = {
                "platform": sys.platform,
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
                "home_directory": str(Path.home()),
            }
            
            # Try to get additional info safely
            try:
                import psutil
                info["cpu_count"] = psutil.cpu_count()
                info["memory_total"] = f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
            except ImportError:
                pass
            
            self._log_operation("get_system_info", "Retrieved system information")
            return info
        except Exception as e:
            self._log_operation("get_system_info", f"Error: {str(e)}", False)
            return {"error": str(e)}
    
    # ==================== WEB OPERATIONS ====================
    
    def web_search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform a web search (requires web_search module).
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search result dictionaries
        """
        try:
            from web_search import search_web
            results = search_web(query)
            self._log_operation("web_search", f"Search completed for: {query}")
            return results
        except ImportError:
            self._log_operation("web_search", "Web search module not available", False)
            return []
        except Exception as e:
            self._log_operation("web_search", f"Error: {str(e)}", False)
            return []
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def get_operation_log(self) -> List[Dict]:
        """Get the operation log for audit purposes."""
        return self.operation_log
    
    def clear_operation_log(self):
        """Clear the operation log."""
        self.operation_log = []
        self._log_operation("clear_operation_log", "Operation log cleared")


# Global instance for easy access
_agentic_tools = None

def get_agentic_tools(base_path: str = None, safe_mode: bool = True) -> AgenticTools:
    """Get or create the global AgenticTools instance."""
    global _agentic_tools
    if _agentic_tools is None:
        _agentic_tools = AgenticTools(base_path, safe_mode)
    return _agentic_tools


if __name__ == "__main__":
    # Test the agentic tools
    print("Testing Agentic Tools...")
    
    tools = AgenticTools(safe_mode=True)
    
    # Test file operations
    print("\n=== File Operations ===")
    files = tools.list_files(pattern="*.py")
    print(f"Found {len(files)} Python files")
    
    # Test system info
    print("\n=== System Info ===")
    info = tools.get_system_info()
    print(json.dumps(info, indent=2))
    
    # Test safe command
    print("\n=== Safe Command ===")
    success, output = tools.run_command("echo 'Hello from agentic tools'")
    print(f"Success: {success}, Output: {output}")
    
    # Test dangerous command blocking
    print("\n=== Dangerous Command Blocking ===")
    success, output = tools.run_command("rm -rf /")
    print(f"Success: {success}, Output: {output}")
    
    # Show operation log
    print("\n=== Operation Log ===")
    for entry in tools.get_operation_log():
        print(f"{entry['operation']}: {entry['details']} - {'SUCCESS' if entry['success'] else 'FAILED'}")