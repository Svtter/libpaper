"""
Collection management API endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_collection_service
from ..schemas import (
    CollectionResponse, CollectionListResponse, CollectionCreate, 
    CollectionUpdate, BaseResponse
)
from ...services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("/", response_model=CollectionResponse)
async def create_collection(
    collection_data: CollectionCreate,
    service: CollectionService = Depends(get_collection_service)
):
    """Create a new collection"""
    try:
        collection = service.create_collection(
            name=collection_data.name,
            description=collection_data.description,
            parent_id=collection_data.parent_id
        )
        
        return CollectionResponse.model_validate(collection)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.get("/", response_model=CollectionListResponse)
async def list_collections(
    tree: bool = False,
    service: CollectionService = Depends(get_collection_service)
):
    """List all collections"""
    try:
        if tree:
            # Return only root collections with their children
            collections = service.get_root_collections(with_relations=True)
        else:
            # Return all collections flat
            collections = service.list_collections(with_relations=True)
        
        return CollectionListResponse(
            collections=[CollectionResponse.model_validate(col) for col in collections]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    service: CollectionService = Depends(get_collection_service)
):
    """Get a specific collection"""
    try:
        # This would require adding a get_collection method to CollectionService
        collections = service.list_collections(with_relations=True)
        collection = next((c for c in collections if c.id == collection_id), None)
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        return CollectionResponse.model_validate(collection)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}"
        )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    collection_update: CollectionUpdate,
    service: CollectionService = Depends(get_collection_service)
):
    """Update a collection"""
    try:
        updated_collection = service.update_collection(
            collection_id=collection_id,
            name=collection_update.name,
            description=collection_update.description,
            parent_id=collection_update.parent_id
        )
        
        if not updated_collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        return CollectionResponse.model_validate(updated_collection)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update collection: {str(e)}"
        )


@router.delete("/{collection_id}", response_model=BaseResponse)
async def delete_collection(
    collection_id: UUID,
    service: CollectionService = Depends(get_collection_service)
):
    """Delete a collection"""
    try:
        success = service.delete_collection(collection_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        return BaseResponse(message="Collection deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.get("/{collection_id}/children", response_model=CollectionListResponse)
async def get_collection_children(
    collection_id: UUID,
    service: CollectionService = Depends(get_collection_service)
):
    """Get child collections of a specific collection"""
    try:
        children = service.get_child_collections(collection_id, with_relations=True)
        
        return CollectionListResponse(
            collections=[CollectionResponse.model_validate(col) for col in children]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection children: {str(e)}"
        )
