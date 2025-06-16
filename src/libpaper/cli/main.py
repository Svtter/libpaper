import asyncio
from pathlib import Path
from typing import Optional

import click

from ..services import CollectionService, PaperService, TagService
from ..storage.config import Config
from .commands import collection, paper, stats, tag


@click.group()
@click.option(
    "--config-path",
    type=click.Path(exists=False, path_type=Path),
    help="配置文件路径 (默认: ~/.libpaper/config.yaml)",
)
@click.pass_context
def cli(ctx: click.Context, config_path: Optional[Path]):
    """
    LibPaper - 文献管理工具

    一个轻量级的研究文献管理工具，支持 PDF 文件存储、分类和标签管理。
    """
    # 加载配置
    if config_path:
        config = Config.load(str(config_path))
    else:
        config = Config.load()

    # 将配置存储在上下文中
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.pass_context
def init(ctx: click.Context):
    """初始化 LibPaper 环境"""

    async def _init():
        config = ctx.obj["config"]

        # 初始化服务
        paper_service = PaperService(config)
        collection_service = CollectionService(config)
        tag_service = TagService(config)

        try:
            await paper_service.initialize()
            await collection_service.initialize()
            await tag_service.initialize()

            click.echo(click.style("✓ LibPaper 初始化完成", fg="green"))
            click.echo(f"数据库路径: {config.get_database_path()}")
            click.echo(f"存储路径: {config.get_storage_path()}")

        finally:
            await paper_service.close()
            await collection_service.close()
            await tag_service.close()

    asyncio.run(_init())


@cli.command()
@click.pass_context
def version(ctx: click.Context):
    """显示版本信息"""
    click.echo("LibPaper v1.0.0")
    click.echo("一个轻量级的研究文献管理工具")


# 添加子命令组
cli.add_command(paper.paper)
cli.add_command(collection.collection)
cli.add_command(tag.tag)
cli.add_command(stats.stats)


if __name__ == "__main__":
    cli()
