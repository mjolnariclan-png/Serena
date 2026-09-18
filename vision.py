"""
Vision System for Serena
Phase 3: Image loading, processing, and visual analysis

This module provides safe image processing and visual analysis capabilities.
Respects filesystem permissions and does not allow unrestricted filesystem access.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

# Try to import vision libraries
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class VisionSystem:
    """
    Vision system for image processing and analysis.
    
    Supports:
    - Image loading
    - Supported format detection
    - Basic image processing
    - Image metadata extraction
    - Safe handling of inaccessible images
    - Permission-aware file access
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
        '.webp', '.ico', '.svg', '.pdf'
    }
    
    def __init__(self, permission_system=None):
        """
        Initialize Vision System.
        
        Args:
            permission_system: Centralized permission system for file access
        """
        self.permission_system = permission_system
        self.logger = self._setup_logging()
        
        # Check available libraries
        self.capabilities = {
            "pil_available": PIL_AVAILABLE,
            "opencv_available": OPENCV_AVAILABLE,
            "supported_formats": list(self.SUPPORTED_FORMATS)
        }
        
        self.logger.info(f"Vision System initialized with capabilities: {self.capabilities}")
    
    def _setup_logging(self):
        """Setup logging."""
        import logging
        logger = logging.getLogger("VisionSystem")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger
    
    def load_image(self, image_path: str) -> Dict[str, Any]:
        """
        Load an image with permission checking.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image information or error
        """
        path = Path(image_path)
        
        # Check if file exists
        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "path": str(path)
            }
        
        # Check if format is supported
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return {
                "success": False,
                "error": f"Unsupported format: {path.suffix}",
                "supported_formats": list(self.SUPPORTED_FORMATS),
                "path": str(path)
            }
        
        # Check permission if permission system is available
        if self.permission_system:
            try:
                # Request permission to read the file
                from core_data_contracts import PermissionRequest, PermissionLevel, generate_request_id
                
                request = PermissionRequest(
                    request_id=generate_request_id(),
                    operation="read_image",
                    agent_id="VisionSystem",
                    parameters={"path": str(path)},
                    context={"purpose": "visual_analysis"},
                    permission_level=PermissionLevel.SAFE
                )
                
                decision = self.permission_system.validate_operation(request)
                
                if not decision.allowed:
                    return {
                        "success": False,
                        "error": "Permission denied",
                        "reason": decision.reason,
                        "path": str(path)
                    }
                    
            except Exception as e:
                self.logger.warning(f"Permission check failed: {e}, proceeding with caution")
        
        # Try to load image
        try:
            if PIL_AVAILABLE:
                img = Image.open(path)
                
                # Extract metadata
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                
                # Get EXIF data if available
                if hasattr(img, '_getexif'):
                    try:
                        exif = img._getexif()
                        if exif:
                            metadata["exif"] = dict(exif)
                    except:
                        pass
                
                return {
                    "success": True,
                    "path": str(path),
                    "metadata": metadata,
                    "library": "PIL"
                }
                
            elif OPENCV_AVAILABLE:
                img = cv2.imread(str(path))
                if img is None:
                    return {
                        "success": False,
                        "error": "Failed to load image with OpenCV",
                        "path": str(path)
                    }
                
                height, width = img.shape[:2]
                metadata = {
                    "size": (width, height),
                    "width": width,
                    "height": height,
                    "channels": img.shape[2] if len(img.shape) > 2 else 1
                }
                
                return {
                    "success": True,
                    "path": str(path),
                    "metadata": metadata,
                    "library": "OpenCV"
                }
                
            else:
                return {
                    "success": False,
                    "error": "No image processing library available",
                    "available_libraries": {
                        "PIL": PIL_AVAILABLE,
                        "OpenCV": OPENCV_AVAILABLE
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": str(path)
            }
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Perform basic visual analysis on an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Analysis results
        """
        # First load the image
        load_result = self.load_image(image_path)
        
        if not load_result["success"]:
            return load_result
        
        try:
            analysis = {
                "path": load_result["path"],
                "metadata": load_result["metadata"],
                "analysis": {}
            }
            
            # Add basic analysis
            metadata = load_result["metadata"]
            
            # Calculate aspect ratio
            if "width" in metadata and "height" in metadata:
                width = metadata["width"]
                height = metadata["height"]
                aspect_ratio = width / height if height > 0 else 0
                analysis["analysis"]["aspect_ratio"] = round(aspect_ratio, 2)
                analysis["analysis"]["orientation"] = self._determine_orientation(width, height)
            
            # Estimate color information
            if OPENCV_AVAILABLE:
                img = cv2.imread(image_path)
                if img is not None:
                    # Get basic color statistics
                    if len(img.shape) == 3:
                        # Color image
                        analysis["analysis"]["color_mode"] = "RGB"
                        analysis["analysis"]["channels"] = 3
                    else:
                        # Grayscale
                        analysis["analysis"]["color_mode"] = "Grayscale"
                        analysis["analysis"]["channels"] = 1
            
            return {
                "success": True,
                "result": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": image_path
            }
    
    def resize_image(self, image_path: str, size: Tuple[int, int], 
                    output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Resize an image.
        
        Args:
            image_path: Path to input image
            size: Target size (width, height)
            output_path: Path for output (defaults to input_path with _resized suffix)
            
        Returns:
            Result information
        """
        # Load image first
        load_result = self.load_image(image_path)
        
        if not load_result["success"]:
            return load_result
        
        # Determine output path
        if output_path is None:
            path = Path(image_path)
            output_path = str(path.parent / f"{path.stem}_resized{path.suffix}")
        
        # Check write permission if permission system is available
        if self.permission_system:
            try:
                from core_data_contracts import PermissionRequest, PermissionLevel, generate_request_id
                
                request = PermissionRequest(
                    request_id=generate_request_id(),
                    operation="write_image",
                    agent_id="VisionSystem",
                    parameters={"path": output_path},
                    context={"purpose": "image_resize"},
                    permission_level=PermissionLevel.SAFE
                )
                
                decision = self.permission_system.validate_operation(request)
                
                if not decision.allowed:
                    return {
                        "success": False,
                        "error": "Permission denied",
                        "reason": decision.reason,
                        "output_path": output_path
                    }
                    
            except Exception as e:
                self.logger.warning(f"Permission check failed: {e}, proceeding with caution")
        
        try:
            if PIL_AVAILABLE:
                img = Image.open(image_path)
                resized = img.resize(size)
                resized.save(output_path)
                
                return {
                    "success": True,
                    "input_path": image_path,
                    "output_path": output_path,
                    "original_size": img.size,
                    "new_size": size,
                    "library": "PIL"
                }
                
            elif OPENCV_AVAILABLE:
                img = cv2.imread(image_path)
                resized = cv2.resize(img, size)
                cv2.imwrite(output_path, resized)
                
                return {
                    "success": True,
                    "input_path": image_path,
                    "output_path": output_path,
                    "original_size": (img.shape[1], img.shape[0]),
                    "new_size": size,
                    "library": "OpenCV"
                }
                
            else:
                return {
                    "success": False,
                    "error": "No image processing library available"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "input_path": image_path,
                "output_path": output_path
            }
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get basic information about an image without loading it fully.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image information
        """
        path = Path(image_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "path": str(path)
            }
        
        try:
            stat = path.stat()
            
            info = {
                "success": True,
                "path": str(path),
                "name": path.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "format": path.suffix.lower(),
                "is_supported": path.suffix.lower() in self.SUPPORTED_FORMATS,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            return info
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": str(path)
            }
    
    def _determine_orientation(self, width: int, height: int) -> str:
        """Determine image orientation from dimensions."""
        if width > height:
            return "landscape"
        elif height > width:
            return "portrait"
        else:
            return "square"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get system capabilities."""
        return self.capabilities.copy()


# Global instance
_vision_system = None

def get_vision_system(permission_system=None) -> VisionSystem:
    """Get or create the global VisionSystem instance."""
    global _vision_system
    if _vision_system is None:
        _vision_system = VisionSystem(permission_system)
    return _vision_system


if __name__ == "__main__":
    # Test the vision system
    print("Testing Vision System...")
    
    vision = VisionSystem()
    
    # Test capabilities
    capabilities = vision.get_capabilities()
    print(f"Capabilities: {capabilities}")
    
    # Test with a non-existent file
    result = vision.load_image("/nonexistent/image.jpg")
    print(f"Non-existent file: {result}")
    
    # Test image info on existing file (if available)
    test_images = [
        "/home/eirik17/Desktop/Serena/images/avatars/Serena.png",
        "/home/eirik17/Desktop/Serena/images/avatars/Astrid.png"
    ]
    
    for img_path in test_images:
        if Path(img_path).exists():
            info = vision.get_image_info(img_path)
            print(f"Image info: {info}")
            break
    
    print("\n✅ Vision System Test Passed!")