from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
from uuid import UUID

from sqlmodel import Session, SQLModel, create_engine, select

from ..models import Collection, Paper, PaperCollectionLink, PaperTagLink, Tag


class Database:
    """数据库操作类"""

    def __init__(self, db_path: Union[str, Path]):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_url = f"sqlite:///{self.db_path}"

        # 创建引擎
        self.engine = create_engine(
            self.db_url,
            echo=False,  # 设为True可以看到SQL日志
            connect_args={"check_same_thread": False},  # SQLite需要这个配置
        )

    def create_tables(self) -> None:
        """创建所有表"""
        SQLModel.metadata.create_all(self.engine)

    def close(self) -> None:
        """关闭数据库连接"""
        self.engine.dispose()

    # Paper 操作
    def create_paper(self, paper: Paper) -> Paper:
        """创建文献记录"""
        with Session(self.engine) as session:
            session.add(paper)
            session.commit()
            session.refresh(paper)
            return paper

    def get_paper_by_id(
        self, paper_id: UUID, with_relations: bool = False
    ) -> Optional[Paper]:
        """根据 ID 获取文献"""
        with Session(self.engine) as session:
            statement = select(Paper).where(Paper.id == paper_id)
            result = session.exec(statement)
            return result.first()

    def get_paper_by_hash(
        self, file_hash: str, with_relations: bool = False
    ) -> Optional[Paper]:
        """根据文件哈希获取文献"""
        with Session(self.engine) as session:
            statement = select(Paper).where(Paper.file_hash == file_hash)
            result = session.exec(statement)
            return result.first()

    def update_paper(self, paper: Paper) -> Paper:
        """更新文献记录"""
        paper.updated_at = datetime.now()
        with Session(self.engine) as session:
            session.add(paper)
            session.commit()
            session.refresh(paper)
            return paper

    def delete_paper(self, paper_id: UUID) -> bool:
        """删除文献记录"""
        with Session(self.engine) as session:
            paper = session.get(Paper, paper_id)
            if paper:
                session.delete(paper)
                session.commit()
                return True
            return False

    def search_papers(
        self,
        query: Optional[str] = None,
        collection_id: Optional[UUID] = None,
        tag_names: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        with_relations: bool = False,
    ) -> List[Paper]:
        """搜索文献"""
        with Session(self.engine) as session:
            statement = select(Paper)

            # 添加文本搜索
            if query:
                statement = statement.where(
                    Paper.title.contains(query)
                    | Paper.abstract.contains(query)
                    | Paper.authors_json.contains(query)
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

            statement = (
                statement.order_by(Paper.created_at.desc()).offset(offset).limit(limit)
            )

            result = session.exec(statement)
            return result.all()

    def get_all_papers(self, with_relations: bool = False) -> List[Paper]:
        """获取所有文献"""
        with Session(self.engine) as session:
            statement = select(Paper)
            statement = statement.order_by(Paper.created_at.desc())
            result = session.exec(statement)
            return result.all()

    # Collection 操作
    def create_collection(self, collection: Collection) -> Collection:
        """创建分类记录"""
        with Session(self.engine) as session:
            session.add(collection)
            session.commit()
            session.refresh(collection)
            return collection

    def get_collection_by_id(
        self, collection_id: UUID, with_relations: bool = False
    ) -> Optional[Collection]:
        """根据 ID 获取分类"""
        with Session(self.engine) as session:
            statement = select(Collection).where(Collection.id == collection_id)
            result = session.exec(statement)
            return result.first()

    def get_all_collections(self, with_relations: bool = False) -> List[Collection]:
        """获取所有分类"""
        with Session(self.engine) as session:
            statement = select(Collection)
            statement = statement.order_by(Collection.name)
            result = session.exec(statement)
            return result.all()

    def update_collection(self, collection: Collection) -> Collection:
        """更新分类记录"""
        collection.updated_at = datetime.now()
        with Session(self.engine) as session:
            session.add(collection)
            session.commit()
            session.refresh(collection)
            return collection

    def delete_collection(self, collection_id: UUID) -> bool:
        """删除分类记录"""
        with Session(self.engine) as session:
            collection = session.get(Collection, collection_id)
            if collection:
                session.delete(collection)
                session.commit()
                return True
            return False

    # Tag 操作
    def create_tag(self, tag: Tag) -> Tag:
        """创建标签记录"""
        with Session(self.engine) as session:
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag

    def get_tag_by_name(self, name: str, with_relations: bool = False) -> Optional[Tag]:
        """根据名称获取标签"""
        with Session(self.engine) as session:
            statement = select(Tag).where(Tag.name == name)
            result = session.exec(statement)
            return result.first()

    def get_all_tags(self, with_relations: bool = False) -> List[Tag]:
        """获取所有标签"""
        with Session(self.engine) as session:
            statement = select(Tag)
            statement = statement.order_by(Tag.name)
            result = session.exec(statement)
            return result.all()

    def update_tag(self, tag: Tag) -> Tag:
        """更新标签记录"""
        with Session(self.engine) as session:
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag

    def delete_tag(self, tag_name: str) -> bool:
        """删除标签记录"""
        with Session(self.engine) as session:
            tag = session.get(Tag, tag_name)
            if tag:
                session.delete(tag)
                session.commit()
                return True
            return False

    # 关联操作
    def add_paper_to_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
        """将文献添加到分类"""
        with Session(self.engine) as session:
            # 检查关联是否已存在
            statement = select(PaperCollectionLink).where(
                PaperCollectionLink.paper_id == paper_id,
                PaperCollectionLink.collection_id == collection_id,
            )
            result = session.exec(statement)
            if result.first():
                return False  # 关联已存在

            link = PaperCollectionLink(paper_id=paper_id, collection_id=collection_id)
            session.add(link)
            session.commit()
            return True

    def remove_paper_from_collection(self, paper_id: UUID, collection_id: UUID) -> bool:
        """从分类中移除文献"""
        with Session(self.engine) as session:
            statement = select(PaperCollectionLink).where(
                PaperCollectionLink.paper_id == paper_id,
                PaperCollectionLink.collection_id == collection_id,
            )
            result = session.exec(statement)
            link = result.first()

            if link:
                session.delete(link)
                session.commit()
                return True
            return False

    def add_tag_to_paper(self, paper_id: UUID, tag_name: str) -> bool:
        """为文献添加标签"""
        with Session(self.engine) as session:
            # 检查关联是否已存在
            statement = select(PaperTagLink).where(
                PaperTagLink.paper_id == paper_id, PaperTagLink.tag_name == tag_name
            )
            result = session.exec(statement)
            if result.first():
                return False  # 关联已存在

            link = PaperTagLink(paper_id=paper_id, tag_name=tag_name)
            session.add(link)
            session.commit()
            return True

    def remove_tag_from_paper(self, paper_id: UUID, tag_name: str) -> bool:
        """从文献移除标签"""
        with Session(self.engine) as session:
            statement = select(PaperTagLink).where(
                PaperTagLink.paper_id == paper_id, PaperTagLink.tag_name == tag_name
            )
            result = session.exec(statement)
            link = result.first()

            if link:
                session.delete(link)
                session.commit()
                return True
            return False
