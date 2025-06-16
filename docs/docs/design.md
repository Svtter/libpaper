# LibPaper 设计文档

## 项目概述

LibPaper 是一个专为文献管理设计的 headless 库，提供完整的文献数据管理、元数据提取、搜索和组织功能。作为 headless 库，它不包含用户界面，而是专注于提供强大的 API，可以被集成到各种应用程序中。

## 核心特性

### 1. 文献管理

- **文献导入**: 支持多种格式（PDF、DOI、BibTeX、RIS、EndNote）
- **元数据提取**: 自动从 PDF 和在线数据库提取文献信息
- **元数据标准化**: 统一不同来源的文献元数据格式
- **文献存储**: 安全的文件存储和版本管理

### 2. 搜索与过滤

- **全文搜索**: 基于文献内容的全文搜索
- **元数据搜索**: 按作者、标题、期刊、年份等字段搜索
- **标签系统**: 自定义标签和分类
- **高级过滤**: 多维度组合过滤

### 3. 数据组织

- **收藏夹/文件夹**: 层次化文献组织
- **智能分类**: 基于内容的自动分类建议
- **关联关系**: 文献间的引用和相关性分析
- **批量操作**: 批量标记、移动、删除等操作

### 4. 集成能力

- **第三方集成**: Zotero、Mendeley、EndNote 数据同步
- **API 接口**: RESTful API 和 Python SDK
- **插件系统**: 可扩展的插件架构
- **导出功能**: 多种格式的数据导出

## 技术架构

### 核心组件

```
libpaper/
├── core/           # 核心业务逻辑
│   ├── models/     # 数据模型
│   ├── services/   # 业务服务
│   └── interfaces/ # 接口定义
├── storage/        # 存储层
│   ├── database/   # 数据库操作
│   ├── files/      # 文件存储
│   └── cache/      # 缓存管理
├── extractors/     # 元数据提取器
│   ├── pdf/        # PDF 解析
│   ├── doi/        # DOI 查询
│   └── bibtex/     # BibTeX 解析
├── search/         # 搜索引擎
│   ├── indexing/   # 索引管理
│   ├── query/      # 查询处理
│   └── ranking/    # 相关性排序
└── integrations/   # 第三方集成
    ├── zotero/     # Zotero 集成
    ├── mendeley/   # Mendeley 集成
    └── crossref/   # CrossRef API
```

### 数据模型

#### Paper 文献实体

```python
class Paper:
    id: str
    title: str
    authors: List[Author]
    abstract: str
    publication_date: datetime
    journal: str
    doi: str
    url: str
    file_path: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
```

#### Collection 收藏夹

```python
class Collection:
    id: str
    name: str
    description: str
    parent_id: Optional[str]
    papers: List[str]  # paper_ids
    created_at: datetime
```

#### Tag 标签

```python
class Tag:
    name: str
    color: str
    description: str
    paper_count: int
```

## API 设计

### 文献管理 API

```python
# 添加文献
async def add_paper(file_path: str, metadata: Optional[dict] = None) -> Paper

# 批量导入
async def import_papers(files: List[str], format: str = "auto") -> List[Paper]

# 获取文献
async def get_paper(paper_id: str) -> Paper
async def get_papers(filters: dict = None, limit: int = 100) -> List[Paper]

# 更新文献
async def update_paper(paper_id: str, updates: dict) -> Paper

# 删除文献
async def delete_paper(paper_id: str) -> bool
```

### 搜索 API

```python
# 全文搜索
async def search_papers(
    query: str,
    filters: dict = None,
    sort_by: str = "relevance",
    limit: int = 100
) -> SearchResult

# 高级搜索
async def advanced_search(
    title: str = None,
    authors: List[str] = None,
    journal: str = None,
    year_range: Tuple[int, int] = None,
    tags: List[str] = None
) -> List[Paper]
```

### 收藏夹管理 API

```python
# 创建收藏夹
async def create_collection(name: str, parent_id: str = None) -> Collection

# 添加文献到收藏夹
async def add_to_collection(collection_id: str, paper_ids: List[str]) -> bool

# 获取收藏夹内容
async def get_collection_papers(collection_id: str) -> List[Paper]
```

## 存储设计

### 数据库设计 (Supabase/PostgreSQL)

#### papers 表

```sql
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    authors JSONB,
    abstract TEXT,
    publication_date DATE,
    journal TEXT,
    doi TEXT UNIQUE,
    url TEXT,
    file_path TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### collections 表

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES collections(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### paper_collections 关联表

```sql
CREATE TABLE paper_collections (
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (paper_id, collection_id)
);
```

### 文件存储设计

```
storage/
├── papers/
│   ├── 2024/
│   │   ├── 01/
│   │   │   └── {paper_id}.pdf
│   │   └── 02/
│   └── 2023/
├── thumbnails/
│   └── {paper_id}_thumb.png
└── extracted/
    └── {paper_id}/
        ├── text.txt
        ├── figures/
        └── metadata.json
```

## 扩展机制

### 插件架构

```python
class ExtractorPlugin(ABC):
    @abstractmethod
    async def extract_metadata(self, file_path: str) -> dict:
        pass

class SearchPlugin(ABC):
    @abstractmethod
    async def search(self, query: str, papers: List[Paper]) -> List[Paper]:
        pass
```

### 配置系统

```python
# libpaper.config.py
class Config:
    DATABASE_URL: str
    STORAGE_PATH: str
    SEARCH_ENGINE: str  # "elasticsearch" | "whoosh" | "simple"
    EXTRACTORS: List[str] = ["pdf", "doi", "crossref"]
    PLUGINS: List[str] = []
```

## 使用示例

```python
from libpaper import LibPaper

# 初始化库
lib = LibPaper(config_path="config.yaml")

# 添加文献
paper = await lib.add_paper("research_paper.pdf")

# 搜索文献
results = await lib.search_papers("machine learning neural networks")

# 创建收藏夹
collection = await lib.create_collection("AI Research")
await lib.add_to_collection(collection.id, [paper.id])

# 批量导入
papers = await lib.import_from_bibtex("references.bib")
```

## 开发路线图

### Phase 1: 核心功能 (v0.1)

- [ ] 基础数据模型
- [ ] PDF 元数据提取
- [ ] 简单搜索功能
- [ ] 基础 CRUD 操作

### Phase 2: 增强功能 (v0.2)

- [ ] 全文搜索
- [ ] 收藏夹系统
- [ ] 标签管理
- [ ] BibTeX 导入/导出

### Phase 3: 集成与优化 (v0.3)

- [ ] 第三方服务集成
- [ ] 性能优化
- [ ] 插件系统
- [ ] 批量操作

### Phase 4: 高级特性 (v1.0)

- [ ] 智能分类
- [ ] 引用分析
- [ ] 协作功能
- [ ] 高级搜索语法
