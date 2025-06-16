import asyncio
import click
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ...services import PaperService
from ..utils import format_date, format_size, truncate_text, parse_uuid


console = Console()


@click.group()
def paper():
  """文献管理"""
  pass


@paper.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--title', '-t', help='自定义标题')
@click.option('--authors', '-a', help='作者列表 (用逗号分隔)')
@click.option('--tags', help='标签列表 (用逗号分隔)')
@click.option('--collection', '-c', help='分类ID')
@click.pass_context
def add(
  ctx: click.Context,
  file_path: Path,
  title: Optional[str],
  authors: Optional[str],
  tags: Optional[str],
  collection: Optional[str]
):
  """添加新文献"""

  async def _add():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析参数
      author_list = [a.strip() for a in authors.split(',')] if authors else None
      tag_list = [t.strip() for t in tags.split(',')] if tags else None
      collection_ids = [parse_uuid(collection)] if collection else None

      # 添加文献
      console.print(f"[blue]正在添加文献: {file_path.name}[/blue]")

      paper = await service.add_paper(
        file_path=str(file_path),
        title=title,
        authors=author_list,
        tags=tag_list,
        collection_ids=collection_ids
      )

      console.print(f"[green]✓ 文献添加成功[/green]")
      console.print(f"ID: {paper.id}")
      console.print(f"标题: {paper.title}")
      if paper.authors:
        console.print(f"作者: {', '.join(paper.authors)}")
      console.print(f"文件大小: {format_size(paper.file_size)}")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except FileExistsError:
      console.print(f"[yellow]警告: 文件已存在[/yellow]")
    except Exception as e:
      console.print(f"[red]添加失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_add())


@paper.command()
@click.option('--query', '-q', help='搜索关键词')
@click.option('--collection', '-c', help='分类ID筛选')
@click.option('--tags', help='标签筛选 (用逗号分隔)')
@click.option('--limit', '-l', default=20, help='显示数量限制')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
@click.pass_context
def list(
  ctx: click.Context,
  query: Optional[str],
  collection: Optional[str],
  tags: Optional[str],
  limit: int,
  verbose: bool
):
  """列出/搜索文献"""

  async def _list():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析参数
      collection_id = parse_uuid(collection) if collection else None
      tag_list = [t.strip() for t in tags.split(',')] if tags else None

      # 搜索文献
      if query or collection_id or tag_list:
        papers = await service.search_papers(
          query=query,
          collection_id=collection_id,
          tag_names=tag_list,
          limit=limit
        )
        console.print(f"[blue]搜索结果 ({len(papers)} 条)[/blue]")
      else:
        papers = await service.list_papers(limit=limit)
        console.print(f"[blue]所有文献 ({len(papers)} 条)[/blue]")

      if not papers:
        console.print("[yellow]没有找到文献[/yellow]")
        return

      # 创建表格
      table = Table(show_header=True, header_style="bold magenta")
      table.add_column("ID", style="dim", width=8)
      table.add_column("标题", min_width=20)
      table.add_column("作者", width=15)
      table.add_column("大小", width=8, justify="right")
      table.add_column("添加时间", width=10)

      if verbose:
        table.add_column("标签", width=15)
        table.add_column("摘要", width=30)

      for paper in papers:
        # 基础信息
        short_id = str(paper.id)[:8]
        title = truncate_text(paper.title, 30)
        authors = ', '.join(paper.authors[:2]) if paper.authors else "-"
        if paper.authors and len(paper.authors) > 2:
          authors += f" 等{len(paper.authors)}人"
        size = format_size(paper.file_size)
        created = format_date(paper.created_at)

        row = [short_id, title, authors, size, created]

        if verbose:
          # 标签
          tag_names = [tag.name for tag in paper.tags] if paper.tags else []
          tags_text = ', '.join(tag_names[:3])
          if len(tag_names) > 3:
            tags_text += f" +{len(tag_names)-3}"

          # 摘要
          abstract = truncate_text(paper.abstract, 50) if paper.abstract else "-"

          row.extend([tags_text, abstract])

        table.add_row(*row)

      console.print(table)

    except Exception as e:
      console.print(f"[red]查询失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_list())


@paper.command()
@click.argument('paper_id', type=str)
@click.pass_context
def show(ctx: click.Context, paper_id: str):
  """显示文献详情"""

  async def _show():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析ID
      paper_uuid = parse_uuid(paper_id)

      # 获取文献
      paper = await service.get_paper(paper_uuid)
      if not paper:
        console.print(f"[red]文献不存在: {paper_id}[/red]")
        return

      # 显示详细信息
      console.print(f"[bold blue]文献详情[/bold blue]")
      console.print()

      console.print(f"[bold]ID:[/bold] {paper.id}")
      console.print(f"[bold]标题:[/bold] {paper.title}")

      if paper.authors:
        console.print(f"[bold]作者:[/bold] {', '.join(paper.authors)}")

      if paper.journal:
        console.print(f"[bold]期刊:[/bold] {paper.journal}")

      if paper.publication_date:
        console.print(f"[bold]发表日期:[/bold] {format_date(paper.publication_date)}")

      if paper.doi:
        console.print(f"[bold]DOI:[/bold] {paper.doi}")

      console.print(f"[bold]文件:[/bold] {paper.original_filename}")
      console.print(f"[bold]大小:[/bold] {format_size(paper.file_size)}")
      console.print(f"[bold]添加时间:[/bold] {format_date(paper.created_at)}")
      console.print(f"[bold]更新时间:[/bold] {format_date(paper.updated_at)}")

      # 标签
      if paper.tags:
        tag_names = [tag.name for tag in paper.tags]
        console.print(f"[bold]标签:[/bold] {', '.join(tag_names)}")

      # 分类
      if paper.collections:
        collection_names = [collection.name for collection in paper.collections]
        console.print(f"[bold]分类:[/bold] {', '.join(collection_names)}")

      # 摘要
      if paper.abstract:
        console.print(f"[bold]摘要:[/bold]")
        console.print(paper.abstract)

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]查询失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_show())


