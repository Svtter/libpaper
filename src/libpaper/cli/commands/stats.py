import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...services import PaperService, CollectionService, TagService
from ..utils import format_size


console = Console()


@click.group()
def stats():
  """统计信息"""
  pass


@stats.command()
@click.pass_context
def overview(ctx: click.Context):
  """显示总体统计信息"""

  async def _overview():
    config = ctx.obj['config']
    paper_service = PaperService(config)
    collection_service = CollectionService(config)
    tag_service = TagService(config)

    try:
      # 初始化服务
      await paper_service.initialize()
      await collection_service.initialize()
      await tag_service.initialize()

      # 获取统计信息
      storage_stats = await paper_service.get_storage_stats()

      papers = await paper_service.list_papers(limit=1000)  # 获取所有文献
      collections = await collection_service.list_collections()
      tags = await tag_service.list_tags()

      # 创建统计表格
      console.print("[bold blue]LibPaper 统计概览[/bold blue]")
      console.print()

      # 文献统计
      papers_table = Table(title="文献统计", show_header=True, header_style="bold magenta")
      papers_table.add_column("项目", style="cyan")
      papers_table.add_column("数量/大小", justify="right")

      papers_table.add_row("总文献数", str(storage_stats['total_papers']))
      papers_table.add_row("总文件大小", format_size(storage_stats['total_size']))
      papers_table.add_row("平均文件大小", format_size(storage_stats['average_size']))
      papers_table.add_row("有摘要的文献", str(storage_stats['papers_with_abstract']))
      papers_table.add_row("有DOI的文献", str(storage_stats['papers_with_doi']))

      console.print(papers_table)
      console.print()

      # 分类和标签统计
      org_table = Table(title="组织结构", show_header=True, header_style="bold magenta")
      org_table.add_column("项目", style="cyan")
      org_table.add_column("数量", justify="right")

      # 计算根分类数量
      root_collections = [c for c in collections if c.is_root()]

      org_table.add_row("总分类数", str(len(collections)))
      org_table.add_row("根分类数", str(len(root_collections)))
      org_table.add_row("总标签数", str(len(tags)))

      # 计算使用中的标签
      used_tags = [tag for tag in tags if tag.paper_count > 0]
      org_table.add_row("使用中的标签", str(len(used_tags)))

      console.print(org_table)
      console.print()

      # 存储统计
      storage_table = Table(title="存储信息", show_header=True, header_style="bold magenta")
      storage_table.add_column("项目", style="cyan")
      storage_table.add_column("值", justify="right")

      storage_table.add_row("数据库路径", str(config.get_database_path()))
      storage_table.add_row("文件存储路径", str(config.get_storage_path()))
      storage_table.add_row("存储文件数", str(storage_stats['total_files']))

      console.print(storage_table)

    except Exception as e:
      console.print(f"[red]获取统计信息失败: {e}[/red]")
    finally:
      await paper_service.close()
      await collection_service.close()
      await tag_service.close()

  asyncio.run(_overview())


