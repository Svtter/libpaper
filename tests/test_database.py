"""测试数据库操作"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.libpaper.models import Collection, Paper, Tag
from src.libpaper.storage.database import Database


class TestDatabase:
    """测试数据库操作类"""

    def test_database_initialization(self, temp_dir):
        """测试数据库初始化"""
        db_path = temp_dir / "test.db"
        db = Database(db_path)

        assert db.db_path == db_path
        assert "sqlite:///" in db.db_url

        # 测试表创建
        db.create_tables()
        assert db_path.exists()

        db.close()

    def test_paper_crud_operations(self, test_db):
        """测试Paper的CRUD操作"""
        # 创建Paper
        paper = Paper(
            title="Test Paper",
            file_path="/test/path.pdf",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
            authors=["Test Author"],
            abstract="Test abstract",
        )

        # 测试创建
        created_paper = test_db.create_paper(paper)
        assert created_paper.id is not None
        assert created_paper.title == "Test Paper"

        # 测试按ID获取
        retrieved_paper = test_db.get_paper_by_id(created_paper.id)
        assert retrieved_paper is not None
        assert retrieved_paper.title == "Test Paper"

        # 测试按哈希获取
        hash_paper = test_db.get_paper_by_hash(paper.file_hash)
        assert hash_paper is not None
        assert hash_paper.id == created_paper.id

        # 测试更新
        retrieved_paper.title = "Updated Title"
        updated_paper = test_db.update_paper(retrieved_paper)
        assert updated_paper.title == "Updated Title"
        assert updated_paper.updated_at > updated_paper.created_at

        # 测试删除
        success = test_db.delete_paper(created_paper.id)
        assert success is True

        # 验证删除
        deleted_paper = test_db.get_paper_by_id(created_paper.id)
        assert deleted_paper is None

    def test_collection_crud_operations(self, test_db):
        """测试Collection的CRUD操作"""
        # 创建Collection
        collection = Collection(
            name="Test Collection",
            description="Test description",
        )

        # 测试创建
        created_collection = test_db.create_collection(collection)
        assert created_collection.id is not None
        assert created_collection.name == "Test Collection"

        # 测试获取
        retrieved_collection = test_db.get_collection_by_id(created_collection.id)
        assert retrieved_collection is not None
        assert retrieved_collection.name == "Test Collection"

        # 测试更新
        retrieved_collection.name = "Updated Collection"
        updated_collection = test_db.update_collection(retrieved_collection)
        assert updated_collection.name == "Updated Collection"

        # 测试获取所有
        all_collections = test_db.get_all_collections()
        assert len(all_collections) == 1
        assert all_collections[0].name == "Updated Collection"

        # 测试删除
        success = test_db.delete_collection(created_collection.id)
        assert success is True

        # 验证删除
        deleted_collection = test_db.get_collection_by_id(created_collection.id)
        assert deleted_collection is None

    def test_tag_crud_operations(self, test_db):
        """测试Tag的CRUD操作"""
        # 创建Tag
        tag = Tag(
            name="test-tag",
            description="Test tag description",
            color="#FF0000",
        )

        # 测试创建
        created_tag = test_db.create_tag(tag)
        assert created_tag.name == "test-tag"

        # 测试获取
        retrieved_tag = test_db.get_tag_by_name("test-tag")
        assert retrieved_tag is not None
        assert retrieved_tag.name == "test-tag"

        # 测试获取所有
        all_tags = test_db.get_all_tags()
        assert len(all_tags) == 1
        assert all_tags[0].name == "test-tag"

        # 测试删除
        success = test_db.delete_tag("test-tag")
        assert success is True

        # 验证删除
        deleted_tag = test_db.get_tag_by_name("test-tag")
        assert deleted_tag is None

    def test_paper_search(self, test_db):
        """测试文献搜索功能"""
        # 创建测试数据
        paper1 = Paper(
            title="Machine Learning Research",
            file_path="/test/ml.pdf",
            original_filename="ml.pdf",
            file_size=1024,
            file_hash="a" * 64,
            authors=["ML Author"],
            abstract="This is about machine learning",
        )

        paper2 = Paper(
            title="Deep Learning Study",
            file_path="/test/dl.pdf",
            original_filename="dl.pdf",
            file_size=2048,
            file_hash="b" * 64,
            authors=["DL Author"],
            abstract="This is about deep learning",
        )

        test_db.create_paper(paper1)
        test_db.create_paper(paper2)

        # 测试文本搜索
        results = test_db.search_papers(query="Machine")
        assert len(results) == 1
        assert results[0].title == "Machine Learning Research"

        results = test_db.search_papers(query="learning")
        assert len(results) == 2

        # 测试分页
        results = test_db.search_papers(limit=1)
        assert len(results) == 1

        results = test_db.search_papers(limit=1, offset=1)
        assert len(results) == 1

    def test_paper_collection_relationships(self, test_db):
        """测试文献和分类的关联关系"""
        # 创建测试数据
        paper = Paper(
            title="Test Paper",
            file_path="/test/test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
        )
        created_paper = test_db.create_paper(paper)

        collection = Collection(name="Test Collection")
        created_collection = test_db.create_collection(collection)

        # 测试添加关联
        success = test_db.add_paper_to_collection(
            created_paper.id, created_collection.id
        )
        assert success is True

        # 测试搜索（按分类过滤）
        results = test_db.search_papers(collection_id=created_collection.id)
        assert len(results) == 1
        assert results[0].id == created_paper.id

        # 测试移除关联
        success = test_db.remove_paper_from_collection(
            created_paper.id, created_collection.id
        )
        assert success is True

        # 验证移除
        results = test_db.search_papers(collection_id=created_collection.id)
        assert len(results) == 0

    def test_paper_tag_relationships(self, test_db):
        """测试文献和标签的关联关系"""
        # 创建测试数据
        paper = Paper(
            title="Test Paper",
            file_path="/test/test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
        )
        created_paper = test_db.create_paper(paper)

        tag = Tag(name="test-tag")
        test_db.create_tag(tag)

        # 测试添加关联
        success = test_db.add_tag_to_paper(created_paper.id, "test-tag")
        assert success is True

        # 测试搜索（按标签过滤）
        results = test_db.search_papers(tag_names=["test-tag"])
        assert len(results) == 1
        assert results[0].id == created_paper.id

        # 测试移除关联
        success = test_db.remove_tag_from_paper(created_paper.id, "test-tag")
        assert success is True

        # 验证移除
        results = test_db.search_papers(tag_names=["test-tag"])
        assert len(results) == 0

    def test_get_all_papers(self, test_db):
        """测试获取所有文献"""
        # 创建测试数据
        for i in range(3):
            paper = Paper(
                title=f"Paper {i}",
                file_path=f"/test/paper{i}.pdf",
                original_filename=f"paper{i}.pdf",
                file_size=1024,
                file_hash=str(i) * 64,
            )
            test_db.create_paper(paper)

        # 测试获取所有
        all_papers = test_db.get_all_papers()
        assert len(all_papers) == 3

        # 应该按创建时间倒序排列
        titles = [paper.title for paper in all_papers]
        expected_titles = ["Paper 2", "Paper 1", "Paper 0"]
        assert titles == expected_titles

    def test_database_integrity(self, test_db):
        """测试数据库完整性约束"""
        # 测试唯一约束 - file_hash
        paper1 = Paper(
            title="Paper 1",
            file_path="/test/paper1.pdf",
            original_filename="paper1.pdf",
            file_size=1024,
            file_hash="a" * 64,
        )
        test_db.create_paper(paper1)

        paper2 = Paper(
            title="Paper 2",
            file_path="/test/paper2.pdf",
            original_filename="paper2.pdf",
            file_size=1024,
            file_hash="a" * 64,  # 相同的哈希
        )

        # 应该抛出异常（在实际数据库中）
        with pytest.raises(Exception):
            test_db.create_paper(paper2)

    def test_cascade_delete(self, test_db):
        """测试级联删除"""
        # 创建测试数据
        paper = Paper(
            title="Test Paper",
            file_path="/test/test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            file_hash="a" * 64,
        )
        created_paper = test_db.create_paper(paper)

        collection = Collection(name="Test Collection")
        created_collection = test_db.create_collection(collection)

        tag = Tag(name="test-tag")
        test_db.create_tag(tag)

        # 添加关联
        test_db.add_paper_to_collection(created_paper.id, created_collection.id)
        test_db.add_tag_to_paper(created_paper.id, "test-tag")

        # 删除文献，关联应该被级联删除
        test_db.delete_paper(created_paper.id)

        # 验证关联已被删除
        results = test_db.search_papers(collection_id=created_collection.id)
        assert len(results) == 0

        results = test_db.search_papers(tag_names=["test-tag"])
        assert len(results) == 0
