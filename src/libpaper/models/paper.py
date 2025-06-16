from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import json


class Paper(BaseModel):
    """文献模型"""

    id: UUID = Field(default_factory=uuid4, description="文献唯一标识")
    title: str = Field(..., description="文献标题")
    file_path: str = Field(..., description="PDF 文件存储路径")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    file_hash: str = Field(..., description="文件 SHA256 哈希值")

    # 可选元数据
    authors: Optional[List[str]] = Field(default_factory=list, description="作者列表")
    abstract: Optional[str] = Field(None, description="摘要")
    publication_date: Optional[datetime] = Field(None, description="发表日期")
    journal: Optional[str] = Field(None, description="期刊名称")
    doi: Optional[str] = Field(None, description="DOI")

    # 分类和标签
    collection_ids: List[UUID] = Field(default_factory=list, description="所属分类ID列表")
    tag_names: List[str] = Field(default_factory=list, description="标签名称列表")

    # 系统字段
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

    @validator('file_hash')
    def validate_file_hash(cls, v):
        """验证 SHA256 哈希值格式"""
        if len(v) != 64:
            raise ValueError('SHA256 哈希值必须是64位十六进制字符串')
        try:
            int(v, 16)
        except ValueError:
            raise ValueError('SHA256 哈希值必须是有效的十六进制字符串')
        return v.lower()

    @validator('doi')
    def validate_doi(cls, v):
        """验证 DOI 格式"""
        if v and not v.startswith('10.'):
            raise ValueError('DOI 必须以 "10." 开头')
        return v

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return self.dict()

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return self.json()

    @classmethod
    def from_dict(cls, data: dict) -> 'Paper':
        """从字典创建 Paper 实例"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Paper':
        """从 JSON 字符串创建 Paper 实例"""
        return cls.parse_raw(json_str)