@paper.command()
@click.argument('paper_id', type=str)
@click.option('--title', '-t', help='新标题')
@click.option('--authors', '-a', help='新作者列表 (用逗号分隔)')
@click.option('--journal', '-j', help='期刊名称')
@click.option('--doi', help='DOI')
@click.option('--abstract', help='摘要')
@click.pass_context
def update(
  ctx: click.Context,
  paper_id: str,
  title: Optional[str],
  authors: Optional[str],
  journal: Optional[str],
  doi: Optional[str],
  abstract: Optional[str]
):
  """更新文献信息"""

  async def _update():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析ID
      paper_uuid = parse_uuid(paper_id)

      # 解析作者
      author_list = [a.strip() for a in authors.split(',')] if authors else None

      # 更新文献
      updated_paper = await service.update_paper(
        paper_id=paper_uuid,
        title=title,
        authors=author_list,
        journal=journal,
        doi=doi,
        abstract=abstract
      )

      if updated_paper:
        console.print(f"[green]✓ 文献更新成功[/green]")
        console.print(f"标题: {updated_paper.title}")
      else:
        console.print(f"[red]文献不存在: {paper_id}[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]更新失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_update())


@paper.command()
@click.argument('paper_id', type=str)
@click.confirmation_option(prompt='确定要删除这篇文献吗？')
@click.pass_context
def delete(ctx: click.Context, paper_id: str):
  """删除文献"""

  async def _delete():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析ID
      paper_uuid = parse_uuid(paper_id)

      # 删除文献
      success = await service.delete_paper(paper_uuid)

      if success:
        console.print(f"[green]✓ 文献删除成功[/green]")
      else:
        console.print(f"[red]文献不存在: {paper_id}[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]删除失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_delete())


@paper.command()
@click.argument('paper_id', type=str)
@click.argument('tag_name', type=str)
@click.pass_context
def add_tag(ctx: click.Context, paper_id: str, tag_name: str):
  """为文献添加标签"""

  async def _add_tag():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析ID
      paper_uuid = parse_uuid(paper_id)

      # 添加标签
      success = await service.add_tag_to_paper(paper_uuid, tag_name)

      if success:
        console.print(f"[green]✓ 标签 '{tag_name}' 添加成功[/green]")
      else:
        console.print(f"[red]添加标签失败[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]操作失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_add_tag())


@paper.command()
@click.argument('paper_id', type=str)
@click.argument('tag_name', type=str)
@click.pass_context
def remove_tag(ctx: click.Context, paper_id: str, tag_name: str):
  """从文献移除标签"""

  async def _remove_tag():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      # 解析ID
      paper_uuid = parse_uuid(paper_id)

      # 移除标签
      success = await service.remove_tag_from_paper(paper_uuid, tag_name)

      if success:
        console.print(f"[green]✓ 标签 '{tag_name}' 移除成功[/green]")
      else:
        console.print(f"[red]移除标签失败[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]操作失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_remove_tag())