@stats.command()
@click.pass_context
def storage(ctx: click.Context):
  """显示存储统计信息"""

  async def _storage():
    config = ctx.obj['config']
    service = PaperService(config)

    try:
      await service.initialize()

      storage_stats = await service.get_storage_stats()

      console.print("[bold blue]存储统计信息[/bold blue]")
      console.print()

      # 创建详细存储统计
      table = Table(show_header=True, header_style="bold magenta")
      table.add_column("项目", style="cyan", min_width=20)
      table.add_column("值", justify="right", min_width=15)

      # 基础统计
      table.add_row("总文件数", str(storage_stats['total_files']))
      table.add_row("总大小", format_size(storage_stats['total_size']))
      table.add_row("平均大小", format_size(storage_stats['average_size']))

      if storage_stats['total_files'] > 0:
        table.add_row("最大文件", format_size(storage_stats['max_size']))
        table.add_row("最小文件", format_size(storage_stats['min_size']))

      # 文献相关统计
      table.add_row("", "")  # 分隔行
      table.add_row("文献总数", str(storage_stats['total_papers']))
      table.add_row("有摘要的文献", str(storage_stats['papers_with_abstract']))
      table.add_row("有DOI的文献", str(storage_stats['papers_with_doi']))

      # 计算百分比
      if storage_stats['total_papers'] > 0:
        abstract_percent = (storage_stats['papers_with_abstract'] / storage_stats['total_papers']) * 100
        doi_percent = (storage_stats['papers_with_doi'] / storage_stats['total_papers']) * 100

        table.add_row("摘要覆盖率", f"{abstract_percent:.1f}%")
        table.add_row("DOI覆盖率", f"{doi_percent:.1f}%")

      console.print(table)

      # 显示路径信息
      console.print()
      console.print(Panel(
        f"数据库: {config.get_database_path()}\n存储目录: {config.get_storage_path()}",
        title="路径信息",
        border_style="blue"
      ))

    except Exception as e:
      console.print(f"[red]获取存储信息失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_storage())


@stats.command()
@click.option('--limit', '-l', default=10, help='显示数量限制')
@click.pass_context
def tags(ctx: click.Context, limit: int):
  """显示标签使用统计"""

  async def _tags():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      # 获取热门标签
      popular_tags = await service.get_popular_tags(limit=limit)
      unused_tags = await service.get_unused_tags()

      console.print("[bold blue]标签使用统计[/bold blue]")
      console.print()

      if popular_tags:
        # 热门标签表格
        table = Table(title=f"热门标签 (前 {len(popular_tags)} 个)", show_header=True, header_style="bold magenta")
        table.add_column("排名", width=6, justify="center")
        table.add_column("标签名称", min_width=15)
        table.add_column("使用次数", width=10, justify="right")
        table.add_column("描述", min_width=20)

        for i, tag in enumerate(popular_tags, 1):
          rank = str(i)
          name = tag.name
          count = str(tag.paper_count)
          description = tag.description[:30] + "..." if tag.description and len(tag.description) > 30 else (tag.description or "-")

          table.add_row(rank, name, count, description)

        console.print(table)
        console.print()

      # 未使用标签信息
      if unused_tags:
        console.print(f"[yellow]未使用的标签: {len(unused_tags)} 个[/yellow]")
        if len(unused_tags) <= 10:
          unused_names = [tag.name for tag in unused_tags]
          console.print(f"  {', '.join(unused_names)}")
        else:
          console.print("  使用 'libpaper tag list --unused' 查看详情")
      else:
        console.print("[green]所有标签都在使用中[/green]")

    except Exception as e:
      console.print(f"[red]获取标签统计失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_tags())


@stats.command()
@click.pass_context
def collections(ctx: click.Context):
  """显示分类统计信息"""

  async def _collections():
    config = ctx.obj['config']
    service = CollectionService(config)

    try:
      await service.initialize()

      collections = await service.list_collections()

      if not collections:
        console.print("[yellow]没有找到分类[/yellow]")
        return

      console.print("[bold blue]分类统计信息[/bold blue]")
      console.print()

      # 基础统计
      root_collections = [c for c in collections if c.is_root()]
      child_collections = [c for c in collections if c.has_parent()]

      # 统计表格
      table = Table(show_header=True, header_style="bold magenta")
      table.add_column("项目", style="cyan", min_width=15)
      table.add_column("数量", justify="right", min_width=10)

      table.add_row("总分类数", str(len(collections)))
      table.add_row("根分类数", str(len(root_collections)))
      table.add_row("子分类数", str(len(child_collections)))

      # 计算平均深度
      if collections:
        total_papers = sum(c.paper_count for c in collections)
        table.add_row("总文献数", str(total_papers))

        if total_papers > 0:
          avg_papers = total_papers / len(collections)
          table.add_row("平均每分类文献数", f"{avg_papers:.1f}")

      console.print(table)

      # 显示文献数最多的分类
      if collections:
        console.print()
        sorted_collections = sorted(collections, key=lambda c: c.paper_count, reverse=True)
        top_collections = sorted_collections[:5]

        if any(c.paper_count > 0 for c in top_collections):
          top_table = Table(title="文献数最多的分类 (前5个)", show_header=True, header_style="bold magenta")
          top_table.add_column("分类名称", min_width=20)
          top_table.add_column("文献数", width=10, justify="right")
          top_table.add_column("类型", width=10)

          for collection in top_collections:
            if collection.paper_count > 0:
              name = collection.name
              count = str(collection.paper_count)
              type_str = "根分类" if collection.is_root() else "子分类"

              top_table.add_row(name, count, type_str)

          console.print(top_table)

    except Exception as e:
      console.print(f"[red]获取分类统计失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_collections())