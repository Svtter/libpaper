"""
Tag management API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..dependencies import get_tag_service
from ..schemas import (
    TagResponse, TagListResponse, TagCreate, TagUpdate, BaseResponse
)
from ...services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/", response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    service: TagService = Depends(get_tag_service)
):
    """Create a new tag"""
    try:
        tag = service.create_tag(
            name=tag_data.name,
            description=tag_data.description,
            color=tag_data.color
        )
        
        return TagResponse.model_validate(tag)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tag: {str(e)}"
        )


@router.get("/", response_model=TagListResponse)
async def list_tags(
    service: TagService = Depends(get_tag_service)
):
    """List all tags"""
    try:
        tags = service.list_tags(with_relations=True)
        
        return TagListResponse(
            tags=[TagResponse.model_validate(tag) for tag in tags]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tags: {str(e)}"
        )


@router.get("/search", response_model=TagListResponse)
async def search_tags(
    query: str = Query(..., description="Search query for tag names"),
    service: TagService = Depends(get_tag_service)
):
    """Search tags by name"""
    try:
        tags = service.search_tags(query, with_relations=True)
        
        return TagListResponse(
            tags=[TagResponse.model_validate(tag) for tag in tags]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search tags: {str(e)}"
        )


@router.get("/popular", response_model=TagListResponse)
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=100, description="Number of popular tags to return"),
    service: TagService = Depends(get_tag_service)
):
    """Get most popular tags"""
    try:
        tags = service.get_popular_tags(limit=limit, with_relations=True)
        
        return TagListResponse(
            tags=[TagResponse.model_validate(tag) for tag in tags]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular tags: {str(e)}"
        )


@router.get("/unused", response_model=TagListResponse)
async def get_unused_tags(
    service: TagService = Depends(get_tag_service)
):
    """Get unused tags"""
    try:
        tags = service.get_unused_tags(with_relations=True)
        
        return TagListResponse(
            tags=[TagResponse.model_validate(tag) for tag in tags]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unused tags: {str(e)}"
        )


@router.get("/{tag_name}", response_model=TagResponse)
async def get_tag(
    tag_name: str,
    service: TagService = Depends(get_tag_service)
):
    """Get a specific tag"""
    try:
        # This would require adding a get_tag method to TagService
        tags = service.list_tags(with_relations=True)
        tag = next((t for t in tags if t.name == tag_name), None)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        return TagResponse.model_validate(tag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tag: {str(e)}"
        )


@router.put("/{tag_name}", response_model=TagResponse)
async def update_tag(
    tag_name: str,
    tag_update: TagUpdate,
    service: TagService = Depends(get_tag_service)
):
    """Update a tag"""
    try:
        updated_tag = service.update_tag(
            name=tag_name,
            description=tag_update.description,
            color=tag_update.color
        )
        
        if not updated_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        return TagResponse.model_validate(updated_tag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tag: {str(e)}"
        )


@router.delete("/{tag_name}", response_model=BaseResponse)
async def delete_tag(
    tag_name: str,
    service: TagService = Depends(get_tag_service)
):
    """Delete a tag"""
    try:
        success = service.delete_tag(tag_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        return BaseResponse(message="Tag deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tag: {str(e)}"
        )


@router.post("/cleanup", response_model=BaseResponse)
async def cleanup_unused_tags(
    service: TagService = Depends(get_tag_service)
):
    """Clean up unused tags"""
    try:
        count = service.cleanup_unused_tags()
        
        return BaseResponse(message=f"Cleaned up {count} unused tags")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup tags: {str(e)}"
        )
