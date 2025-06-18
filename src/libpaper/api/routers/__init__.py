"""
API routers for LibPaper
"""

from .papers import router as papers_router
from .collections import router as collections_router
from .tags import router as tags_router

__all__ = ["papers_router", "collections_router", "tags_router"]
