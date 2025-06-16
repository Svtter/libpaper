import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """存储配置"""
    base_path: str = Field(default="~/.libpaper", description="基础存储路径")
    database_file: str = Field(default="library.db", description="数据库文件名")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = Field(default="sqlite", description="数据库类型")
    path: Optional[str] = Field(None, description="数据库路径")


class CLIConfig(BaseModel):
    """CLI 配置"""
    default_page_size: int = Field(default=20, description="默认分页大小")
    date_format: str = Field(default="%Y-%m-%d", description="日期格式")


class PDFConfig(BaseModel):
    """PDF 处理配置"""
    extract_metadata: bool = Field(default=True, description="是否提取元数据")
    extract_text: bool = Field(default=False, description="是否提取文本内容")


class Config(BaseModel):
    """主配置类"""
    storage: StorageConfig = Field(default_factory=StorageConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    pdf: PDFConfig = Field(default_factory=PDFConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """
        加载配置文件

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径

        Returns:
            Config 实例
        """
        if config_path is None:
            config_path = cls.get_default_config_path()

        config_file = Path(config_path)

        # 如果配置文件不存在，创建默认配置
        if not config_file.exists():
            config = cls()
            config.save(config_path)
            return config

        # 加载配置文件
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}

            # 合并环境变量
            config_data = cls._merge_env_vars(config_data)

            return cls(**config_data)
        except Exception as e:
            raise ValueError(f"配置文件加载失败: {e}")

    def save(self, config_path: Optional[str] = None) -> None:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        if config_path is None:
            config_path = self.get_default_config_path()

        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_data = self.dict()

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    @staticmethod
    def get_default_config_path() -> str:
        """获取默认配置文件路径"""
        return str(Path.home() / ".libpaper" / "config.yaml")

    @staticmethod
    def _merge_env_vars(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """合并环境变量到配置中"""
        # 存储路径
        if storage_path := os.getenv('LIBPAPER_STORAGE_PATH'):
            config_data.setdefault('storage', {})['base_path'] = storage_path

        # 数据库路径
        if db_path := os.getenv('LIBPAPER_DATABASE_PATH'):
            config_data.setdefault('database', {})['path'] = db_path

        return config_data

    def get_storage_path(self) -> Path:
        """获取存储路径"""
        return Path(self.storage.base_path).expanduser()

    def get_database_path(self) -> Path:
        """获取数据库路径"""
        if self.database.path:
            return Path(self.database.path).expanduser()

        return self.get_storage_path() / self.storage.database_file

    def get_papers_storage_path(self) -> Path:
        """获取 PDF 文件存储路径"""
        return self.get_storage_path() / "storage" / "papers"

    def get_metadata_storage_path(self) -> Path:
        """获取元数据存储路径"""
        return self.get_storage_path() / "storage" / "metadata"

    def ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        paths_to_create = [
            self.get_storage_path(),
            self.get_papers_storage_path(),
            self.get_metadata_storage_path(),
        ]

        for path in paths_to_create:
            path.mkdir(parents=True, exist_ok=True)