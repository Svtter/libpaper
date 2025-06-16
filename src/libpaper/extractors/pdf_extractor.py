import pypdf
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import re


class PDFExtractor:
  """PDF 元数据提取器"""

  def __init__(self):
    """初始化 PDF 提取器"""
    pass

  async def extract_metadata(self, file_path: Path) -> Dict[str, any]:
    """
    从 PDF 文件提取元数据

    Args:
      file_path: PDF 文件路径

    Returns:
      提取的元数据字典
    """
    try:
      with open(file_path, 'rb') as file:
        reader = pypdf.PdfReader(file)

        # 获取基础元数据
        metadata = {}

        # 从 PDF 元数据提取
        if reader.metadata:
          pdf_meta = reader.metadata

          # 标题
          if '/Title' in pdf_meta:
            title = str(pdf_meta['/Title']).strip()
            if title:
              metadata['title'] = self._clean_text(title)

          # 作者
          if '/Author' in pdf_meta:
            author_str = str(pdf_meta['/Author']).strip()
            if author_str:
              authors = self._parse_authors(author_str)
              if authors:
                metadata['authors'] = authors

          # 主题（可能包含关键词）
          if '/Subject' in pdf_meta:
            subject = str(pdf_meta['/Subject']).strip()
            if subject:
              metadata['subject'] = self._clean_text(subject)

          # 创建日期
          if '/CreationDate' in pdf_meta:
            creation_date = self._parse_pdf_date(pdf_meta['/CreationDate'])
            if creation_date:
              metadata['creation_date'] = creation_date

        # 尝试从文档内容提取信息
        text_metadata = await self._extract_from_content(reader)

        # 合并元数据（内容提取优先级更高）
        metadata.update(text_metadata)

        # 添加文档统计信息
        metadata['page_count'] = len(reader.pages)

        return metadata

    except Exception as e:
      # 如果提取失败，返回空元数据
      return {
        'extraction_error': str(e),
        'page_count': 0
      }

  async def _extract_from_content(self, reader: pypdf.PdfReader) -> Dict[str, any]:
    """从 PDF 内容提取元数据"""
    metadata = {}

    try:
      # 只读取前几页以提取标题和摘要
      text_content = ""
      max_pages = min(3, len(reader.pages))

      for i in range(max_pages):
        try:
          page_text = reader.pages[i].extract_text()
          text_content += page_text + "\n"
        except:
          continue

      if text_content:
        # 提取标题（通常在第一页的前几行）
        title = self._extract_title_from_text(text_content)
        if title:
          metadata['title'] = title

        # 提取摘要
        abstract = self._extract_abstract_from_text(text_content)
        if abstract:
          metadata['abstract'] = abstract

        # 提取 DOI
        doi = self._extract_doi_from_text(text_content)
        if doi:
          metadata['doi'] = doi

    except Exception:
      pass

    return metadata

  def _extract_title_from_text(self, text: str) -> Optional[str]:
    """从文本中提取标题"""
    lines = text.split('\n')

    # 查找看起来像标题的行
    for i, line in enumerate(lines[:10]):  # 只检查前10行
      line = line.strip()

      # 跳过太短或太长的行
      if len(line) < 10 or len(line) > 200:
        continue

      # 跳过包含特定关键词的行（可能是期刊名、作者等）
      skip_keywords = ['abstract', 'keywords', 'introduction', 'journal', 'volume', 'number', 'page']
      if any(keyword in line.lower() for keyword in skip_keywords):
        continue

      # 如果行主要由大写字母组成或者格式看起来像标题
      if (line.isupper() or
          (line[0].isupper() and len(line.split()) > 2) or
          re.match(r'^[A-Z].*[.!?]?$', line)):
        return self._clean_text(line)

    return None

  def _extract_abstract_from_text(self, text: str) -> Optional[str]:
    """从文本中提取摘要"""
    # 查找 Abstract 关键词
    abstract_pattern = r'(?i)abstract[:\s]*\n?(.*?)(?=\n\s*(?:keywords?|introduction|1\.|i\.|contents)|$)'
    match = re.search(abstract_pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
      abstract = match.group(1).strip()
      # 清理和限制长度
      abstract = self._clean_text(abstract)
      if len(abstract) > 50 and len(abstract) < 2000:  # 合理的摘要长度
        return abstract

    return None

  def _extract_doi_from_text(self, text: str) -> Optional[str]:
    """从文本中提取 DOI"""
    # DOI 正则表达式
    doi_pattern = r'(?i)doi:?\s*(10\.\d+/[^\s\]]+)'
    match = re.search(doi_pattern, text)

    if match:
      doi = match.group(1).strip()
      # 移除末尾的标点符号
      doi = re.sub(r'[.,;)\]]+$', '', doi)
      return doi

    return None

  def _parse_authors(self, author_str: str) -> List[str]:
    """解析作者字符串"""
    # 清理作者字符串
    author_str = self._clean_text(author_str)

    # 常见的分隔符
    separators = [',', ';', ' and ', ' & ', '\n']

    authors = [author_str]  # 默认整个字符串作为一个作者

    # 尝试用不同分隔符分割
    for sep in separators:
      if sep in author_str:
        authors = [author.strip() for author in author_str.split(sep)]
        break

    # 过滤和清理作者名
    clean_authors = []
    for author in authors:
      author = author.strip()
      if len(author) > 2 and len(author) < 100:  # 合理的作者名长度
        clean_authors.append(author)

    return clean_authors

  def _parse_pdf_date(self, date_obj) -> Optional[datetime]:
    """解析 PDF 日期对象"""
    try:
      if hasattr(date_obj, 'year'):
        return date_obj

      # PDF 日期格式：D:YYYYMMDDHHmmSSOHH'mm'
      date_str = str(date_obj)
      if date_str.startswith('D:'):
        date_str = date_str[2:]

      # 提取年月日
      if len(date_str) >= 8:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])

        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
          return datetime(year, month, day)

    except (ValueError, AttributeError):
      pass

    return None

  def _clean_text(self, text: str) -> str:
    """清理文本"""
    if not text:
      return ""

    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())

    # 移除特殊字符（保留基本标点）
    text = re.sub(r'[^\w\s\-.,;:()[\]{}\"\'!?]', '', text)

    return text.strip()

  def get_supported_formats(self) -> List[str]:
    """获取支持的文件格式"""
    return ['.pdf']

  def is_supported_file(self, file_path: Path) -> bool:
    """检查文件是否支持"""
    return file_path.suffix.lower() in self.get_supported_formats()