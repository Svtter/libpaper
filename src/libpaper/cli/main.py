"""LibPaper CLI 主入口"""

from pathlib import Path

import click

from ..services.collection_service import CollectionService
from ..services.paper_service import PaperService
from ..services.tag_service import TagService
from ..storage.config import Config
from ..storage.database import Database
from ..storage.file_manager import FileManager
from .commands.collection import collection_commands
from .commands.paper import paper_commands
from .commands.stats import stats_commands
from .commands.tag import tag_commands


@click.group()
@click.option(
    "--config-path",
    type=click.Path(),
    help="配置文件路径",
)
@click.pass_context
def cli(ctx, config_path):
    """LibPaper - 研究文献管理工具"""
    ctx.ensure_object(dict)

    # 加载配置
    if config_path:
        config = Config.load(Path(config_path))
    else:
        config = Config.load()

    ctx.obj["config"] = config


@cli.command()
@click.pass_context
def init(ctx):
    """初始化 LibPaper"""
    config = ctx.obj["config"]

    def _init():
        """内部初始化函数"""
        # 创建服务实例
        db = Database(config.get_database_path())
        file_manager = FileManager(config)

        paper_service = PaperService(db, file_manager)
        collection_service = CollectionService(config)
        tag_service = TagService(config)

        # 初始化服务
        paper_service.initialize()
        collection_service.initialize()
        tag_service.initialize()

        click.echo("✅ LibPaper 初始化完成!")

        # 关闭服务
        paper_service.close()
        collection_service.close()
        tag_service.close()

    _init()


@cli.command()
def version():
    """显示版本信息"""
    click.echo("LibPaper 0.1.0")


# 注册子命令组
cli.add_command(paper_commands, name="paper")
cli.add_command(collection_commands, name="collection")
cli.add_command(tag_commands, name="tag")
cli.add_command(stats_commands, name="stats")


if __name__ == "__main__":
    cli()
