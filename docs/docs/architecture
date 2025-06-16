# LibPaper 第一阶段架构设计

## 阶段目标

第一阶段专注于实现基础的文献管理功能，为后续扩展打下坚实基础：

- **PDF 文件存储**: 安全存储 PDF 文件并记录存储位置
- **文件分类**: 支持层次化的文件夹/分类系统
- **标签管理**: 灵活的标签系统，支持多标签关联
- **CLI 工具**: 提供命令行界面进行所有操作

## 核心组件架构

```
src/libpaper/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── paper.py        # Paper 数据模型
│   ├── collection.py   # Collection/分类模型
│   └── tag.py          # Tag 标签模型
├── storage/
│   ├── __init__.py
│   ├── database.py     # 数据库操作
│   ├── file_manager.py # 文件存储管理
│   └── config.py       # 配置管理
├── services/
│   ├── __init__.py
│   ├── paper_service.py     # 文献管理服务
│   ├── collection_service.py # 分类管理服务
│   └── tag_service.py       # 标签管理服务
├── extractors/
│   ├── __init__.py
│   └── pdf_extractor.py     # PDF 元数据提取
└── cli/
    ├── __init__.py
    ├── main.py         # CLI 主入口
    ├── commands/
    │   ├── __init__.py
    │   ├── paper.py    # 文献相关命令
    │   ├── collection.py # 分类相关命令
    │   └── tag.py      # 标签相关命令
    └── utils.py        # CLI 工具函数
```

## 数据模型设计

