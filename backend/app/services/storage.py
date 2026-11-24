import os
import shutil
import logging
from typing import Optional
from fastapi import UploadFile
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class StorageService:
    """
    Service for handling local file storage.
    Manages uploaded images and associated files.
    """
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "images").mkdir(exist_ok=True)
        (self.upload_dir / "masks").mkdir(exist_ok=True)
    
    async def save_upload_file(self, file: UploadFile, subdirectory: str = "images") -> str:
        """
        Save an uploaded file and return the relative path.
        
        Args:
            file: The uploaded file
            subdirectory: Subdirectory within uploads (e.g., "images", "masks")
            
        Returns:
            str: Relative path to the saved file
        """
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create full path
        target_dir = self.upload_dir / subdirectory
        target_dir.mkdir(exist_ok=True)
        file_path = target_dir / unique_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()
        
        # Return relative path with forward slashes and uploads prefix
        relative_path = f"uploads/{subdirectory}/{unique_filename}".replace('\\', '/')
        logger.info(f"Saved file: {relative_path} (absolute: {file_path})")
        return relative_path
    
    def get_absolute_path(self, relative_path: str) -> str:
        """
        Convert relative path to absolute path.
        
        Args:
            relative_path: Relative path from project root (e.g., "uploads/images/file.jpg")
            
        Returns:
            str: Absolute file path
        """
        return str(Path.cwd() / relative_path)
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a file by its relative path.
        
        Args:
            relative_path: Relative path to delete (e.g., "uploads/images/file.jpg")
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            file_path = Path.cwd() / relative_path
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            relative_path: Relative path to check (e.g., "uploads/images/file.jpg")
            
        Returns:
            bool: True if file exists
        """
        file_path = Path.cwd() / relative_path
        return file_path.exists()