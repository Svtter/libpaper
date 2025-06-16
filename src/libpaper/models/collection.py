from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class Collection(BaseModel):
    """分类模型，支持层次化结构"""

    id: UUID = Field(default_factory=uuid4, description="分类唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    parent_id: Optional[UUID] = Field(None, description="父分类ID，支持层次化结构")
    paper_count: int = Field(default=0, ge=0, description="包含的文献数量")

    # 系统字段
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

    @validator('name')
    def validate_name(cls, v):
        """验证分类名称"""
        v = v.strip()
        if not v:
            raise ValueError('分类名称不能为空')
        if len(v) > 100:
            raise ValueError('分类名称长度不能超过100个字符')
        return v

    @validator('parent_id')
    def validate_parent_id(cls, v, values):
        """验证父分类ID，防止自引用"""
        if v and 'id' in values and v == values['id']:
            raise ValueError('分类不能将自己设为父分类')
        return v

    def is_root(self) -> bool:
        """判断是否为根分类"""
        return self.parent_id is None

    def has_parent(self) -> bool:
        """判断是否有父分类"""
        return self.parent_id is not None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return self.dict()

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return self.json()

    @classmethod
    def from_dict(cls, data: dict) -> 'Collection':
        """从字典创建 Collection 实例"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Collection':
        """从 JSON 字符串创建 Collection 实例"""
        return cls.parse_raw(json_str)