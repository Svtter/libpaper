import asyncio
import click
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from ...services import CollectionService
from ..utils import parse_uuid, truncate_text


console = Console()


@click.group()
def collection():
  """分类管理"""
  pass


@collection.command()
@click.argument('name', type=str)
@click.option('--description', '-d', help='分类描述')
@click.option('--parent', '-p', help='父分类ID')
@click.pass_context
def create(
  ctx: click.Context,
  name: str,
  description: Optional[str],
  parent: Optional[str]
):
  """创建新分类"""

  async def _create():
    config = ctx.obj['config']
    service = CollectionService(config)

    try:
      await service.initialize()

      # 解析父分类ID
      parent_id = parse_uuid(parent) if parent else None

      # 创建分类
      collection = await service.create_collection(
        name=name,
        description=description,
        parent_id=parent_id
      )

      console.print(f"[green]✓ 分类创建成功[/green]")
      console.print(f"ID: {collection.id}")
      console.print(f"名称: {collection.name}")
      if collection.description:
        console.print(f"描述: {collection.description}")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]创建失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_create())


@collection.command()
@click.option('--tree', '-t', is_flag=True, help='以树形结构显示')
@click.pass_context
def list(ctx: click.Context, tree: bool):
  """列出所有分类"""

  async def _list():
    config = ctx.obj['config']
    service = CollectionService(config)

    try:
      await service.initialize()

      collections = await service.list_collections()

      if not collections:
        console.print("[yellow]没有找到分类[/yellow]")
        return

      if tree:
        # 树形显示
        console.print("[blue]分类结构[/blue]")

        root_collections = await service.get_root_collections()
        tree_display = Tree("分类")

        async def add_collection_to_tree(parent_node, collection):
          node_text = f"{collection.name}"
          if collection.description:
            node_text += f" ({collection.description})"

          node = parent_node.add(node_text)

          # 添加子分类
          children = await service.get_child_collections(collection.id)
          for child in children:
            await add_collection_to_tree(node, child)

        for root_collection in root_collections:
          await add_collection_to_tree(tree_display, root_collection)

        console.print(tree_display)

      else:
        # 表格显示
        console.print(f"[blue]所有分类 ({len(collections)} 个)[/blue]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=8)
        table.add_column("名称", min_width=15)
        table.add_column("描述", min_width=20)
        table.add_column("父分类", width=15)
        table.add_column("文献数", width=8, justify="right")

        for collection in collections:
          short_id = str(collection.id)[:8]
          name = collection.name
          description = truncate_text(collection.description, 30)

          # 查找父分类名称
          parent_name = "-"
          if collection.parent_id:
            for c in collections:
              if c.id == collection.parent_id:
                parent_name = c.name
                break

          paper_count = str(collection.paper_count)

          table.add_row(short_id, name, description, parent_name, paper_count)

        console.print(table)

    except Exception as e:
      console.print(f"[red]查询失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_list())


@collection.command()
@click.argument('collection_id', type=str)
@click.option('--name', '-n', help='新名称')
@click.option('--description', '-d', help='新描述')
@click.option('--parent', '-p', help='新父分类ID')
@click.pass_context
def update(
  ctx: click.Context,
  collection_id: str,
  name: Optional[str],
  description: Optional[str],
  parent: Optional[str]
):
  """更新分类信息"""

  async def _update():
    config = ctx.obj['config']
    service = CollectionService(config)

    try:
      await service.initialize()

      # 解析ID
      collection_uuid = parse_uuid(collection_id)
      parent_id = parse_uuid(parent) if parent else None

      # 更新分类
      updated_collection = await service.update_collection(
        collection_id=collection_uuid,
        name=name,
        description=description,
        parent_id=parent_id
      )

      if updated_collection:
        console.print(f"[green]✓ 分类更新成功[/green]")
        console.print(f"名称: {updated_collection.name}")
      else:
        console.print(f"[red]分类不存在: {collection_id}[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]更新失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_update())


@collection.command()
@click.argument('collection_id', type=str)
@click.confirmation_option(prompt='确定要删除这个分类吗？')
@click.pass_context
def delete(ctx: click.Context, collection_id: str):
  """删除分类"""

  async def _delete():
    config = ctx.obj['config']
    service = CollectionService(config)

    try:
      await service.initialize()

      # 解析ID
      collection_uuid = parse_uuid(collection_id)

      # 删除分类
      success = await service.delete_collection(collection_uuid)

      if success:
        console.print(f"[green]✓ 分类删除成功[/green]")
      else:
        console.print(f"[red]分类不存在: {collection_id}[/red]")

    except ValueError as e:
      console.print(f"[red]错误: {e}[/red]")
    except Exception as e:
      console.print(f"[red]删除失败: {e}[/red]")
    finally:
      await service.close()

  asyncio.run(_delete())