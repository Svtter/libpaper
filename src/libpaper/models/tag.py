from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re


class Tag(BaseModel):
    """标签模型"""

    name: str = Field(..., min_length=1, max_length=50, description="标签名称，作为主键")
    description: Optional[str] = Field(None, max_length=200, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色（十六进制格式）")
    paper_count: int = Field(default=0, ge=0, description="使用此标签的文献数量")

    # 系统字段
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('name')
    def validate_name(cls, v):
        """验证标签名称"""
        v = v.strip().lower()  # 标签名称统一小写
        if not v:
            raise ValueError('标签名称不能为空')
        if len(v) > 50:
            raise ValueError('标签名称长度不能超过50个字符')

        # 标签名称只能包含字母、数字、中文、连字符和下划线
        if not re.match(r'^[\w\u4e00-\u9fff-]+$', v):
            raise ValueError('标签名称只能包含字母、数字、中文、连字符和下划线')

        return v

    @validator('color')
    def validate_color(cls, v):
        """验证颜色格式"""
        if v is None:
            return v

        # 移除可能的 # 前缀
        v = v.lstrip('#')

        # 验证十六进制颜色格式
        if not re.match(r'^[0-9A-Fa-f]{6}$', v):
            raise ValueError('颜色必须是6位十六进制格式（如：FF5722）')

        return f"#{v.upper()}"

    @validator('description')
    def validate_description(cls, v):
        """验证描述"""
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError('标签描述长度不能超过200个字符')
            return v if v else None
        return v

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return self.dict()

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return self.json()

    @classmethod
    def from_dict(cls, data: dict) -> 'Tag':
        """从字典创建 Tag 实例"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Tag':
        """从 JSON 字符串创建 Tag 实例"""
        return cls.parse_raw(json_str)

    def __str__(self) -> str:
        """字符串表示"""
        return self.name

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"Tag(name='{self.name}', color='{self.color}', paper_count={self.paper_count})"