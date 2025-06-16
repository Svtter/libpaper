from typing import List, Optional
from uuid import UUID

from ..models import Tag
from ..storage.config import Config
from ..storage.database import Database


class TagService:
    """标签管理服务"""

    def __init__(self, config: Config):
        """
        初始化标签管理服务

        Args:
          config: 配置对象
        """
        self.config = config
        self.db = Database(config.get_database_path())

    def initialize(self) -> None:
        """初始化服务"""
        self.db.create_tables()

    def create_tag(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Tag:
        """创建标签

        Args:
            name: 标签名称
            description: 标签描述（可选）
            color: 标签颜色（可选）

        Returns:
            创建的标签对象

        Raises:
            ValueError: 参数验证失败
            IntegrityError: 标签名称已存在
        """
        tag = Tag(name=name, description=description, color=color)
        return self.db.create_tag(tag)

    def get_tag(self, name: str, with_relations: bool = True) -> Optional[Tag]:
        """获取标签

        Args:
            name: 标签名称
            with_relations: 是否加载关联数据

        Returns:
            标签对象或 None
        """
        return self.db.get_tag_by_name(name, with_relations)

    def update_tag(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Optional[Tag]:
        """更新标签信息

        Args:
            name: 标签名称
            description: 新描述
            color: 新颜色

        Returns:
            更新后的标签对象或 None
        """
        tag = self.db.get_tag_by_name(name)
        if not tag:
            return None

        if description is not None:
            tag.description = description
        if color is not None:
            tag.color = color

        return self.db.update_tag(tag)

    def delete_tag(self, name: str) -> bool:
        """删除标签

        Args:
            name: 标签名称

        Returns:
            是否删除成功
        """
        return self.db.delete_tag(name)

    def list_tags(self, with_relations: bool = True) -> List[Tag]:
        """列出所有标签

        Args:
            with_relations: 是否加载关联数据

        Returns:
            标签列表
        """
        return self.db.get_all_tags(with_relations)

    def search_tags(self, query: str, with_relations: bool = False) -> List[Tag]:
        """搜索标签

        Args:
            query: 搜索关键词
            with_relations: 是否加载关联数据

        Returns:
            匹配的标签列表
        """
        all_tags = self.db.get_all_tags(with_relations)
        query_lower = query.lower()

        return [
            tag
            for tag in all_tags
            if query_lower in tag.name.lower()
            or (tag.description and query_lower in tag.description.lower())
        ]

    def get_popular_tags(
        self, limit: int = 10, with_relations: bool = False
    ) -> List[Tag]:
        """获取热门标签

        Args:
            limit: 返回数量限制
            with_relations: 是否加载关联数据

        Returns:
            按使用频率排序的标签列表
        """
        all_tags = self.db.get_all_tags(with_relations)

        # 根据 paper_count 排序
        return sorted(all_tags, key=lambda t: t.paper_count, reverse=True)[:limit]

    def get_unused_tags(self, with_relations: bool = False) -> List[Tag]:
        """获取未使用的标签

        Args:
            with_relations: 是否加载关联数据

        Returns:
            未被任何文献使用的标签列表
        """
        all_tags = self.db.get_all_tags(with_relations)
        return [tag for tag in all_tags if tag.paper_count == 0]

    def cleanup_unused_tags(self) -> int:
        """清理未使用的标签

        Returns:
            清理的标签数量
        """
        unused_tags = self.get_unused_tags()
        deleted_count = 0

        for tag in unused_tags:
            if self.db.delete_tag(tag.name):
                deleted_count += 1

        return deleted_count

    def close(self) -> None:
        """关闭服务"""
        self.db.close()