### Paper 文献模型
```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class Paper(BaseModel):
    id: UUID
    title: str
    file_path: str              # PDF 文件存储路径
    original_filename: str      # 原始文件名
    file_size: int             # 文件大小（字节）
    file_hash: str             # 文件 SHA256 哈希值

    # 可选元数据
    authors: Optional[List[str]] = []
    abstract: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    doi: Optional[str] = None

    # 分类和标签
    collection_ids: List[UUID] = []
    tag_names: List[str] = []

    # 系统字段
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Collection 分类模型
```python
class Collection(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None  # 支持层次化分类
    paper_count: int = 0

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Tag 标签模型
```python
class Tag(BaseModel):
    name: str                    # 标签名（主键）
    description: Optional[str] = None
    color: Optional[str] = None  # 标签颜色（十六进制）
    paper_count: int = 0

    created_at: datetime

    class Config:
        from_attributes = True
```

## 存储设计

### 数据库表结构 (SQLite)

```sql
-- 文献表
CREATE TABLE papers (
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
);

-- 分类表
CREATE TABLE collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    parent_id TEXT REFERENCES collections(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 标签表
CREATE TABLE tags (
    name TEXT PRIMARY KEY,
    description TEXT,
    color TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文献-分类关联表
CREATE TABLE paper_collections (
    paper_id TEXT REFERENCES papers(id) ON DELETE CASCADE,
    collection_id TEXT REFERENCES collections(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (paper_id, collection_id)
);

-- 文献-标签关联表
CREATE TABLE paper_tags (
    paper_id TEXT REFERENCES papers(id) ON DELETE CASCADE,
    tag_name TEXT REFERENCES tags(name) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (paper_id, tag_name)
);
```

### 文件存储结构

```
~/.libpaper/
├── config.yaml           # 配置文件
├── library.db            # SQLite 数据库
└── storage/
    ├── papers/           # PDF 文件存储
    │   ├── 2024/
    │   │   ├── 01/
    │   │   │   ├── abc123def.pdf
    │   │   │   └── def456ghi.pdf
    │   │   └── 02/
    │   └── 2023/
    └── metadata/         # 提取的元数据缓存
        ├── abc123def.json
        └── def456ghi.json
```

## CLI 命令设计

### 文献管理命令

```bash
# 添加 PDF 文件
libpaper add /path/to/paper.pdf
libpaper add /path/to/paper.pdf --title "Custom Title" --tags "ml,ai"

# 列出所有文献
libpaper list
libpaper list --collection "AI Research" --tags "ml"

# 查看文献详情
libpaper show <paper-id>

# 搜索文献
libpaper search "machine learning"
libpaper search --title "neural" --author "hinton"

# 删除文献
libpaper remove <paper-id>
```

### 分类管理命令

```bash
# 创建分类
libpaper collection create "AI Research"
libpaper collection create "Deep Learning" --parent "AI Research"

# 列出分类
libpaper collection list
libpaper collection list --tree  # 树状显示

# 添加文献到分类
libpaper collection add <collection-id> <paper-id>

# 从分类中移除文献
libpaper collection remove <collection-id> <paper-id>

# 删除分类
libpaper collection delete <collection-id>
```

### 标签管理命令

```bash
# 创建标签
libpaper tag create "machine-learning" --color "#FF5722"

# 列出标签
libpaper tag list

# 给文献添加标签
libpaper tag add <paper-id> "ml" "ai" "deep-learning"

# 从文献移除标签
libpaper tag remove <paper-id> "old-tag"

# 删除标签
libpaper tag delete "unused-tag"
```

### 系统命令

```bash
# 初始化库
libpaper init

# 查看配置
libpaper config show
libpaper config set storage_path "/custom/path"

# 数据库维护
libpaper db status
libpaper db backup /path/to/backup.db
libpaper db restore /path/to/backup.db
```

## 文件存储策略

### 存储原则
1. **唯一性**: 使用文件 SHA256 哈希值确保不重复存储
2. **组织性**: 按年月分层存储，便于管理
3. **安全性**: 原始文件名和存储路径分离，防止路径注入
4. **可恢复性**: 保留原始文件名和元数据

### 存储流程
```python
def store_pdf(file_path: str) -> StorageInfo:
    # 1. 计算文件哈希
    file_hash = calculate_sha256(file_path)

    # 2. 检查是否已存储
    if exists_in_storage(file_hash):
        return get_storage_info(file_hash)

    # 3. 生成存储路径
    storage_path = generate_storage_path(file_hash)

    # 4. 复制文件到存储位置
    copy_file(file_path, storage_path)

    # 5. 返回存储信息
    return StorageInfo(
        hash=file_hash,
        path=storage_path,
        size=get_file_size(storage_path)
    )
```

## 配置管理

### 配置文件结构 (config.yaml)
```yaml
# 存储配置
storage:
  base_path: "~/.libpaper"
  database_file: "library.db"

# 数据库配置
database:
  type: "sqlite"
  path: "~/.libpaper/library.db"

# CLI 配置
cli:
  default_page_size: 20
  date_format: "%Y-%m-%d"

# PDF 处理配置
pdf:
  extract_metadata: true
  extract_text: false  # 第一阶段暂不实现
```

## 扩展点设计

为后续阶段预留扩展接口：

### 元数据提取器接口
```python
from abc import ABC, abstractmethod

class MetadataExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> dict:
        """从 PDF 文件提取元数据"""
        pass

class PDFExtractor(MetadataExtractor):
    def extract(self, file_path: str) -> dict:
        # 使用 pypdf 提取基础元数据
        pass
```

### 搜索引擎接口
```python
class SearchEngine(ABC):
    @abstractmethod
    def index_paper(self, paper: Paper) -> None:
        """索引文献"""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Paper]:
        """搜索文献"""
        pass
```

## 错误处理策略

### 异常类型定义
```python
class LibPaperError(Exception):
    """基础异常类"""
    pass

class FileNotFoundError(LibPaperError):
    """文件不存在"""
    pass

class DuplicateFileError(LibPaperError):
    """文件已存在"""
    pass

class InvalidPDFError(LibPaperError):
    """无效的 PDF 文件"""
    pass

class DatabaseError(LibPaperError):
    """数据库操作错误"""
    pass
```

### CLI 错误显示
使用 Rich 库提供友好的错误信息显示，包括：
- 彩色错误消息
- 详细的错误描述
- 建议的解决方案

这个第一阶段的架构设计专注于核心功能的实现，同时为后续扩展留下了清晰的接口和扩展点。