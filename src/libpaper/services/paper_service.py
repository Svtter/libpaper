"""文献服务"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..extractors.pdf_extractor import PDFExtractor
from ..models import Paper
from ..storage.database import Database
from ..storage.file_manager import FileManager


class PaperService:
    """文献服务"""

    def __init__(self, db: Database, file_manager: FileManager):
        """初始化文献服务

        Args:
            db: 数据库实例
            file_manager: 文件管理器实例
        """
        self.db = db
        self.file_manager = file_manager
        self.pdf_extractor = PDFExtractor()

    def initialize(self) -> None:
        """初始化服务"""
        self.db.create_tables()

    # 核心功能
    def add_paper(
        self,
        source_path: Path,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        collection_ids: Optional[List[UUID]] = None,
        override_metadata: Optional[Dict[str, Any]] = None,
    ) -> Paper:
        """添加文献

        Args:
            source_path: 源文件路径
            title: 手动指定的标题（可选）
            tags: 标签列表（可选）
            collection_ids: 分类ID列表（可选）
            override_metadata: 覆盖的元数据（可选）

        Returns:
            创建的文献实例

        Raises:
            FileNotFoundError: 源文件不存在
            ValueError: 文件格式不支持或其他验证错误
            RuntimeError: 文件处理失败
        """
        if not source_path.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")

        if source_path.suffix.lower() != ".pdf":
            raise ValueError("目前只支持 PDF 文件")

        try:
            # 处理文件
            file_hash, file_size, storage_path = self.file_manager.process_file(
                source_path
            )

            # 提取元数据
            extracted_metadata = self.pdf_extractor.extract_metadata(source_path)

            # 合并元数据
            metadata = extracted_metadata.copy()
            if override_metadata:
                metadata.update(override_metadata)

            # 创建文献实例
            paper = Paper(
                title=title or metadata.get("title", source_path.stem),
                file_path=str(storage_path),
                original_filename=source_path.name,
                file_size=file_size,
                file_hash=file_hash,
                authors=metadata.get("authors", []),
                abstract=metadata.get("abstract"),
                publication_date=metadata.get("publication_date"),
                journal=metadata.get("journal"),
                doi=metadata.get("doi"),
            )

            # 保存到数据库
            saved_paper = self.db.create_paper(paper)

            # 添加标签
            if tags:
                for tag_name in tags:
                    self.db.add_tag_to_paper(saved_paper.id, tag_name)

            # 添加到分类
            if collection_ids:
                for collection_id in collection_ids:
                    self.db.add_paper_to_collection(saved_paper.id, collection_id)

            return saved_paper

        except Exception as e:
            # 清理可能已创建的文件
            try:
                if "storage_path" in locals():
                    Path(storage_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError(f"添加文献失败: {e}") from e

    def get_paper(self, paper_id: UUID, with_relations: bool = True) -> Optional[Paper]:
        """获取文献

        Args:
            paper_id: 文献ID
            with_relations: 是否包含关联数据

        Returns:
            文献实例，如果不存在则返回None
        """
        return self.db.get_paper_by_id(paper_id, with_relations)

    def update_paper(
        self,
        paper_id: UUID,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        abstract: Optional[str] = None,
        publication_date: Optional[str] = None,
        journal: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> Optional[Paper]:
        """更新文献信息

        Args:
            paper_id: 文献ID
            title: 新标题
            authors: 新作者列表
            abstract: 新摘要
            publication_date: 新发表日期
            journal: 新期刊
            doi: 新DOI

        Returns:
            更新后的文献实例，如果不存在则返回None
        """
        paper = self.db.get_paper_by_id(paper_id)
        if not paper:
            return None

        # 更新字段
        if title is not None:
            paper.title = title
        if authors is not None:
            paper.authors = authors
        if abstract is not None:
            paper.abstract = abstract
        if publication_date is not None:
            paper.publication_date = publication_date
        if journal is not None:
            paper.journal = journal
        if doi is not None:
            paper.doi = doi

        return self.db.update_paper(paper)

    def delete_paper(self, paper_id: UUID) -> bool:
        """删除文献

        Args:
            paper_id: 文献ID

        Returns:
            是否成功删除
        """
        # 获取文献信息
        paper = self.db.get_paper_by_id(paper_id)
        if not paper:
            return False

        # 删除文件
        file_path = Path(paper.file_path)
        if file_path.exists():
            self.file_manager.delete_file(file_path)

        # 删除数据库记录（级联删除关联）
        return self.db.delete_paper(paper_id)

    def search_papers(
        self,
        query: Optional[str] = None,
        collection_id: Optional[UUID] = None,
        tag_names: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        with_relations: bool = True,
    ) -> List[Paper]:
        """搜索文献

        Args:
            query: 搜索关键词
            collection_id: 分类ID过滤
            tag_names: 标签名称过滤
            limit: 结果数量限制
            offset: 结果偏移量
            with_relations: 是否包含关联数据

        Returns:
            匹配的文献列表
        """
        return self.db.search_papers(
            query=query,
            collection_id=collection_id,
            tag_names=tag_names,
            limit=limit,
            offset=offset,
            with_relations=with_relations,
        )

    def list_papers(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        with_relations: bool = True,
    ) -> List[Paper]:
        """列出所有文献

        Args:
            limit: 结果数量限制
            offset: 结果偏移量
            with_relations: 是否包含关联数据

        Returns:
            文献列表
        """
        papers = self.db.get_all_papers(with_relations)

        # 手动分页
        if limit is not None:
            return papers[offset : offset + limit]
        return papers[offset:]

    def add_tag_to_paper(self, paper_id: UUID, tag_name: str) -> bool:
        """为文献添加标签

        Args:
            paper_id: 文献ID
            tag_name: 标签名称

        Returns:
            是否成功添加
        """
        return self.db.add_tag_to_paper(paper_id, tag_name)

    def remove_tag_from_paper(self, paper_id: UUID, tag_name: str) -> bool:
        """从文献移除标签

        Args:
            paper_id: 文献ID
            tag_name: 标签名称

        Returns:
            是否成功移除
        """
        return self.db.remove_tag_from_paper(paper_id, tag_name)

    def add_paper_to_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
        """将文献添加到分类

        Args:
            paper_id: 文献ID
            collection_id: 分类ID

        Returns:
            是否成功添加
        """
        return self.db.add_paper_to_collection(paper_id, collection_id)

    def remove_paper_from_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
        """从分类中移除文献

        Args:
            paper_id: 文献ID
            collection_id: 分类ID

        Returns:
            是否成功移除
        """
        return self.db.remove_paper_from_collection(paper_id, collection_id)

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            包含存储统计的字典
        """
        papers = self.db.get_all_papers()

        total_size = sum(paper.file_size for paper in papers)
        total_count = len(papers)

        return {
            "total_papers": total_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_size_mb": round(
                total_size / (1024 * 1024) / max(total_count, 1), 2
            ),
        }

    def close(self) -> None:
        """关闭服务"""
        self.db.close()
