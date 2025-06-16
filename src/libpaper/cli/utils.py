from datetime import datetime
from typing import Optional
from uuid import UUID


def format_date(dt: datetime) -> str:
  """格式化日期"""
  if not dt:
    return "-"
  return dt.strftime("%Y-%m-%d")


def format_size(size_bytes: int) -> str:
  """格式化文件大小"""
  if size_bytes == 0:
    return "0B"

  size_names = ["B", "KB", "MB", "GB"]
  size = float(size_bytes)
  i = 0

  while size >= 1024.0 and i < len(size_names) - 1:
    size /= 1024.0
    i += 1

  if i == 0:
    return f"{int(size)}{size_names[i]}"
  else:
    return f"{size:.1f}{size_names[i]}"


def truncate_text(text: Optional[str], max_length: int) -> str:
  """截断文本"""
  if not text:
    return "-"

  if len(text) <= max_length:
    return text

  return text[:max_length-3] + "..."


def parse_uuid(uuid_str: str) -> UUID:
  """解析 UUID 字符串"""
  try:
    # 支持短 ID（前8位）
    if len(uuid_str) == 8:
      # 这里需要从数据库查找完整 UUID
      # 暂时抛出错误，让用户提供完整 UUID
      raise ValueError(f"请提供完整的 UUID，不支持短 ID: {uuid_str}")

    return UUID(uuid_str)
  except ValueError:
    raise ValueError(f"无效的 UUID 格式: {uuid_str}")


def format_list(items: list, separator: str = ", ") -> str:
  """格式化列表为字符串"""
  if not items:
    return "-"
  return separator.join(str(item) for item in items)


def parse_list(text: str, separator: str = ",") -> list:
  """解析字符串为列表"""
  if not text or not text.strip():
    return []
  return [item.strip() for item in text.split(separator) if item.strip()]


def confirm_action(message: str) -> bool:
  """确认操作"""
  response = input(f"{message} (y/N): ").strip().lower()
  return response in ['y', 'yes', '是', 'true']