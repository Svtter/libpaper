"""
FastAPI dependencies for LibPaper API
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from ..storage.config import Config
from ..storage.database import Database
from ..storage.file_manager import FileManager
from ..services.paper_service import PaperService
from ..services.collection_service import CollectionService
from ..services.tag_service import TagService


# Global instances
_config: Config = None
_database: Database = None
_file_manager: FileManager = None


def get_config() -> Config:
    """Get application configuration"""
    global _config
    if _config is None:
        _config = Config.load()
        _config.ensure_directories()
    return _config


def get_database(config: Config = Depends(get_config)) -> Generator[Database, None, None]:
    """Get database instance"""
    global _database
    if _database is None:
        _database = Database(config.get_database_path())
        _database.create_tables()
    
    try:
        yield _database
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


def get_file_manager(config: Config = Depends(get_config)) -> FileManager:
    """Get file manager instance"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager(config)
    return _file_manager


def get_paper_service(
    database: Database = Depends(get_database),
    file_manager: FileManager = Depends(get_file_manager)
) -> PaperService:
    """Get paper service instance"""
    service = PaperService(database, file_manager)
    service.initialize()
    return service


def get_collection_service(
    database: Database = Depends(get_database)
) -> CollectionService:
    """Get collection service instance"""
    service = CollectionService(database)
    service.initialize()
    return service


def get_tag_service(
    database: Database = Depends(get_database)
) -> TagService:
    """Get tag service instance"""
    service = TagService(database)
    service.initialize()
    return service
