from typing import List, Optional
from uuid import UUID

from ..models import Tag
from ..storage.database import Database
from ..storage.config import Config


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

  async def initialize(self) -> None:
    """初始化服务"""
    await self.db.create_tables()

  async def create_tag(
    self,
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None
  ) -> Tag:
    """
    创建新标签

    Args:
      name: 标签名称
      description: 标签描述
      color: 标签颜色

    Returns:
      创建的标签对象
    """
    tag = Tag(
      name=name,
      description=description,
      color=color
    )

    return await self.db.create_tag(tag)

  async def get_tag(self, name: str, with_relations: bool = True) -> Optional[Tag]:
    """
    获取标签

    Args:
      name: 标签名称
      with_relations: 是否加载关联数据

    Returns:
      标签对象或 None
    """
    return await self.db.get_tag_by_name(name, with_relations)

  async def update_tag(
    self,
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None
  ) -> Optional[Tag]:
    """
    更新标签信息

    Args:
      name: 标签名称
      description: 新描述
      color: 新颜色

    Returns:
      更新后的标签对象或 None
    """
    tag = await self.db.get_tag_by_name(name)
    if not tag:
      return None

    # 更新字段
    if description is not None:
      tag.description = description
    if color is not None:
      tag.color = color

    return await self.db.update_tag(tag)

  async def delete_tag(self, name: str) -> bool:
    """
    删除标签

    Args:
      name: 标签名称

    Returns:
      是否删除成功
    """
    return await self.db.delete_tag(name)

  async def list_tags(self, with_relations: bool = True) -> List[Tag]:
    """
    列出所有标签

    Args:
      with_relations: 是否加载关联数据

    Returns:
      标签列表
    """
    return await self.db.get_all_tags(with_relations)

  async def search_tags(self, query: str, with_relations: bool = False) -> List[Tag]:
    """
    搜索标签

    Args:
      query: 搜索关键词
      with_relations: 是否加载关联数据

    Returns:
      匹配的标签列表
    """
    all_tags = await self.db.get_all_tags(with_relations)

    # 简单的名称匹配搜索
    query_lower = query.lower()
    matching_tags = []

    for tag in all_tags:
      if (query_lower in tag.name.lower() or
          (tag.description and query_lower in tag.description.lower())):
        matching_tags.append(tag)

    return matching_tags

  async def get_popular_tags(self, limit: int = 10, with_relations: bool = False) -> List[Tag]:
    """
    获取热门标签（按使用次数排序）

    Args:
      limit: 返回数量限制
      with_relations: 是否加载关联数据

    Returns:
      热门标签列表
    """
    all_tags = await self.db.get_all_tags(with_relations)

    # 按使用次数排序
    sorted_tags = sorted(all_tags, key=lambda t: t.paper_count, reverse=True)

    return sorted_tags[:limit]

  async def get_unused_tags(self, with_relations: bool = False) -> List[Tag]:
    """
    获取未使用的标签

    Args:
      with_relations: 是否加载关联数据

    Returns:
      未使用的标签列表
    """
    all_tags = await self.db.get_all_tags(with_relations)
    return [tag for tag in all_tags if tag.paper_count == 0]

  async def cleanup_unused_tags(self) -> int:
    """
    清理未使用的标签

    Returns:
      删除的标签数量
    """
    unused_tags = await self.get_unused_tags()
    deleted_count = 0

    for tag in unused_tags:
      if await self.db.delete_tag(tag.name):
        deleted_count += 1

    return deleted_count

  async def close(self) -> None:
    """关闭服务"""
    await self.db.close()