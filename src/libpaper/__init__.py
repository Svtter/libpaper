"""
LibPaper - A headless library for research paper management
"""

__version__ = "0.1.0"

from .models.paper import Paper, PaperCollectionLink, PaperTagLink
from .models.collection import Collection
from .models.tag import Tag
from .storage.config import Config
from .storage.database import Database
from .storage.file_manager import FileManager
from .api.main import app

__all__ = [
  "Paper", "PaperCollectionLink", "PaperTagLink",
  "Collection", "Tag",
  "Config", "Database", "FileManager",
  "app"
]
