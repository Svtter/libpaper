from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import json


class PaperCollectionLink(SQLModel, table=True):
  """文献和分类的关联表"""
  __tablename__ = "paper_collections"

  paper_id: UUID = Field(foreign_key="papers.id", primary_key=True)
  collection_id: UUID = Field(foreign_key="collections.id", primary_key=True)
  added_at: datetime = Field(default_factory=datetime.now)


class PaperTagLink(SQLModel, table=True):
  """文献和标签的关联表"""
  __tablename__ = "paper_tags"

  paper_id: UUID = Field(foreign_key="papers.id", primary_key=True)
  tag_name: str = Field(foreign_key="tags.name", primary_key=True)
  added_at: datetime = Field(default_factory=datetime.now)


class Paper(SQLModel, table=True):
  """文献模型"""
  __tablename__ = "papers"

  id: UUID = Field(default_factory=uuid4, primary_key=True, description="文献唯一标识")
  title: str = Field(..., description="文献标题")
  file_path: str = Field(..., unique=True, description="PDF 文件存储路径")
  original_filename: str = Field(..., description="原始文件名")
  file_size: int = Field(..., ge=0, description="文件大小（字节）")
  file_hash: str = Field(..., unique=True, description="文件 SHA256 哈希值")

  # 可选元数据
  authors_json: Optional[str] = Field(None, description="作者列表（JSON格式）")
  abstract: Optional[str] = Field(None, description="摘要")
  publication_date: Optional[datetime] = Field(None, description="发表日期")
  journal: Optional[str] = Field(None, description="期刊名称")
  doi: Optional[str] = Field(None, description="DOI")

  # 系统字段
  created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
  updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

  # 关系
  collections: List["Collection"] = Relationship(
    back_populates="papers",
    link_model=PaperCollectionLink
  )
  tags: List["Tag"] = Relationship(
    back_populates="papers",
    link_model=PaperTagLink
  )

  @property
  def authors(self) -> List[str]:
    """获取作者列表"""
    if self.authors_json:
      try:
        return json.loads(self.authors_json)
      except json.JSONDecodeError:
        return []
    return []

  @authors.setter
  def authors(self, value: List[str]) -> None:
    """设置作者列表"""
    self.authors_json = json.dumps(value) if value else None

  @property
  def collection_ids(self) -> List[UUID]:
    """获取分类ID列表"""
    return [collection.id for collection in self.collections]

  @property
  def tag_names(self) -> List[str]:
    """获取标签名称列表"""
    return [tag.name for tag in self.tags]

  def validate_file_hash(self) -> None:
    """验证 SHA256 哈希值格式"""
    if len(self.file_hash) != 64:
      raise ValueError('SHA256 哈希值必须是64位十六进制字符串')
    try:
      int(self.file_hash, 16)
    except ValueError:
      raise ValueError('SHA256 哈希值必须是有效的十六进制字符串')
    self.file_hash = self.file_hash.lower()

  def validate_doi(self) -> None:
    """验证 DOI 格式"""
    if self.doi and not self.doi.startswith('10.'):
      raise ValueError('DOI 必须以 "10." 开头')

  def model_post_init(self, __context) -> None:
    """模型初始化后的验证"""
    self.validate_file_hash()
    self.validate_doi()

  def to_dict(self) -> dict:
    """转换为字典格式"""
    return {
      "id": str(self.id),
      "title": self.title,
      "file_path": self.file_path,
      "original_filename": self.original_filename,
      "file_size": self.file_size,
      "file_hash": self.file_hash,
      "authors": self.authors,
      "abstract": self.abstract,
      "publication_date": self.publication_date.isoformat() if self.publication_date else None,
      "journal": self.journal,
      "doi": self.doi,
      "collection_ids": [str(cid) for cid in self.collection_ids],
      "tag_names": self.tag_names,
      "created_at": self.created_at.isoformat(),
      "updated_at": self.updated_at.isoformat()
    }

  def to_json(self) -> str:
    """转换为 JSON 字符串"""
    return json.dumps(self.to_dict())

  @classmethod
  def from_dict(cls, data: dict) -> 'Paper':
    """从字典创建 Paper 实例"""
    # 处理特殊字段
    if 'authors' in data:
      data['authors_json'] = json.dumps(data.pop('authors'))
    if 'publication_date' in data and isinstance(data['publication_date'], str):
      data['publication_date'] = datetime.fromisoformat(data['publication_date'])
    if 'created_at' in data and isinstance(data['created_at'], str):
      data['created_at'] = datetime.fromisoformat(data['created_at'])
    if 'updated_at' in data and isinstance(data['updated_at'], str):
      data['updated_at'] = datetime.fromisoformat(data['updated_at'])

    # 移除不是模型字段的数据
    model_data = {k: v for k, v in data.items()
                  if k not in ['collection_ids', 'tag_names']}

    return cls(**model_data)

  @classmethod
  def from_json(cls, json_str: str) -> 'Paper':
    """从 JSON 字符串创建 Paper 实例"""
    data = json.loads(json_str)
    return cls.from_dict(data)