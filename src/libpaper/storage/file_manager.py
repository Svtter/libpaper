import hashlib
import shutil
import aiofiles
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from .config import Config


class FileManager:
    """文件存储管理类"""

    def __init__(self, config: Config):
        """
        初始化文件管理器

        Args:
            config: 配置对象
        """
        self.config = config
        self.storage_path = config.get_papers_storage_path()
        self.metadata_path = config.get_metadata_storage_path()

    async def calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件的 SHA256 哈希值

        Args:
            file_path: 文件路径

        Returns:
            SHA256 哈希值（小写十六进制字符串）
        """
        hash_sha256 = hashlib.sha256()

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    def generate_storage_path(self, file_hash: str) -> Path:
        """
        根据哈希值生成存储路径

        Args:
            file_hash: 文件哈希值

        Returns:
            存储路径
        """
        now = datetime.now()
        year = str(now.year)
        month = f"{now.month:02d}"

        # 使用年/月的分层结构
        storage_dir = self.storage_path / year / month
        storage_dir.mkdir(parents=True, exist_ok=True)

        return storage_dir / f"{file_hash}.pdf"

    async def store_file(self, source_path: Path, file_hash: str) -> Path:
        """
        存储文件到指定位置

        Args:
            source_path: 源文件路径
            file_hash: 文件哈希值

        Returns:
            存储后的文件路径
        """
        target_path = self.generate_storage_path(file_hash)

        # 如果文件已存在，直接返回路径
        if target_path.exists():
            return target_path

        # 复制文件到目标位置
        await self._copy_file_async(source_path, target_path)

        return target_path

    async def file_exists(self, file_hash: str) -> bool:
        """
        检查文件是否已存在

        Args:
            file_hash: 文件哈希值

        Returns:
            文件是否存在
        """
        target_path = self.generate_storage_path(file_hash)
        return target_path.exists()

    async def delete_file(self, file_path: Path) -> bool:
        """
        删除存储的文件

        Args:
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        try:
            if file_path.exists():
                file_path.unlink()

                # 尝试删除空的父目录
                self._cleanup_empty_directories(file_path.parent)

                return True
        except Exception:
            pass

        return False

    async def get_file_size(self, file_path: Path) -> int:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            文件大小（字节）
        """
        return file_path.stat().st_size

    async def validate_pdf_file(self, file_path: Path) -> bool:
        """
        验证文件是否为有效的 PDF

        Args:
            file_path: 文件路径

        Returns:
            是否为有效的 PDF 文件
        """
        if not file_path.exists():
            return False

        try:
            # 检查文件扩展名
            if file_path.suffix.lower() != '.pdf':
                return False

            # 检查 PDF 文件头
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(5)
                if not header.startswith(b'%PDF-'):
                    return False

            return True

        except Exception:
            return False

    async def process_file(self, file_path: Path) -> Tuple[str, int, Path]:
        """
        处理文件：验证、计算哈希、存储

        Args:
            file_path: 源文件路径

        Returns:
            (文件哈希, 文件大小, 存储路径)

        Raises:
            ValueError: 文件无效
            FileExistsError: 文件已存在
        """
        # 验证文件
        if not await self.validate_pdf_file(file_path):
            raise ValueError(f"无效的 PDF 文件: {file_path}")

        # 计算哈希值
        file_hash = await self.calculate_file_hash(file_path)

        # 检查文件是否已存在
        if await self.file_exists(file_hash):
            existing_path = self.generate_storage_path(file_hash)
            raise FileExistsError(f"文件已存在: {existing_path}")

        # 获取文件大小
        file_size = await self.get_file_size(file_path)

        # 存储文件
        storage_path = await self.store_file(file_path, file_hash)

        return file_hash, file_size, storage_path

    def get_storage_stats(self) -> dict:
        """
        获取存储统计信息

        Returns:
            存储统计信息字典
        """
        if not self.storage_path.exists():
            return {
                'total_files': 0,
                'total_size': 0,
                'storage_path': str(self.storage_path)
            }

        total_files = 0
        total_size = 0

        for file_path in self.storage_path.rglob('*.pdf'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_path': str(self.storage_path)
        }

    async def _copy_file_async(self, source: Path, target: Path) -> None:
        """
        异步复制文件

        Args:
            source: 源文件路径
            target: 目标文件路径
        """
        async with aiofiles.open(source, 'rb') as src:
            async with aiofiles.open(target, 'wb') as dst:
                while chunk := await src.read(8192):
                    await dst.write(chunk)

    def _cleanup_empty_directories(self, directory: Path) -> None:
        """
        清理空目录

        Args:
            directory: 要清理的目录
        """
        try:
            # 只清理存储路径下的目录
            if not directory.is_relative_to(self.storage_path):
                return

            # 如果目录为空且不是根存储目录，则删除
            if (directory != self.storage_path and
                directory.exists() and
                not any(directory.iterdir())):
                directory.rmdir()

                # 递归清理父目录
                self._cleanup_empty_directories(directory.parent)

        except Exception:
            # 忽略清理错误
            pass