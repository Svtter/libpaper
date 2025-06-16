from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models import Paper
from ..storage.database import Database
from ..storage.file_manager import FileManager
from ..storage.config import Config
from ..extractors.pdf_extractor import PDFExtractor


class PaperService:
  """文献管理服务"""

  def __init__(self, config: Config):
    """
    初始化文献管理服务

    Args:
      config: 配置对象
    """
    self.config = config
    self.db = Database(config.get_database_path())
    self.file_manager = FileManager(config)
    self.pdf_extractor = PDFExtractor()

  async def initialize(self) -> None:
    """初始化服务（创建数据库表等）"""
    await self.db.create_tables()
    self.config.ensure_directories()

  async def add_paper(
    self,
    file_path: str,
    title: Optional[str] = None,
    authors: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    collection_ids: Optional[List[UUID]] = None
  ) -> Paper:
    """
    添加新文献

    Args:
      file_path: PDF 文件路径
      title: 自定义标题（可选）
      authors: 作者列表（可选）
      tags: 标签列表（可选）
      collection_ids: 分类ID列表（可选）

    Returns:
      创建的文献对象

    Raises:
      ValueError: 文件无效或不存在
      FileExistsError: 文件已存在
    """
    source_path = Path(file_path).resolve()

    if not source_path.exists():
      raise ValueError(f"文件不存在: {source_path}")

    # 处理文件（验证、计算哈希、存储）
    file_hash, file_size, storage_path = await self.file_manager.process_file(source_path)

    # 提取元数据
    extracted_metadata = await self.pdf_extractor.extract_metadata(source_path)

    # 创建文献对象
    paper = Paper(
      title=title or extracted_metadata.get('title', source_path.stem),
      file_path=str(storage_path),
      original_filename=source_path.name,
      file_size=file_size,
      file_hash=file_hash,
      abstract=extracted_metadata.get('abstract'),
      publication_date=extracted_metadata.get('creation_date'),
      doi=extracted_metadata.get('doi')
    )

    # 设置作者
    if authors:
      paper.authors = authors
    elif 'authors' in extracted_metadata:
      paper.authors = extracted_metadata['authors']

    # 保存到数据库
    saved_paper = await self.db.create_paper(paper)

    # 添加标签关联
    if tags:
      for tag_name in tags:
        await self.db.add_tag_to_paper(saved_paper.id, tag_name)

    # 添加分类关联
    if collection_ids:
      for collection_id in collection_ids:
        await self.db.add_paper_to_collection(saved_paper.id, collection_id)

    return saved_paper

  async def get_paper(self, paper_id: UUID, with_relations: bool = True) -> Optional[Paper]:
    """
    获取文献

    Args:
      paper_id: 文献ID
      with_relations: 是否加载关联数据

    Returns:
      文献对象或 None
    """
    return await self.db.get_paper_by_id(paper_id, with_relations)

  async def update_paper(
    self,
    paper_id: UUID,
    title: Optional[str] = None,
    authors: Optional[List[str]] = None,
    abstract: Optional[str] = None,
    journal: Optional[str] = None,
    doi: Optional[str] = None
  ) -> Optional[Paper]:
    """
    更新文献信息

    Args:
      paper_id: 文献ID
      title: 新标题
      authors: 新作者列表
      abstract: 新摘要
      journal: 期刊名称
      doi: DOI

    Returns:
      更新后的文献对象或 None
    """
    paper = await self.db.get_paper_by_id(paper_id)
    if not paper:
      return None

    # 更新字段
    if title is not None:
      paper.title = title
    if authors is not None:
      paper.authors = authors
    if abstract is not None:
      paper.abstract = abstract
    if journal is not None:
      paper.journal = journal
    if doi is not None:
      paper.doi = doi

    return await self.db.update_paper(paper)

  async def delete_paper(self, paper_id: UUID) -> bool:
    """
    删除文献（包括文件）

    Args:
      paper_id: 文献ID

    Returns:
      是否删除成功
    """
    # 获取文献信息
    paper = await self.db.get_paper_by_id(paper_id)
    if not paper:
      return False

    # 删除文件
    file_path = Path(paper.file_path)
    await self.file_manager.delete_file(file_path)

    # 删除数据库记录
    return await self.db.delete_paper(paper_id)

  async def search_papers(
    self,
    query: Optional[str] = None,
    collection_id: Optional[UUID] = None,
    tag_names: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0,
    with_relations: bool = True
  ) -> List[Paper]:
    """
    搜索文献

    Args:
      query: 搜索关键词
      collection_id: 分类ID筛选
      tag_names: 标签名称筛选
      limit: 返回数量限制
      offset: 偏移量
      with_relations: 是否加载关联数据

    Returns:
      文献列表
    """
    return await self.db.search_papers(
      query=query,
      collection_id=collection_id,
      tag_names=tag_names,
      limit=limit,
      offset=offset,
      with_relations=with_relations
    )

  async def list_papers(
    self,
    limit: int = 20,
    offset: int = 0,
    with_relations: bool = True
  ) -> List[Paper]:
    """
    列出所有文献

    Args:
      limit: 返回数量限制
      offset: 偏移量
      with_relations: 是否加载关联数据

    Returns:
      文献列表
    """
    papers = await self.db.get_all_papers(with_relations)
    return papers[offset:offset + limit]

  async def add_tag_to_paper(self, paper_id: UUID, tag_name: str) -> bool:
    """
    为文献添加标签

    Args:
      paper_id: 文献ID
      tag_name: 标签名称

    Returns:
      是否添加成功
    """
    return await self.db.add_tag_to_paper(paper_id, tag_name)

  async def remove_tag_from_paper(self, paper_id: UUID, tag_name: str) -> bool:
    """
    从文献移除标签

    Args:
      paper_id: 文献ID
      tag_name: 标签名称

    Returns:
      是否移除成功
    """
    return await self.db.remove_tag_from_paper(paper_id, tag_name)

  async def add_paper_to_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
    """
    将文献添加到分类

    Args:
      paper_id: 文献ID
      collection_id: 分类ID

    Returns:
      是否添加成功
    """
    return await self.db.add_paper_to_collection(paper_id, collection_id)

  async def remove_paper_from_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
    """
    从分类中移除文献

    Args:
      paper_id: 文献ID
      collection_id: 分类ID

    Returns:
      是否移除成功
    """
    return await self.db.remove_paper_from_collection(paper_id, collection_id)

  async def get_storage_stats(self) -> Dict[str, Any]:
    """
    获取存储统计信息

    Returns:
      存储统计信息
    """
    file_stats = self.file_manager.get_storage_stats()

    # 获取数据库统计
    papers = await self.db.get_all_papers()

    return {
      **file_stats,
      'total_papers': len(papers),
      'papers_with_abstract': len([p for p in papers if p.abstract]),
      'papers_with_doi': len([p for p in papers if p.doi])
    }

  async def close(self) -> None:
    """关闭服务"""
    await self.db.close()