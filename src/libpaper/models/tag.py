from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
import re
import json


class Tag(SQLModel, table=True):
    """标签模型"""
    __tablename__ = "tags"

    name: str = Field(..., min_length=1, max_length=50, primary_key=True, description="标签名称，作为主键")
    description: Optional[str] = Field(None, max_length=200, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色（十六进制格式）")

    # 系统字段
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    # 关系
    papers: List["Paper"] = Relationship(
        back_populates="tags",
        link_model="PaperTagLink"
    )

    @property
    def paper_count(self) -> int:
        """获取使用此标签的文献数量"""
        return len(self.papers)

    def validate_name(self) -> None:
        """验证标签名称"""
        name = self.name.strip().lower()  # 标签名称统一小写
        if not name:
            raise ValueError('标签名称不能为空')
        if len(name) > 50:
            raise ValueError('标签名称长度不能超过50个字符')

        # 标签名称只能包含字母、数字、中文、连字符和下划线
        if not re.match(r'^[\w\u4e00-\u9fff-]+$', name):
            raise ValueError('标签名称只能包含字母、数字、中文、连字符和下划线')

        self.name = name

    def validate_color(self) -> None:
        """验证颜色格式"""
        if self.color is None:
            return

        # 移除可能的 # 前缀
        color = self.color.lstrip('#')

        # 验证十六进制颜色格式
        if not re.match(r'^[0-9A-Fa-f]{6}$', color):
            raise ValueError('颜色必须是6位十六进制格式（如：FF5722）')

        self.color = f"#{color.upper()}"

    def validate_description(self) -> None:
        """验证描述"""
        if self.description is not None:
            description = self.description.strip()
            if len(description) > 200:
                raise ValueError('标签描述长度不能超过200个字符')
            self.description = description if description else None

    def model_post_init(self, __context) -> None:
        """模型初始化后的验证"""
        self.validate_name()
        self.validate_color()
        self.validate_description()

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "paper_count": self.paper_count,
            "created_at": self.created_at.isoformat()
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> 'Tag':
        """从字典创建 Tag 实例"""
        # 处理特殊字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])

        # 移除不是模型字段的数据
        model_data = {k: v for k, v in data.items() if k != 'paper_count'}

        return cls(**model_data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Tag':
        """从 JSON 字符串创建 Tag 实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """字符串表示"""
        return self.name

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"Tag(name='{self.name}', color='{self.color}', paper_count={self.paper_count})"