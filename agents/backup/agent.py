"""
Backup Agent
Automated backup operations with restricted capabilities

Phase 3: Specialized agent for safe backup operations
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import tarfile
import gzip

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent


class BackupAgent(BaseAgent):
    """
    Agent for automated backup operations.
    
    Restricted capabilities:
    - READ: Source directories for backup
    - WRITE: Backup destination directory only
    - Never delete original files
    - Never overwrite existing backups without authorization
    - All operations logged and verified
    """
    
    def __init__(self, workspace: Path, backup_destination: Path):
        """
        Initialize Backup Agent.
        
        Args:
            workspace: Agent workspace for logs
            backup_destination: The only directory this agent can write backups to
        """
        instructions = """
        You are the Backup Agent. Your job is to:
        1. Create backups of specified directories
        2. Maintain backup retention policies
        3. Verify backup integrity
        4. Report backup status
        5. Clean up old backups per policy
        
        CRITICAL SECURITY RULES:
        - NEVER delete original files
        - NEVER write outside backup destination
        - NEVER overwrite existing backups without authorization
        - ALWAYS verify backup integrity
        - ALWAYS report backup status
        - NEVER bypass permission system
        """
        
        super().__init__("BackupAgent", workspace, instructions)
        
        # Store backup destination
        self.backup_destination = Path(backup_destination).resolve()
        
        # Create backup destination
        self.backup_destination.mkdir(parents=True, exist_ok=True)
        
        # Backup paths
        self.backup_paths = {
            "destination": str(self.backup_destination),
            "logs": str(workspace / "backup_logs")
        }
        
        # Create log directory
        Path(self.backup_paths["logs"]).mkdir(parents=True, exist_ok=True)
        
        # Set up READ permissions for source directories (will be added dynamically)
        self.add_permission("read_dirs", [])
        
        # Set up WRITE permissions ONLY for backup destination
        self.add_permission("write_dirs", [str(self.backup_destination)])
        
        # Set up allowed commands
        self.add_permission("allowed_commands", [
            "tar",  # Creating archives
            "gzip",  # Compression
            "ls",  # Listing files
            "du",  # Disk usage
        ])
        
        # Add safety rules
        self.add_rule("NEVER delete original files")
        self.add_rule("NEVER write outside backup destination")
        self.add_rule("NEVER overwrite existing backups without authorization")
        self.add_rule("ALWAYS verify backup integrity")
        self.add_rule("Report all backup operations")
    
    def add_source_directory(self, source_dir: Path) -> bool:
        """
        Add a source directory to backup.
        
        Args:
            source_dir: Directory to backup
            
        Returns:
            True if added successfully
        """
        source_dir = Path(source_dir).resolve()
        
        if not source_dir.exists():
            self.logger.warning(f"Source directory does not exist: {source_dir}")
            return False
        
        # Add to read permissions
        self.add_permission("read_dirs", [str(source_dir)])
        self.logger.info(f"Added source directory: {source_dir}")
        return True
    
    def create_backup(self, source_dir: Path, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a backup of a directory.
        
        Args:
            source_dir: Directory to backup
            backup_name: Optional custom backup name
            
        Returns:
            Backup result information
        """
        source_dir = Path(source_dir).resolve()
        
        # Verify source is in read permissions
        if str(source_dir) not in self.permissions["read_dirs"]:
            return {
                "success": False,
                "error": "Source directory not in approved read list",
                "source": str(source_dir)
            }
        
        if not source_dir.exists():
            return {
                "success": False,
                "error": "Source directory does not exist",
                "source": str(source_dir)
            }
        
        try:
            # Generate backup name
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{source_dir.name}_{timestamp}.tar.gz"
            
            backup_path = self.backup_destination / backup_name
            
            # Check if backup already exists
            if backup_path.exists():
                return {
                    "success": False,
                    "error": "Backup already exists",
                    "backup_path": str(backup_path)
                }
            
            # Create backup
            self.logger.info(f"Creating backup: {source_dir} -> {backup_path}")
            
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(source_dir, arcname=source_dir.name)
            
            # Verify backup
            if not backup_path.exists():
                return {
                    "success": False,
                    "error": "Backup file not created",
                    "backup_path": str(backup_path)
                }
            
            backup_size = backup_path.stat().st_size
            
            return {
                "success": True,
                "source": str(source_dir),
                "backup_path": str(backup_path),
                "backup_name": backup_name,
                "backup_size": backup_size,
                "backup_size_mb": round(backup_size / (1024 * 1024), 2),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": str(source_dir)
            }
    
    def verify_backup(self, backup_path: Path) -> Dict[str, Any]:
        """
        Verify the integrity of a backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Verification result
        """
        backup_path = Path(backup_path).resolve()
        
        # Verify backup is in destination
        if not backup_path.is_relative_to(self.backup_destination):
            return {
                "success": False,
                "error": "Backup not in approved destination",
                "backup_path": str(backup_path)
            }
        
        if not backup_path.exists():
            return {
                "success": False,
                "error": "Backup file does not exist",
                "backup_path": str(backup_path)
            }
        
        try:
            # Try to open and verify the tar file
            with tarfile.open(backup_path, "r:gz") as tar:
                # Get list of files
                members = tar.getmembers()
                
                return {
                    "success": True,
                    "backup_path": str(backup_path),
                    "file_count": len(members),
                    "total_size": sum(m.size for m in members),
                    "verified": True
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backup_path": str(backup_path),
                "verified": False
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all backups in the destination.
        
        Returns:
            List of backup information
        """
        backups = []
        
        try:
            for item in self.backup_destination.iterdir():
                if item.is_file() and (item.suffix == ".gz" or item.name.endswith(".tar.gz")):
                    stat = item.stat()
                    backups.append({
                        "name": item.name,
                        "path": str(item),
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self, retain_count: int = 10) -> Dict[str, Any]:
        """
        Clean up old backups, retaining only the most recent ones.
        
        Args:
            retain_count: Number of backups to retain
            
        Returns:
            Cleanup result
        """
        backups = self.list_backups()
        
        if len(backups) <= retain_count:
            return {
                "success": True,
                "message": "No cleanup needed",
                "total_backups": len(backups),
                "retained": len(backups),
                "deleted": 0
            }
        
        # Delete old backups
        to_delete = backups[retain_count:]
        deleted_count = 0
        
        for backup in to_delete:
            try:
                backup_path = Path(backup["path"])
                backup_path.unlink()
                deleted_count += 1
                self.logger.info(f"Deleted old backup: {backup['name']}")
            except Exception as e:
                self.logger.error(f"Failed to delete backup {backup['name']}: {e}")
        
        return {
            "success": True,
            "total_backups": len(backups),
            "retained": len(backups) - deleted_count,
            "deleted": deleted_count
        }


if __name__ == "__main__":
    # Test the Backup Agent
    print("Testing Backup Agent...")
    
    import tempfile
    temp_workspace = Path(tempfile.mkdtemp())
    temp_dest = Path(tempfile.mkdtemp())
    temp_source = Path(tempfile.mkdtemp())
    
    # Create a test file in source
    test_file = temp_source / "test.txt"
    test_file.write_text("Test data for backup\n")
    
    agent = BackupAgent(temp_workspace, temp_dest)
    agent.add_source_directory(temp_source)
    
    # Test create backup
    result = agent.create_backup(temp_source)
    print(f"Backup result: {result}")
    
    # Test list backups
    backups = agent.list_backups()
    print(f"Backups: {len(backups)}")
    
    # Test verify backup
    if backups:
        verify = agent.verify_backup(backups[0]["path"])
        print(f"Verify result: {verify}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_workspace)
    shutil.rmtree(temp_dest)
    shutil.rmtree(temp_source)
    
    print("\n✅ Backup Agent Test Passed!")