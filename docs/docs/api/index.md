# API 参考

欢迎来到 LibPaper 的 API 参考文档！LibPaper 是一个专为文献管理设计的 headless 库，提供完整的 Python API 供开发者集成使用。

## 快速开始

### 安装

```bash
pip install libpaper
```

### 基本使用

```python
from libpaper import LibPaper
from libpaper.models import Paper, Collection, Tag

# 初始化库
library = LibPaper()

# 添加 PDF 文献
paper = library.add_paper("/path/to/paper.pdf", title="我的研究论文")

# 创建分类
collection = library.create_collection("机器学习")

# 添加标签
tag = library.create_tag("深度学习", color="#FF5722")

# 将文献添加到分类和标签
library.add_paper_to_collection(paper.id, collection.id)
library.add_tag_to_paper(paper.id, tag.name)

# 搜索文献
results = library.search_papers("neural networks")
```

## 核心概念

### Paper (文献)

文献是 LibPaper 的核心实体，代表一个研究论文。每个文献包含：

- 基本信息（标题、作者、摘要等）
- 文件信息（PDF 路径、大小、哈希值等）
- 关联信息（分类、标签）

### Collection (分类)

分类用于组织文献，支持层次化结构：

- 可以创建父子关系的分类
- 一个文献可以属于多个分类
- 自动统计分类中的文献数量

### Tag (标签)

标签提供灵活的文献标记方式：

- 支持自定义颜色
- 一个文献可以有多个标签
- 自动统计标签的使用次数

## API 组织

LibPaper 的 API 按功能模块组织：

- **[数据模型](models.md)**: 核心数据模型定义
- **[存储层](storage.md)**: 数据库和文件存储管理
- **[服务层](services.md)**: 业务逻辑和操作接口
- **[CLI](cli.md)**: 命令行工具

## 异步支持

LibPaper 完全支持异步操作，适合集成到现代 Python 应用中：

```python
import asyncio
from libpaper import AsyncLibPaper

async def main():
    library = AsyncLibPaper()

    # 异步添加文献
    paper = await library.add_paper("/path/to/paper.pdf")

    # 异步搜索
    results = await library.search_papers("machine learning")

    for paper in results:
        print(f"找到文献: {paper.title}")

asyncio.run(main())
```

## 错误处理

LibPaper 定义了清晰的异常体系：

```python
from libpaper.exceptions import (
    LibPaperError,
    FileNotFoundError,
    DuplicateFileError,
    InvalidPDFError,
    DatabaseError
)

try:
    paper = library.add_paper("/invalid/path.pdf")
except FileNotFoundError:
    print("文件不存在")
except InvalidPDFError:
    print("不是有效的 PDF 文件")
except DuplicateFileError:
    print("文件已经存在")
```

## 配置

LibPaper 支持灵活的配置选项：

```python
from libpaper.storage import Config

# 加载配置
config = Config.load("/path/to/config.yaml")

# 修改配置
config.storage.base_path = "/custom/storage/path"
config.save()

# 使用自定义配置初始化
library = LibPaper(config=config)
```
