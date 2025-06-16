"""测试数据模型"""

import json
from datetime import datetime
from uuid import uuid4

import pytest

from src.libpaper.models import Collection, Paper, Tag


class TestPaper:
    """测试Paper模型"""

    def test_paper_creation(self, sample_paper_data):
        """测试Paper创建"""
        paper = Paper(
            title=sample_paper_data["title"],
            file_path="/test/path/file.pdf",
            original_filename="file.pdf",
            file_size=1024,
            file_hash="a" * 64,  # 64位SHA256哈希
            authors=sample_paper_data["authors"],
            abstract=sample_paper_data["abstract"],
            journal=sample_paper_data["journal"],
            doi=sample_paper_data["doi"],
        )

        assert paper.title == sample_paper_data["title"]
        assert paper.authors == sample_paper_data["authors"]
        assert paper.abstract == sample_paper_data["abstract"]
        assert paper.journal == sample_paper_data["journal"]
        assert paper.doi == sample_paper_data["doi"]
        assert paper.file_size == 1024
        assert len(paper.file_hash) == 64

    def test_paper_authors_property(self):
        """测试authors属性的getter和setter"""
        paper = Paper(
            title="Test",
            file_path="/test",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
        )

        # 测试设置authors
        authors = ["Author 1", "Author 2"]
        paper.authors = authors
        assert paper.authors == authors
        assert paper.authors_json == json.dumps(authors)

        # 测试空authors
        paper.authors = []
        assert paper.authors == []
        assert paper.authors_json is None

    def test_paper_hash_validation(self):
        """测试文件哈希验证"""
        # 测试有效哈希
        paper = Paper(
            title="Test",
            file_path="/test",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
        )
        assert len(paper.file_hash) == 64

        # 测试无效哈希长度
        with pytest.raises(ValueError, match="SHA256 哈希值必须是64位十六进制字符串"):
            Paper(
                title="Test",
                file_path="/test",
                original_filename="test.pdf",
                file_size=1024,
                file_hash="a" * 32,  # 错误长度
            )

        # 测试无效哈希字符
        with pytest.raises(ValueError, match="SHA256 哈希值必须是有效的十六进制字符串"):
            Paper(
                title="Test",
                file_path="/test",
                original_filename="test.pdf",
                file_size=1024,
                file_hash="z" * 64,  # 无效字符
            )

    def test_paper_doi_validation(self):
        """测试DOI验证"""
        # 测试有效DOI
        paper = Paper(
            title="Test",
            file_path="/test",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
            doi="10.1234/test.doi",
        )
        assert paper.doi == "10.1234/test.doi"

        # 测试无效DOI
        with pytest.raises(ValueError, match='DOI 必须以 "10." 开头'):
            Paper(
                title="Test",
                file_path="/test",
                original_filename="test.pdf",
                file_size=1024,
                file_hash="a" * 64,
                doi="invalid.doi",
            )

    def test_paper_to_dict(self):
        """测试转换为字典"""
        paper = Paper(
            title="Test Title",
            file_path="/test/path",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
            authors=["Author 1"],
            abstract="Test abstract",
            doi="10.1234/test",
        )

        paper_dict = paper.to_dict()

        assert paper_dict["title"] == "Test Title"
        assert paper_dict["authors"] == ["Author 1"]
        assert paper_dict["file_size"] == 1024
        assert "created_at" in paper_dict
        assert "updated_at" in paper_dict

    def test_paper_from_dict(self):
        """测试从字典创建Paper"""
        data = {
            "title": "Test Title",
            "file_path": "/test/path",
            "original_filename": "test.pdf",
            "file_size": 1024,
            "file_hash": "a" * 64,
            "authors": ["Author 1"],
            "abstract": "Test abstract",
            "doi": "10.1234/test",
        }

        paper = Paper.from_dict(data)

        assert paper.title == "Test Title"
        assert paper.authors == ["Author 1"]
        assert paper.file_size == 1024

    def test_paper_json_serialization(self):
        """测试JSON序列化和反序列化"""
        paper = Paper(
            title="Test Title",
            file_path="/test/path",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
            authors=["Author 1"],
        )

        # 序列化
        json_str = paper.to_json()
        assert isinstance(json_str, str)

        # 反序列化
        paper_from_json = Paper.from_json(json_str)
        assert paper_from_json.title == paper.title
        assert paper_from_json.authors == paper.authors


class TestCollection:
    """测试Collection模型"""

    def test_collection_creation(self, sample_collection_data):
        """测试Collection创建"""
        collection = Collection(
            name=sample_collection_data["name"],
            description=sample_collection_data["description"],
        )

        assert collection.name == sample_collection_data["name"]
        assert collection.description == sample_collection_data["description"]
        assert isinstance(collection.id, type(uuid4()))
        assert isinstance(collection.created_at, datetime)
        assert isinstance(collection.updated_at, datetime)

    def test_collection_hierarchy(self):
        """测试分类层次结构"""
        parent = Collection(name="Parent Collection")
        child = Collection(name="Child Collection", parent_id=parent.id)

        assert child.parent_id == parent.id


class TestTag:
    """测试Tag模型"""

    def test_tag_creation(self, sample_tag_data):
        """测试Tag创建"""
        tag = Tag(
            name=sample_tag_data["name"],
            description=sample_tag_data["description"],
            color=sample_tag_data["color"],
        )

        assert tag.name == sample_tag_data["name"]
        assert tag.description == sample_tag_data["description"]
        assert tag.color == sample_tag_data["color"]
        assert isinstance(tag.created_at, datetime)

    def test_tag_name_as_primary_key(self):
        """测试标签名作为主键"""
        tag1 = Tag(name="same-name")
        tag2 = Tag(name="same-name")

        # 两个标签有相同的名称（这在数据库层面会处理唯一性约束）
        assert tag1.name == tag2.name
