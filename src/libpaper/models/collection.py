from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .paper import Paper


class Collection(SQLModel, table=True):
    """分类模型，支持层次化结构"""

    __tablename__ = "collections"

    id: UUID = Field(
        default_factory=uuid4, primary_key=True, description="分类唯一标识"
    )
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    parent_id: Optional[UUID] = Field(
        None, foreign_key="collections.id", description="父分类ID，支持层次化结构"
    )

    # 系统字段
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @property
    def papers(self) -> List["Paper"]:
        """获取文献列表（需要从数据库查询）"""
        # 在实际使用中，这个值需要从数据库查询
        return []

    @property
    def parent(self) -> Optional["Collection"]:
        """获取父分类（需要从数据库查询）"""
        # 在实际使用中，这个值需要从数据库查询
        return None

    @property
    def children(self) -> List["Collection"]:
        """获取子分类列表（需要从数据库查询）"""
        # 在实际使用中，这个值需要从数据库查询
        return []

    @property
    def paper_count(self) -> int:
        """获取文献数量"""
        return len(self.papers)

    def validate_name(self) -> None:
        """验证分类名称"""
        name = self.name.strip()
        if not name:
            raise ValueError("分类名称不能为空")
        if len(name) > 100:
            raise ValueError("分类名称长度不能超过100个字符")
        self.name = name

    def validate_parent_id(self) -> None:
        """验证父分类ID，防止自引用"""
        if self.parent_id and self.parent_id == self.id:
            raise ValueError("分类不能将自己设为父分类")

    def model_post_init(self, __context) -> None:
        """模型初始化后的验证"""
        self.validate_name()
        self.validate_parent_id()

    def is_root(self) -> bool:
        """判断是否为根分类"""
        return self.parent_id is None

    def has_parent(self) -> bool:
        """判断是否有父分类"""
        return self.parent_id is not None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "paper_count": self.paper_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Collection":
        """从字典创建 Collection 实例"""
        # 处理特殊字段
        if "parent_id" in data and data["parent_id"]:
            data["parent_id"] = UUID(data["parent_id"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # 移除不是模型字段的数据
        model_data = {k: v for k, v in data.items() if k != "paper_count"}

        return cls(**model_data)

    @classmethod
    def from_json(cls, json_str: str) -> "Collection":
        """从 JSON 字符串创建 Collection 实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
