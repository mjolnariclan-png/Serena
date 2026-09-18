"""
Media Manager Agent
Watches folders for new media, organizes files, manages Jellyfin library
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import time
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

class MediaAgent(BaseAgent):
    """Agent for managing media files and Jellyfin integration"""
    
    def __init__(self, workspace: Path):
        instructions = """
        You are the Media Manager Agent. Your job is to:
        1. Watch for new media files in incoming directories
        2. Identify what type of content (movie, TV show, etc.)
        3. Rename files to standard format
        4. Sort into correct Jellyfin library folders
        5. Check and fix metadata
        6. Trigger Jellyfin library refresh
        7. Report all changes made
        
        Always be conservative - if unsure, move to Unsorted and report.
        """
        
        super().__init__("MediaAgent", workspace, instructions)
        
        # Media-specific setup
        self.media_dirs = {
            "incoming_movies": "/home/eirik17/Media/Incoming/Movies",
            "incoming_tv": "/home/eirik17/Media/Incoming/TV", 
            "movies_library": "/home/eirik17/Media/Movies",
            "tv_library": "/home/eirik17/Media/TV Shows",
            "unsorted": "/home/eirik17/Media/Unsorted"
        }
        
        # Set up permissions
        self.add_permission("read_dirs", list(self.media_dirs.values()))
        self.add_permission("write_dirs", list(self.media_dirs.values()))
        self.add_permission("allowed_commands", [
            "systemctl",
            "curl",
            "ffprobe",
            "jellyfin"
        ])
        
        # Add safety rules
        self.add_rule("Never permanently delete a file")
        self.add_rule("Never overwrite an existing file")
        self.add_rule("Never modify files outside media directories")
        self.add_rule("If uncertain about categorization, move to Unsorted")
        self.add_rule("Verify every file operation")
        self.add_rule("Keep a log of every operation")
        
    def identify_media_type(self, filename: str) -> str:
        """Identify if file is movie or TV show based on patterns"""
        filename_lower = filename.lower()
        
        # TV show patterns (S01E01, 1x01, etc.)
        tv_patterns = [
            r'[sS]\d{1,2}[eE]\d{1,2}',  # S01E01
            r'\d{1,2}x\d{1,2}',          # 1x01
            r'season *\d+ *episode *\d+', # season 1 episode 1
        ]
        
        for pattern in tv_patterns:
            if re.search(pattern, filename_lower):
                return "tv"
        
        # Movie patterns (year in parentheses, etc.)
        movie_patterns = [
            r'\(\d{4}\)',  # (2023)
            r'\[\d{4}\]',  # [2023]
        ]
        
        for pattern in movie_patterns:
            if re.search(pattern, filename_lower):
                return "movie"
        
        # Default to unsorted if uncertain
        return "unsorted"
    
    def clean_filename(self, filename: str) -> str:
        """Clean filename to standard format"""
        # Remove common junk
        cleaned = re.sub(r'\[.*?\]', '', filename)  # Remove brackets
        cleaned = re.sub(r'\(.*?\)', '', cleaned)  # Remove parentheses
        cleaned = re.sub(r'\.{3,}', '.', cleaned)    # Fix multiple dots
        cleaned = re.sub(r'[_\-.]+', ' ', cleaned)  # Replace separators with space
        cleaned = cleaned.strip()
        
        return cleaned
    
    def format_movie_filename(self, filename: str) -> str:
        """Format movie filename to standard: Movie Name (Year).ext"""
        name = Path(filename).stem
        ext = Path(filename).suffix
        
        # Try to extract year
        year_match = re.search(r'(19|20)\d{2}', filename)
        year = year_match.group(0) if year_match else ""
        
        # Clean name
        clean_name = self.clean_filename(name)
        
        if year:
            return f"{clean_name} ({year}){ext}"
        else:
            return f"{clean_name}{ext}"
    
    def format_tv_filename(self, filename: str) -> str:
        """Format TV filename to standard: Show Name - S01E01 - Episode Title.ext"""
        name = Path(filename).stem
        ext = Path(filename).suffix
        
        # Extract season/episode info
        se_match = re.search(r'[sS](\d{1,2})[eE](\d{1,2})', filename, re.IGNORECASE)
        if se_match:
            season = se_match.group(1).zfill(2)
            episode = se_match.group(2).zfill(2)
            se_info = f"S{season}E{episode}"
        else:
            se_match = re.search(r'(\d{1,2})x(\d{1,2})', filename)
            if se_match:
                season = se_match.group(1).zfill(2)
                episode = se_match.group(2).zfill(2)
                se_info = f"S{season}E{episode}"
            else:
                se_info = ""
        
        # Clean show name
        clean_name = self.clean_filename(name)
        
        if se_info:
            return f"{clean_name} - {se_info}{ext}"
        else:
            return f"{clean_name}{ext}"
    
    def organize_media_file(self, source_path: str) -> bool:
        """Organize a single media file"""
        filename = Path(source_path).name
        media_type = self.identify_type(filename)
        
        if media_type == "movie":
            dest_dir = self.media_dirs["movies_library"]
            new_filename = self.format_movie_filename(filename)
        elif media_type == "tv":
            dest_dir = self.media_dirs["tv_library"]
            new_filename = self.format_tv_filename(filename)
        else:
            dest_dir = self.media_dirs["unsorted"]
            new_filename = filename
        
        destination = os.path.join(dest_dir, new_filename)
        
        # Check if destination exists
        if os.path.exists(destination):
            self.logger.warning(f"Destination already exists: {destination}")
            # Move to unsorted with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{Path(filename).stem}_{timestamp}{Path(filename).suffix}"
            destination = os.path.join(self.media_dirs["unsorted"], new_filename)
        
        # Move the file
        success = self.safe_move_file(source_path, destination)
        
        if success:
            self.log_activity("organized_media", {
                "source": source_path,
                "destination": destination,
                "type": media_type
            })
        
        return success
    
    def scan_incoming_directories(self) -> List[str]:
        """Scan incoming directories for new files"""
        new_files = []
        
        for dir_name, dir_path in self.media_dirs.items():
            if "incoming" in dir_name:
                files = self.list_files(dir_path)
                new_files.extend(files)
        
        return new_files
    
    def trigger_jellyfin_refresh(self) -> bool:
        """Trigger Jellyfin library refresh via API"""
        try:
            # This would connect to Jellyfin API
            # For now, just log the action
            self.log_activity("jellyfin_refresh", {"status": "triggered"})
            return True
        except Exception as e:
            self.logger.error(f"Failed to trigger Jellyfin refresh: {e}")
            return False
    
    def execute_task(self, task: str) -> str:
        """Execute media management task"""
        self.logger.info(f"Media task: {task}")
        
        if "scan" in task.lower():
            new_files = self.scan_incoming_directories()
            organized_count = 0
            
            for file_path in new_files:
                if self.organize_media_file(file_path):
                    organized_count += 1
            
            result = f"Scanned and organized {organized_count} media files"
            
            if organized_count > 0:
                self.trigger_jellyfin_refresh()
            
            return result
        
        elif "refresh" in task.lower():
            if self.trigger_jellyfin_refresh():
                return "Jellyfin refresh triggered"
            else:
                return "Failed to trigger Jellyfin refresh"
        
        else:
            return f"Unknown media task: {task}"
    
    def identify_type(self, filename: str) -> str:
        """Identify media type (alias for identify_media_type)"""
        return self.identify_media_type(filename)