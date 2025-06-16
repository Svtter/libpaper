# 数据模型

LibPaper 的数据模型基于 Pydantic，提供类型安全和数据验证功能。

## Paper 模型

::: libpaper.models.paper.Paper
options:
show_root_heading: true
show_source: true
members_order: source

## Collection 模型

::: libpaper.models.collection.Collection
options:
show_root_heading: true
show_source: true
members_order: source

## Tag 模型

::: libpaper.models.tag.Tag
options:
show_root_heading: true
show_source: true
members_order: source

## 使用示例

### 创建 Paper 实例

```python
from libpaper.models import Paper
from datetime import datetime
from uuid import uuid4

paper = Paper(
    title="深度学习在自然语言处理中的应用",
    file_path="/storage/papers/2024/01/abc123.pdf",
    original_filename="deep_learning_nlp.pdf",
    file_size=2048576,
    file_hash="a1b2c3d4e5f6...",
    authors=["张三", "李四"],
    abstract="本文研究了深度学习技术在自然语言处理领域的应用...",
    publication_date=datetime(2024, 1, 15),
    journal="计算机学报",
    doi="10.1000/journal.2024.001",
    tag_names=["深度学习", "自然语言处理"]
)

print(f"文献标题: {paper.title}")
print(f"作者: {', '.join(paper.authors)}")
print(f"是否有 DOI: {paper.doi is not None}")
```

### 创建 Collection 实例

```python
from libpaper.models import Collection

# 创建根分类
ai_research = Collection(
    name="人工智能研究",
    description="人工智能相关的研究论文"
)

# 创建子分类
nlp_research = Collection(
    name="自然语言处理",
    description="NLP 相关论文",
    parent_id=ai_research.id
)

print(f"根分类: {ai_research.name}")
print(f"子分类: {nlp_research.name}")
print(f"是否为根分类: {ai_research.is_root()}")
print(f"是否有父分类: {nlp_research.has_parent()}")
```

### 创建 Tag 实例

```python
from libpaper.models import Tag

tag = Tag(
    name="机器学习",
    description="机器学习相关研究",
    color="#FF5722"
)

print(f"标签名称: {tag.name}")
print(f"标签颜色: {tag.color}")
print(f"字符串表示: {str(tag)}")
```

## 数据验证

所有模型都包含内置的数据验证：

```python
from libpaper.models import Paper, Tag
from pydantic import ValidationError

# Paper 验证示例
try:
    paper = Paper(
        title="",  # 空标题会被拒绝
        file_path="/path/to/file.pdf",
        original_filename="file.pdf",
        file_size=-100,  # 负数文件大小会被拒绝
        file_hash="invalid_hash"  # 无效哈希会被拒绝
    )
except ValidationError as e:
    print(f"验证错误: {e}")

# Tag 验证示例
try:
    tag = Tag(
        name="invalid name!",  # 包含非法字符
        color="not_a_color"    # 无效颜色格式
    )
except ValidationError as e:
    print(f"验证错误: {e}")
```

## JSON 序列化

所有模型都支持 JSON 序列化：

```python
from libpaper.models import Paper
import json

paper = Paper(
    title="示例论文",
    file_path="/path/to/paper.pdf",
    original_filename="paper.pdf",
    file_size=1024,
    file_hash="a" * 64
)

# 转换为 JSON
json_str = paper.to_json()
print(json_str)

# 从 JSON 创建实例
paper_from_json = Paper.from_json(json_str)
print(f"恢复的标题: {paper_from_json.title}")

# 转换为字典
paper_dict = paper.to_dict()
print(f"字典格式: {paper_dict}")

# 从字典创建实例
paper_from_dict = Paper.from_dict(paper_dict)
print(f"恢复的标题: {paper_from_dict.title}")
```
