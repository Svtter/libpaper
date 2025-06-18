"""
Pydantic schemas for LibPaper API
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# Base response models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


# Paper schemas
class PaperBase(BaseModel):
    """Base paper schema"""
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None


class PaperCreate(PaperBase):
    """Paper creation schema"""
    tags: Optional[List[str]] = []
    collection_ids: Optional[List[UUID]] = []


class PaperUpdate(BaseModel):
    """Paper update schema"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None


class PaperResponse(PaperBase):
    """Paper response schema"""
    id: UUID
    file_path: str
    file_hash: str
    file_size: int
    created_at: datetime
    updated_at: datetime
    collections: List["CollectionResponse"] = []
    tags: List["TagResponse"] = []

    class Config:
        from_attributes = True


class PaperListResponse(BaseResponse):
    """Paper list response schema"""
    papers: List[PaperResponse]
    total: int
    offset: int
    limit: int


# Collection schemas
class CollectionBase(BaseModel):
    """Base collection schema"""
    name: str
    description: Optional[str] = None


class CollectionCreate(CollectionBase):
    """Collection creation schema"""
    parent_id: Optional[UUID] = None


class CollectionUpdate(BaseModel):
    """Collection update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class CollectionResponse(CollectionBase):
    """Collection response schema"""
    id: UUID
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    paper_count: int = 0
    children: List["CollectionResponse"] = []

    class Config:
        from_attributes = True


class CollectionListResponse(BaseResponse):
    """Collection list response schema"""
    collections: List[CollectionResponse]


# Tag schemas
class TagBase(BaseModel):
    """Base tag schema"""
    name: str
    description: Optional[str] = None
    color: Optional[str] = None


class TagCreate(TagBase):
    """Tag creation schema"""
    pass


class TagUpdate(BaseModel):
    """Tag update schema"""
    description: Optional[str] = None
    color: Optional[str] = None


class TagResponse(TagBase):
    """Tag response schema"""
    created_at: datetime
    updated_at: datetime
    paper_count: int = 0

    class Config:
        from_attributes = True


class TagListResponse(BaseResponse):
    """Tag list response schema"""
    tags: List[TagResponse]


# Search schemas
class SearchRequest(BaseModel):
    """Search request schema"""
    query: Optional[str] = None
    collection_id: Optional[UUID] = None
    tag_names: Optional[List[str]] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# Stats schemas
class StorageStats(BaseModel):
    """Storage statistics schema"""
    total_papers: int
    total_size: int
    total_size_formatted: str
    storage_path: str


class OverviewStats(BaseModel):
    """Overview statistics schema"""
    total_papers: int
    total_collections: int
    total_tags: int
    storage_stats: StorageStats


class StatsResponse(BaseResponse):
    """Statistics response schema"""
    stats: OverviewStats


# File upload schemas
class FileUploadResponse(BaseResponse):
    """File upload response schema"""
    paper: PaperResponse


# Update forward references
PaperResponse.model_rebuild()
CollectionResponse.model_rebuild()
