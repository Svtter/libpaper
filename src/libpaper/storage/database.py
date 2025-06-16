from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload
from pathlib import Path
from typing import List, Optional, Union
from uuid import UUID
from datetime import datetime

from ..models import Paper, Collection, Tag, PaperCollectionLink, PaperTagLink


class Database:
    """SQLModel 数据库管理类"""

    def __init__(self, db_path: Union[str, Path]):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"

        # 创建异步引擎
        self.engine = create_async_engine(
            self.db_url,
            echo=False,  # 设为 True 可以看到 SQL 日志
            future=True
        )

        # 创建会话工厂
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self) -> None:
        """创建数据库表"""
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def close(self) -> None:
        """关闭数据库连接"""
        await self.engine.dispose()

    # Paper 操作
    async def create_paper(self, paper: Paper) -> Paper:
        """创建文献记录"""
        async with self.async_session() as session:
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
            return paper

    async def get_paper_by_id(self, paper_id: UUID, with_relations: bool = False) -> Optional[Paper]:
        """根据 ID 获取文献"""
        async with self.async_session() as session:
            statement = select(Paper).where(Paper.id == paper_id)

            if with_relations:
                statement = statement.options(
                    selectinload(Paper.collections),
                    selectinload(Paper.tags)
                )

            result = await session.exec(statement)
            return result.first()

    async def get_paper_by_hash(self, file_hash: str, with_relations: bool = False) -> Optional[Paper]:
        """根据文件哈希获取文献"""
        async with self.async_session() as session:
            statement = select(Paper).where(Paper.file_hash == file_hash)

            if with_relations:
                statement = statement.options(
                    selectinload(Paper.collections),
                    selectinload(Paper.tags)
                )

            result = await session.exec(statement)
            return result.first()

    async def update_paper(self, paper: Paper) -> Paper:
        """更新文献记录"""
        paper.updated_at = datetime.now()
        async with self.async_session() as session:
            session.add(paper)
            await session.commit()
            await session.refresh(paper)
            return paper

    async def delete_paper(self, paper_id: UUID) -> bool:
        """删除文献记录"""
        async with self.async_session() as session:
            paper = await session.get(Paper, paper_id)
            if paper:
                await session.delete(paper)
                await session.commit()
                return True
            return False

    async def search_papers(
        self,
        query: Optional[str] = None,
        collection_id: Optional[UUID] = None,
        tag_names: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        with_relations: bool = False
    ) -> List[Paper]:
        """搜索文献"""
        async with self.async_session() as session:
            statement = select(Paper)

            # 添加文本搜索
            if query:
                statement = statement.where(
                    Paper.title.contains(query) |
                    Paper.abstract.contains(query) |
                    Paper.authors_json.contains(query)
                )

            # 添加分类过滤
            if collection_id:
                statement = statement.join(PaperCollectionLink).where(
                    PaperCollectionLink.collection_id == collection_id
                )

            # 添加标签过滤
            if tag_names:
                statement = statement.join(PaperTagLink).where(
                    PaperTagLink.tag_name.in_(tag_names)
                )

            if with_relations:
                statement = statement.options(
                    selectinload(Paper.collections),
                    selectinload(Paper.tags)
                )

            statement = statement.order_by(Paper.created_at.desc()).offset(offset).limit(limit)

            result = await session.exec(statement)
            return result.all()

    async def get_all_papers(self, with_relations: bool = False) -> List[Paper]:
        """获取所有文献"""
        async with self.async_session() as session:
            statement = select(Paper)

            if with_relations:
                statement = statement.options(
                    selectinload(Paper.collections),
                    selectinload(Paper.tags)
                )

            statement = statement.order_by(Paper.created_at.desc())
            result = await session.exec(statement)
            return result.all()

    # Collection 操作
    async def create_collection(self, collection: Collection) -> Collection:
        """创建分类记录"""
        async with self.async_session() as session:
            session.add(collection)
            await session.commit()
            await session.refresh(collection)
            return collection

    async def get_collection_by_id(self, collection_id: UUID, with_relations: bool = False) -> Optional[Collection]:
        """根据 ID 获取分类"""
        async with self.async_session() as session:
            statement = select(Collection).where(Collection.id == collection_id)

            if with_relations:
                statement = statement.options(
                    selectinload(Collection.papers),
                    selectinload(Collection.children),
                    selectinload(Collection.parent)
                )

            result = await session.exec(statement)
            return result.first()

    async def get_all_collections(self, with_relations: bool = False) -> List[Collection]:
        """获取所有分类"""
        async with self.async_session() as session:
            statement = select(Collection)

            if with_relations:
                statement = statement.options(
                    selectinload(Collection.papers),
                    selectinload(Collection.children),
                    selectinload(Collection.parent)
                )

            statement = statement.order_by(Collection.name)
            result = await session.exec(statement)
            return result.all()

    async def update_collection(self, collection: Collection) -> Collection:
        """更新分类记录"""
        collection.updated_at = datetime.now()
        async with self.async_session() as session:
            session.add(collection)
            await session.commit()
            await session.refresh(collection)
            return collection

    async def delete_collection(self, collection_id: UUID) -> bool:
        """删除分类记录"""
        async with self.async_session() as session:
            collection = await session.get(Collection, collection_id)
            if collection:
                await session.delete(collection)
                await session.commit()
                return True
            return False

    # Tag 操作
    async def create_tag(self, tag: Tag) -> Tag:
        """创建标签记录"""
        async with self.async_session() as session:
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
            return tag

    async def get_tag_by_name(self, name: str, with_relations: bool = False) -> Optional[Tag]:
        """根据名称获取标签"""
        async with self.async_session() as session:
            statement = select(Tag).where(Tag.name == name)

            if with_relations:
                statement = statement.options(selectinload(Tag.papers))

            result = await session.exec(statement)
            return result.first()

    async def get_all_tags(self, with_relations: bool = False) -> List[Tag]:
        """获取所有标签"""
        async with self.async_session() as session:
            statement = select(Tag)

            if with_relations:
                statement = statement.options(selectinload(Tag.papers))

            statement = statement.order_by(Tag.name)
            result = await session.exec(statement)
            return result.all()

    async def update_tag(self, tag: Tag) -> Tag:
        """更新标签记录"""
        async with self.async_session() as session:
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
            return tag

    async def delete_tag(self, tag_name: str) -> bool:
        """删除标签记录"""
        async with self.async_session() as session:
            tag = await session.get(Tag, tag_name)
            if tag:
                await session.delete(tag)
                await session.commit()
                return True
            return False

    # 关联操作
    async def add_paper_to_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
        """将文献添加到分类"""
        async with self.async_session() as session:
            # 检查关联是否已存在
            statement = select(PaperCollectionLink).where(
                PaperCollectionLink.paper_id == paper_id,
                PaperCollectionLink.collection_id == collection_id
            )
            result = await session.exec(statement)
            if result.first():
                return False  # 关联已存在

            link = PaperCollectionLink(paper_id=paper_id, collection_id=collection_id)
            session.add(link)
            await session.commit()
            return True

    async def remove_paper_from_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
        """从分类中移除文献"""
        async with self.async_session() as session:
            statement = select(PaperCollectionLink).where(
                PaperCollectionLink.paper_id == paper_id,
                PaperCollectionLink.collection_id == collection_id
            )
            result = await session.exec(statement)
            link = result.first()

            if link:
                await session.delete(link)
                await session.commit()
                return True
            return False

    async def add_tag_to_paper(self, paper_id: UUID, tag_name: str) -> bool:
        """为文献添加标签"""
        async with self.async_session() as session:
            # 检查关联是否已存在
            statement = select(PaperTagLink).where(
                PaperTagLink.paper_id == paper_id,
                PaperTagLink.tag_name == tag_name
            )
            result = await session.exec(statement)
            if result.first():
                return False  # 关联已存在

            link = PaperTagLink(paper_id=paper_id, tag_name=tag_name)
            session.add(link)
            await session.commit()
            return True

    async def remove_tag_from_paper(self, paper_id: UUID, tag_name: str) -> bool:
        """从文献移除标签"""
        async with self.async_session() as session:
            statement = select(PaperTagLink).where(
                PaperTagLink.paper_id == paper_id,
                PaperTagLink.tag_name == tag_name
            )
            result = await session.exec(statement)
            link = result.first()

            if link:
                await session.delete(link)
                await session.commit()
                return True
            return False