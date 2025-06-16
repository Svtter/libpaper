"""
LibPaper - A headless library for research paper management
"""

__version__ = "0.1.0"

from .models.paper import Paper
from .models.collection import Collection
from .models.tag import Tag

__all__ = ["Paper", "Collection", "Tag"]
