import aiosqlite
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from ..models import Paper, Collection, Tag


class Database:
    """SQLite 数据库管理类"""

    def __init__(self, db_path: Union[str, Path]):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """建立数据库连接"""
        if self._connection is None:
            # 确保数据库目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self._connection = await aiosqlite.connect(str(self.db_path))
            # 启用外键约束
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.commit()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def initialize(self) -> None:
        """初始化数据库表结构"""
        await self.connect()

        # 创建文献表
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                original_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                authors TEXT,  -- JSON 数组
                abstract TEXT,
                publication_date DATE,
                journal TEXT,
                doi TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建分类表
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                parent_id TEXT REFERENCES collections(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建标签表
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                name TEXT PRIMARY KEY,
                description TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建文献-分类关联表
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS paper_collections (
                paper_id TEXT REFERENCES papers(id) ON DELETE CASCADE,
                collection_id TEXT REFERENCES collections(id) ON DELETE CASCADE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (paper_id, collection_id)
            )
        """)

        # 创建文献-标签关联表
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS paper_tags (
                paper_id TEXT REFERENCES papers(id) ON DELETE CASCADE,
                tag_name TEXT REFERENCES tags(name) ON DELETE CASCADE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (paper_id, tag_name)
            )
        """)

        # 创建索引以提高查询性能
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_papers_file_hash ON papers(file_hash)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_collections_parent_id ON collections(parent_id)
        """)

        await self._connection.commit()

    # Paper 操作
    async def insert_paper(self, paper: Paper) -> None:
        """插入文献记录"""
        await self._connection.execute("""
            INSERT INTO papers (
                id, title, file_path, original_filename, file_size, file_hash,
                authors, abstract, publication_date, journal, doi,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(paper.id), paper.title, paper.file_path, paper.original_filename,
            paper.file_size, paper.file_hash,
            json.dumps(paper.authors) if paper.authors else None,
            paper.abstract, paper.publication_date, paper.journal, paper.doi,
            paper.created_at.isoformat(), paper.updated_at.isoformat()
        ))
        await self._connection.commit()

    async def get_paper_by_id(self, paper_id: UUID) -> Optional[Paper]:
        """根据 ID 获取文献"""
        cursor = await self._connection.execute("""
            SELECT * FROM papers WHERE id = ?
        """, (str(paper_id),))
        row = await cursor.fetchone()

        if row:
            return self._row_to_paper(row)
        return None

    async def get_paper_by_hash(self, file_hash: str) -> Optional[Paper]:
        """根据文件哈希获取文献"""
        cursor = await self._connection.execute("""
            SELECT * FROM papers WHERE file_hash = ?
        """, (file_hash,))
        row = await cursor.fetchone()

        if row:
            return self._row_to_paper(row)
        return None

    async def update_paper(self, paper: Paper) -> None:
        """更新文献记录"""
        paper.updated_at = datetime.now()
        await self._connection.execute("""
            UPDATE papers SET
                title = ?, file_path = ?, original_filename = ?, file_size = ?,
                file_hash = ?, authors = ?, abstract = ?, publication_date = ?,
                journal = ?, doi = ?, updated_at = ?
            WHERE id = ?
        """, (
            paper.title, paper.file_path, paper.original_filename, paper.file_size,
            paper.file_hash,
            json.dumps(paper.authors) if paper.authors else None,
            paper.abstract, paper.publication_date, paper.journal, paper.doi,
            paper.updated_at.isoformat(), str(paper.id)
        ))
        await self._connection.commit()

    async def delete_paper(self, paper_id: UUID) -> bool:
        """删除文献记录"""
        cursor = await self._connection.execute("""
            DELETE FROM papers WHERE id = ?
        """, (str(paper_id),))
        await self._connection.commit()
        return cursor.rowcount > 0

    async def search_papers(
        self,
        query: Optional[str] = None,
        collection_id: Optional[UUID] = None,
        tag_names: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Paper]:
        """搜索文献"""
        sql = "SELECT DISTINCT p.* FROM papers p"
        params = []
        conditions = []

        # 添加分类过滤
        if collection_id:
            sql += " JOIN paper_collections pc ON p.id = pc.paper_id"
            conditions.append("pc.collection_id = ?")
            params.append(str(collection_id))

        # 添加标签过滤
        if tag_names:
            sql += " JOIN paper_tags pt ON p.id = pt.paper_id"
            tag_placeholders = ",".join("?" * len(tag_names))
            conditions.append(f"pt.tag_name IN ({tag_placeholders})")
            params.extend(tag_names)

        # 添加文本搜索
        if query:
            conditions.append("(p.title LIKE ? OR p.abstract LIKE ? OR p.authors LIKE ?)")
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await self._connection.execute(sql, params)
        rows = await cursor.fetchall()

        return [self._row_to_paper(row) for row in rows]

    # Collection 操作
    async def insert_collection(self, collection: Collection) -> None:
        """插入分类记录"""
        await self._connection.execute("""
            INSERT INTO collections (id, name, description, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(collection.id), collection.name, collection.description,
            str(collection.parent_id) if collection.parent_id else None,
            collection.created_at.isoformat(), collection.updated_at.isoformat()
        ))
        await self._connection.commit()

    async def get_collection_by_id(self, collection_id: UUID) -> Optional[Collection]:
        """根据 ID 获取分类"""
        cursor = await self._connection.execute("""
            SELECT * FROM collections WHERE id = ?
        """, (str(collection_id),))
        row = await cursor.fetchone()

        if row:
            return self._row_to_collection(row)
        return None

    async def get_all_collections(self) -> List[Collection]:
        """获取所有分类"""
        cursor = await self._connection.execute("""
            SELECT c.*, COUNT(pc.paper_id) as paper_count
            FROM collections c
            LEFT JOIN paper_collections pc ON c.id = pc.collection_id
            GROUP BY c.id
            ORDER BY c.name
        """)
        rows = await cursor.fetchall()

        collections = []
        for row in rows:
            collection = self._row_to_collection(row)
            collection.paper_count = row[7]  # paper_count
            collections.append(collection)

        return collections

    # Tag 操作
    async def insert_tag(self, tag: Tag) -> None:
        """插入标签记录"""
        await self._connection.execute("""
            INSERT INTO tags (name, description, color, created_at)
            VALUES (?, ?, ?, ?)
        """, (tag.name, tag.description, tag.color, tag.created_at.isoformat()))
        await self._connection.commit()

    async def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签"""
        cursor = await self._connection.execute("""
            SELECT * FROM tags WHERE name = ?
        """, (name,))
        row = await cursor.fetchone()

        if row:
            return self._row_to_tag(row)
        return None

    async def get_all_tags(self) -> List[Tag]:
        """获取所有标签"""
        cursor = await self._connection.execute("""
            SELECT t.*, COUNT(pt.paper_id) as paper_count
            FROM tags t
            LEFT JOIN paper_tags pt ON t.name = pt.tag_name
            GROUP BY t.name
            ORDER BY t.name
        """)
        rows = await cursor.fetchall()

        tags = []
        for row in rows:
            tag = self._row_to_tag(row)
            tag.paper_count = row[4]  # paper_count
            tags.append(tag)

        return tags

    # 关联操作
    async def add_paper_to_collection(self, paper_id: UUID, collection_id: UUID) -> None:
        """将文献添加到分类"""
        await self._connection.execute("""
            INSERT OR IGNORE INTO paper_collections (paper_id, collection_id)
            VALUES (?, ?)
        """, (str(paper_id), str(collection_id)))
        await self._connection.commit()

    async def remove_paper_from_collection(self, paper_id: UUID, collection_id: UUID) -> None:
        """从分类中移除文献"""
        await self._connection.execute("""
            DELETE FROM paper_collections
            WHERE paper_id = ? AND collection_id = ?
        """, (str(paper_id), str(collection_id)))
        await self._connection.commit()

    async def add_tag_to_paper(self, paper_id: UUID, tag_name: str) -> None:
        """为文献添加标签"""
        await self._connection.execute("""
            INSERT OR IGNORE INTO paper_tags (paper_id, tag_name)
            VALUES (?, ?)
        """, (str(paper_id), tag_name))
        await self._connection.commit()

    async def remove_tag_from_paper(self, paper_id: UUID, tag_name: str) -> None:
        """从文献移除标签"""
        await self._connection.execute("""
            DELETE FROM paper_tags
            WHERE paper_id = ? AND tag_name = ?
        """, (str(paper_id), tag_name))
        await self._connection.commit()

    # 私有辅助方法
    def _row_to_paper(self, row) -> Paper:
        """将数据库行转换为 Paper 对象"""
        return Paper(
            id=UUID(row[0]),
            title=row[1],
            file_path=row[2],
            original_filename=row[3],
            file_size=row[4],
            file_hash=row[5],
            authors=json.loads(row[6]) if row[6] else [],
            abstract=row[7],
            publication_date=datetime.fromisoformat(row[8]) if row[8] else None,
            journal=row[9],
            doi=row[10],
            created_at=datetime.fromisoformat(row[11]),
            updated_at=datetime.fromisoformat(row[12])
        )

    def _row_to_collection(self, row) -> Collection:
        """将数据库行转换为 Collection 对象"""
        return Collection(
            id=UUID(row[0]),
            name=row[1],
            description=row[2],
            parent_id=UUID(row[3]) if row[3] else None,
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5])
        )

    def _row_to_tag(self, row) -> Tag:
        """将数据库行转换为 Tag 对象"""
        return Tag(
            name=row[0],
            description=row[1],
            color=row[2],
            created_at=datetime.fromisoformat(row[3])
        )