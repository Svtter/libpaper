from typing import Any, Dict, List, Optional
from uuid import UUID

from ..models import Collection
from ..storage.config import Config
from ..storage.database import Database


class CollectionService:
    """分类管理服务"""

    def __init__(self, config: Config):
        """
        初始化分类管理服务

        Args:
          config: 配置对象
        """
        self.config = config
        self.db = Database(config.get_database_path())

    def initialize(self) -> None:
        """初始化服务"""
        self.db.create_tables()

    def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[UUID] = None,
    ) -> Collection:
        """创建分类

        Args:
            name: 分类名称
            description: 分类描述（可选）
            parent_id: 父分类ID（可选）

        Returns:
            创建的分类对象

        Raises:
            ValueError: 参数验证失败
        """
        collection = Collection(name=name, description=description, parent_id=parent_id)
        return self.db.create_collection(collection)

    def get_collection(
        self, collection_id: UUID, with_relations: bool = True
    ) -> Optional[Collection]:
        """获取分类

        Args:
            collection_id: 分类ID
            with_relations: 是否加载关联数据

        Returns:
            分类对象或 None
        """
        return self.db.get_collection_by_id(collection_id, with_relations)

    def update_collection(
        self,
        collection_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[UUID] = None,
    ) -> Optional[Collection]:
        """更新分类信息

        Args:
            collection_id: 分类ID
            name: 新名称
            description: 新描述
            parent_id: 新父分类ID

        Returns:
            更新后的分类对象或 None
        """
        collection = self.db.get_collection_by_id(collection_id)
        if not collection:
            return None

        if name is not None:
            collection.name = name
        if description is not None:
            collection.description = description
        if parent_id is not None:
            collection.parent_id = parent_id

        return self.db.update_collection(collection)

    def delete_collection(self, collection_id: UUID) -> bool:
        """删除分类

        Args:
            collection_id: 分类ID

        Returns:
            是否删除成功
        """
        return self.db.delete_collection(collection_id)

    def list_collections(self, with_relations: bool = True) -> List[Collection]:
        """列出所有分类

        Args:
            with_relations: 是否加载关联数据

        Returns:
            分类列表
        """
        return self.db.get_all_collections(with_relations)

    def get_root_collections(self, with_relations: bool = True) -> List[Collection]:
        """获取根分类（没有父分类的分类）

        Args:
            with_relations: 是否加载关联数据

        Returns:
            根分类列表
        """
        all_collections = self.db.get_all_collections(with_relations)
        return [c for c in all_collections if c.parent_id is None]

    def get_child_collections(
        self, parent_id: UUID, with_relations: bool = True
    ) -> List[Collection]:
        """获取子分类

        Args:
            parent_id: 父分类ID
            with_relations: 是否加载关联数据

        Returns:
            子分类列表
        """
        all_collections = self.db.get_all_collections(with_relations)
        return [c for c in all_collections if c.parent_id == parent_id]

    def build_collection_tree(self, collections: List[Collection]) -> Dict[str, Any]:
        """
        构建分类树结构

        Args:
          collections: 分类列表

        Returns:
          树形结构字典
        """
        # 创建映射
        collection_map = {str(c.id): c for c in collections}
        tree = {}

        for collection in collections:
            if collection.is_root():
                # 根分类
                tree[str(collection.id)] = {"collection": collection, "children": {}}

        # 添加子分类
        for collection in collections:
            if collection.has_parent():
                parent_id = str(collection.parent_id)
                if parent_id in tree:
                    tree[parent_id]["children"][str(collection.id)] = {
                        "collection": collection,
                        "children": {},
                    }

        return tree

    def close(self) -> None:
        """关闭服务"""
        self.db.close()
