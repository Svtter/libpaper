import asyncio
import click
from typing import Optional
from rich.console import Console
from rich.table import Table

from ...services import TagService
from ..utils import truncate_text


console = Console()


@click.group()
def tag():
  """标签管理"""
  pass


@tag.command()
@click.argument('name', type=str)
@click.option('--description', '-d', help='标签描述')
@click.option('--color', '-c', help='标签颜色 (hex 格式，如 #ff0000)')
@click.pass_context
def create(
  ctx: click.Context,
  name: str,
  description: Optional[str],
  color: Optional[str]
):
  """创建新标签"""

  async def _create():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      # 创建标签
      tag = await service.create_tag(
        name=name,
        description=description,
        color=color
      )

      console.print(f"[green]✓ 标签创建成功[/green]")
      console.print(f"名称: {tag.name}")
      if tag.description:
        console.print(f"描述: {tag.description}")
      if tag.color:
        console.print(f"颜色: {tag.color}")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]创建失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_create())


@tag.command()
@click.option('--popular', '-p', is_flag=True, help='显示热门标签')
@click.option('--unused', '-u', is_flag=True, help='显示未使用的标签')
@click.option('--limit', '-l', default=20, help='显示数量限制')
@click.pass_context
def list(
  ctx: click.Context,
  popular: bool,
  unused: bool,
  limit: int
):
  """列出标签"""

  async def _list():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      if popular:
        tags = await service.get_popular_tags(limit=limit)
        title = f"热门标签 (前 {len(tags)} 个)"
      elif unused:
        tags = await service.get_unused_tags()
        title = f"未使用的标签 ({len(tags)} 个)"
      else:
        tags = await service.list_tags()
        title = f"所有标签 ({len(tags)} 个)"

      if not tags:
        console.print("[yellow]没有找到标签[/yellow]")
        return

      console.print(f"[blue]{title}[/blue]")

      # 创建表格
      table = Table(show_header=True, header_style="bold magenta")
      table.add_column("名称", min_width=15)
      table.add_column("描述", min_width=20)
      table.add_column("颜色", width=10)
      table.add_column("使用次数", width=8, justify="right")

      for tag in tags:
        name = tag.name
        description = truncate_text(tag.description, 30)

        # 颜色显示
        color_display = tag.color if tag.color else "-"
        if tag.color:
          # 如果有颜色，用该颜色显示颜色值
          try:
            color_display = f"[{tag.color}]{tag.color}[/{tag.color}]"
          except:
            color_display = tag.color

        paper_count = str(tag.paper_count)

        table.add_row(name, description, color_display, paper_count)

      console.print(table)

    except Exception as e:
      console.print(f"[red]查询失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_list())


@tag.command()
@click.argument('query', type=str)
@click.pass_context
def search(ctx: click.Context, query: str):
  """搜索标签"""

  async def _search():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      tags = await service.search_tags(query)

      if not tags:
        console.print(f"[yellow]没有找到匹配的标签: {query}[/yellow]")
        return

      console.print(f"[blue]搜索结果 ({len(tags)} 个)[/blue]")

      # 创建表格
      table = Table(show_header=True, header_style="bold magenta")
      table.add_column("名称", min_width=15)
      table.add_column("描述", min_width=20)
      table.add_column("使用次数", width=8, justify="right")

      for tag in tags:
        name = tag.name
        description = truncate_text(tag.description, 30)
        paper_count = str(tag.paper_count)

        table.add_row(name, description, paper_count)

      console.print(table)

    except Exception as e:
      console.print(f"[red]搜索失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_search())


@tag.command()
@click.argument('name', type=str)
@click.option('--description', '-d', help='新描述')
@click.option('--color', '-c', help='新颜色')
@click.pass_context
def update(
  ctx: click.Context,
  name: str,
  description: Optional[str],
  color: Optional[str]
):
  """更新标签信息"""

  async def _update():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      # 更新标签
      updated_tag = await service.update_tag(
        name=name,
        description=description,
        color=color
      )

      if updated_tag:
        console.print(f"[green]✓ 标签更新成功[/green]")
        console.print(f"名称: {updated_tag.name}")
        if updated_tag.description:
          console.print(f"描述: {updated_tag.description}")
        if updated_tag.color:
          console.print(f"颜色: {updated_tag.color}")
      else:
        console.print(f"[red]标签不存在: {name}[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]更新失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_update())


@tag.command()
@click.argument('name', type=str)
@click.confirmation_option(prompt='确定要删除这个标签吗？')
@click.pass_context
def delete(ctx: click.Context, name: str):
  """删除标签"""

  async def _delete():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      # 删除标签
      success = await service.delete_tag(name)

      if success:
        console.print(f"[green]✓ 标签删除成功[/green]")
      else:
        console.print(f"[red]标签不存在: {name}[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]删除失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_delete())


@tag.command()
@click.confirmation_option(prompt='确定要清理所有未使用的标签吗？')
@click.pass_context
def cleanup(ctx: click.Context):
  """清理未使用的标签"""

  async def _cleanup():
    config = ctx.obj['config']
    service = TagService(config)

    try:
      await service.initialize()

      # 清理未使用的标签
      deleted_count = await service.cleanup_unused_tags()

      if deleted_count > 0:
        console.print(f"[green]✓ 清理完成，删除了 {deleted_count} 个未使用的标签[/green]")
      else:
        console.print("[blue]没有需要清理的标签[/blue]")

    except Exception as e:
      console.print(f"[red]清理失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_cleanup())