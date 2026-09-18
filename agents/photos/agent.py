"""
Photo Organizer Agent
Watches incoming folders, groups photos by date, detects duplicates, organizes into album structure
"""

import os
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

class PhotoAgent(BaseAgent):
    """Agent for organizing photos and videos by date and detecting duplicates"""
    
    def __init__(self, workspace: Path):
        instructions = """
        You are the Photo Organizer Agent. Your job is to:
        1. Watch incoming folders for new photos and videos
        2. Group files by date taken (from EXIF or file date)
        3. Detect duplicate files using hash comparison
        4. Organize into album structure (YYYY/MM/DD)
        5. Handle videos separately or mixed with photos
        6. Leave uncertain items in Unsorted folder
        7. Maintain a database of processed files
        8. Report all organization activities
        
        Be conservative with file operations. Never delete without confirmation.
        """
        
        super().__init__("PhotoAgent", workspace, instructions)
        
        # Photo organization paths
        self.photo_dirs = {
            "incoming": "/home/eirik17/Pictures/Incoming",
            "organized": "/home/eirik17/Pictures/Organized",
            "unsorted": "/home/eirik17/Pictures/Unsorted",
            "duplicates": "/home/eirik17/Pictures/Duplicates"
        }
        
        # Supported file types
        self.photo_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.raw'}
        self.video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv'}
        
        # Database for tracking processed files
        self.processed_db = self.workspace / "photos_processed.json"
        self.processed_files = self._load_processed_db()
        
        # Set up permissions
        self.add_permission("read_dirs", list(self.photo_dirs.values()))
        self.add_permission("write_dirs", list(self.photo_dirs.values()))
        # Note: exiftool is used directly in _get_file_date, not through safe_run_command
        
        # Add safety rules
        self.add_rule("Never permanently delete a file")
        self.add_rule("Never overwrite an existing file")
        self.add_rule("Never modify files outside photo directories")
        self.add_rule("If date cannot be determined, move to Unsorted")
        self.add_rule("Move duplicates to Duplicates folder, don't delete")
        self.add_rule("Verify every file operation")
        self.add_rule("Keep a log of every operation")
    
    def _load_processed_db(self) -> Dict:
        """Load database of already processed files"""
        if self.processed_db.exists():
            try:
                with open(self.processed_db, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_processed_db(self):
        """Save database of processed files"""
        with open(self.processed_db, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file for duplicate detection"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""
    
    def _get_file_date(self, file_path: str) -> datetime:
        """Get the date of a file from EXIF data or file modification time"""
        try:
            # Try to get EXIF date using exiftool if available
            # Check if exiftool command is available first
            try:
                import subprocess
                result = subprocess.run(
                    ["exiftool", "-DateTimeOriginal", "-s3", file_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout:
                    # Parse EXIF date format: "2023:08:15 14:30:45"
                    date_match = re.search(r'(\d{4}:\d{2}:\d{2})', result.stdout)
                    if date_match:
                        date_str = date_match.group(1)
                        return datetime.strptime(date_str, "%Y:%m:%d")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        except:
            pass
        
        # Fallback to file modification time
        try:
            mod_time = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mod_time)
        except:
            return datetime.now()
    
    def _is_media_file(self, file_path: str) -> Tuple[bool, str]:
        """Check if file is a photo or video and return type"""
        ext = Path(file_path).suffix.lower()
        
        if ext in self.photo_extensions:
            return (True, "photo")
        elif ext in self.video_extensions:
            return (True, "video")
        else:
            return (False, "unknown")
    
    def _is_duplicate(self, file_path: str) -> Tuple[bool, str]:
        """Check if file is a duplicate of an already processed file"""
        file_hash = self._get_file_hash(file_path)
        
        if not file_hash:
            return (False, "")
        
        for processed_path, processed_hash in self.processed_files.items():
            if processed_hash == file_hash:
                return (True, processed_path)
        
        return (False, "")
    
    def _organize_by_date(self, file_path: str, file_type: str) -> str:
        """Organize a file into date-based folder structure"""
        file_date = self._get_file_date(file_path)
        
        # Create date-based path: YYYY/MM/DD
        year_path = self.photo_dirs["organized"] / str(file_date.year)
        month_path = year_path / f"{file_date.month:02d}"
        day_path = month_path / f"{file_date.day:02d}"
        
        # Add subfolder for photos/videos
        type_path = day_path / file_type
        type_path.mkdir(parents=True, exist_ok=True)
        
        # Generate new filename
        original_name = Path(file_path).name
        timestamp = file_date.strftime("%H%M%S")
        new_name = f"{timestamp}_{original_name}"
        destination = type_path / new_name
        
        # Handle name conflicts
        counter = 1
        while destination.exists():
            new_name = f"{timestamp}_{counter}_{original_name}"
            destination = type_path / new_name
            counter += 1
        
        return str(destination)
    
    def process_file(self, file_path: str) -> bool:
        """Process a single media file"""
        file_path_str = str(file_path)
        
        # Check if it's a media file
        is_media, media_type = self._is_media_file(file_path_str)
        if not is_media:
            return False
        
        # Check if already processed
        if file_path_str in self.processed_files:
            self.logger.info(f"File already processed: {file_path_str}")
            return False
        
        # Check for duplicates
        is_duplicate, original_path = self._is_duplicate(file_path_str)
        if is_duplicate:
            # Move to duplicates folder
            duplicate_dest = self.photo_dirs["duplicates"] / Path(file_path_str).name
            Path(self.photo_dirs["duplicates"]).mkdir(parents=True, exist_ok=True)
            
            success = self.safe_move_file(file_path_str, str(duplicate_dest))
            if success:
                self.log_activity("duplicate_found", {
                    "file": file_path_str,
                    "original": original_path,
                    "destination": str(duplicate_dest)
                })
            return success
        
        # Try to organize by date
        try:
            destination = self._organize_by_date(file_path_str, media_type)
            success = self.safe_move_file(file_path_str, destination)
            
            if success:
                # Add to processed database
                file_hash = self._get_file_hash(destination)
                self.processed_files[destination] = file_hash
                self._save_processed_db()
                
                self.log_activity("file_organized", {
                    "source": file_path_str,
                    "destination": destination,
                    "type": media_type
                })
                return True
            else:
                # If organization fails, move to unsorted
                unsorted_dest = self.photo_dirs["unsorted"] / Path(file_path_str).name
                Path(self.photo_dirs["unsorted"]).mkdir(parents=True, exist_ok=True)
                return self.safe_move_file(file_path_str, str(unsorted_dest))
                
        except Exception as e:
            self.logger.error(f"Error processing {file_path_str}: {e}")
            # Move to unsorted on error
            unsorted_dest = self.photo_dirs["unsorted"] / Path(file_path_str).name
            Path(self.photo_dirs["unsorted"]).mkdir(parents=True, exist_ok=True)
            return self.safe_move_file(file_path_str, str(unsorted_dest))
    
    def scan_incoming(self) -> Dict[str, int]:
        """Scan incoming directory for new files"""
        incoming_path = Path(self.photo_dirs["incoming"])
        
        if not incoming_path.exists():
            incoming_path.mkdir(parents=True, exist_ok=True)
            return {"scanned": 0, "processed": 0, "duplicates": 0, "errors": 0}
        
        results = {
            "scanned": 0,
            "processed": 0,
            "duplicates": 0,
            "errors": 0
        }
        
        # Get all files in incoming directory
        files = list(incoming_path.glob("*"))
        files = [f for f in files if f.is_file()]
        
        results["scanned"] = len(files)
        
        for file_path in files:
            try:
                is_media, media_type = self._is_media_file(str(file_path))
                if is_media:
                    # Check for duplicate first
                    is_duplicate, _ = self._is_duplicate(str(file_path))
                    if is_duplicate:
                        self.process_file(str(file_path))
                        results["duplicates"] += 1
                    else:
                        if self.process_file(str(file_path)):
                            results["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error scanning {file_path}: {e}")
                results["errors"] += 1
        
        return results
    
    def get_organization_stats(self) -> Dict:
        """Get statistics about organized photos"""
        stats = {
            "total_processed": len(self.processed_files),
            "incoming_count": 0,
            "organized_count": 0,
            "unsorted_count": 0,
            "duplicate_count": 0
        }
        
        # Count files in each directory
        for dir_name, dir_path in self.photo_dirs.items():
            if Path(dir_path).exists():
                files = list(Path(dir_path).glob("*"))
                files = [f for f in files if f.is_file()]
                
                if dir_name == "incoming":
                    stats["incoming_count"] = len(files)
                elif dir_name == "organized":
                    stats["organized_count"] = len(files)
                elif dir_name == "unsorted":
                    stats["unsorted_count"] = len(files)
                elif dir_name == "duplicates":
                    stats["duplicate_count"] = len(files)
        
        return stats
    
    def generate_report(self) -> str:
        """Generate organization report"""
        stats = self.get_organization_stats()
        
        report = []
        report.append("=" * 50)
        report.append("PHOTO ORGANIZATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 50)
        
        report.append(f"\nTotal files processed: {stats['total_processed']}")
        report.append(f"Files in incoming: {stats['incoming_count']}")
        report.append(f"Files organized: {stats['organized_count']}")
        report.append(f"Files in unsorted: {stats['unsorted_count']}")
        report.append(f"Duplicate files: {stats['duplicate_count']}")
        
        report.append("\nDirectory structure:")
        for dir_name, dir_path in self.photo_dirs.items():
            path = Path(dir_path)
            status = "✓" if path.exists() else "✗"
            report.append(f"  {status} {dir_name}: {dir_path}")
        
        report.append("=" * 50)
        
        return "\n".join(report)
    
    def execute_task(self, task: str) -> str:
        """Execute photo organization task"""
        self.logger.info(f"Photo task: {task}")
        
        if "scan" in task.lower() or "organize" in task.lower():
            results = self.scan_incoming()
            return f"Scanned {results['scanned']} files, processed {results['processed']}, found {results['duplicates']} duplicates, {results['errors']} errors"
        
        elif "report" in task.lower() or "stats" in task.lower():
            return self.generate_report()
        
        elif "check" in task.lower():
            stats = self.get_organization_stats()
            return f"Incoming: {stats['incoming_count']}, Organized: {stats['organized_count']}, Unsorted: {stats['unsorted_count']}, Duplicates: {stats['duplicate_count']}"
        
        else:
            return f"Unknown photo task: {task}"