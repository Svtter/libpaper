"""测试配置和fixtures"""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.libpaper.models import Collection, Paper, Tag
from src.libpaper.services.paper_service import PaperService
from src.libpaper.storage.database import Database
from src.libpaper.storage.file_manager import FileManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_db(temp_dir: Path) -> Generator[Database, None, None]:
    """创建测试数据库"""
    db_path = temp_dir / "test.db"
    db = Database(db_path)
    db.create_tables()
    yield db
    db.close()


@pytest.fixture
def test_file_manager(temp_dir: Path) -> FileManager:
    """创建测试文件管理器"""
    storage_dir = temp_dir / "storage"
    return FileManager(storage_dir)


@pytest.fixture
def paper_service(test_db: Database, test_file_manager: FileManager) -> PaperService:
    """创建文献服务"""
    return PaperService(test_db, test_file_manager)


@pytest.fixture
def sample_pdf(temp_dir: Path) -> Path:
    """创建示例PDF文件"""
    pdf_path = temp_dir / "sample.pdf"
    # 创建一个简单的PDF内容（实际测试中可能需要真实的PDF）
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_paper_data() -> dict:
    """示例文献数据"""
    return {
        "title": "Test Paper Title",
        "authors": ["Author One", "Author Two"],
        "abstract": "This is a test abstract.",
        "journal": "Test Journal",
        "doi": "10.1234/test.doi",
    }


@pytest.fixture
def sample_collection_data() -> dict:
    """示例分类数据"""
    return {
        "name": "Test Collection",
        "description": "This is a test collection",
    }


@pytest.fixture
def sample_tag_data() -> dict:
    """示例标签数据"""
    return {
        "name": "test-tag",
        "description": "This is a test tag",
        "color": "#FF0000",
    }
