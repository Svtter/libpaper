"""
Paper management API endpoints
"""

from typing import List, Optional
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse

from ..dependencies import get_paper_service
from ..schemas import (
    PaperResponse, PaperListResponse, PaperUpdate, PaperCreate,
    SearchRequest, FileUploadResponse, BaseResponse, ErrorResponse
)
from ...services.paper_service import PaperService

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_paper(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    collection_ids: Optional[str] = Form(None),
    service: PaperService = Depends(get_paper_service)
):
    """Upload a new paper file"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse optional parameters
        author_list = authors.split(",") if authors else []
        tag_list = tags.split(",") if tags else []
        collection_list = []
        if collection_ids:
            try:
                collection_list = [UUID(cid.strip()) for cid in collection_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid collection ID format"
                )
        
        # Add paper
        paper = await service.add_paper(
            source_path=temp_path,
            title=title,
            tags=tag_list,
            collection_ids=collection_list,
            override_metadata={"authors": author_list} if author_list else None
        )
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        return FileUploadResponse(
            message="Paper uploaded successfully",
            paper=PaperResponse.model_validate(paper)
        )
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals():
            temp_path.unlink(missing_ok=True)
        
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload paper: {str(e)}"
        )


@router.get("/", response_model=PaperListResponse)
async def list_papers(
    limit: int = 100,
    offset: int = 0,
    service: PaperService = Depends(get_paper_service)
):
    """List all papers"""
    try:
        papers = service.list_papers(limit=limit, offset=offset, with_relations=True)
        total = len(service.list_papers(with_relations=False))
        
        return PaperListResponse(
            papers=[PaperResponse.model_validate(paper) for paper in papers],
            total=total,
            offset=offset,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list papers: {str(e)}"
        )


@router.post("/search", response_model=PaperListResponse)
async def search_papers(
    search_request: SearchRequest,
    service: PaperService = Depends(get_paper_service)
):
    """Search papers"""
    try:
        papers = service.search_papers(
            query=search_request.query,
            collection_id=search_request.collection_id,
            tag_names=search_request.tag_names,
            limit=search_request.limit,
            offset=search_request.offset,
            with_relations=True
        )
        
        # Get total count for pagination
        total_papers = service.search_papers(
            query=search_request.query,
            collection_id=search_request.collection_id,
            tag_names=search_request.tag_names,
            limit=None,
            offset=0,
            with_relations=False
        )
        
        return PaperListResponse(
            papers=[PaperResponse.model_validate(paper) for paper in papers],
            total=len(total_papers),
            offset=search_request.offset,
            limit=search_request.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search papers: {str(e)}"
        )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service)
):
    """Get a specific paper"""
    try:
        paper = service.get_paper(paper_id, with_relations=True)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )
        
        return PaperResponse.model_validate(paper)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get paper: {str(e)}"
        )


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: UUID,
    paper_update: PaperUpdate,
    service: PaperService = Depends(get_paper_service)
):
    """Update a paper"""
    try:
        updated_paper = service.update_paper(
            paper_id=paper_id,
            title=paper_update.title,
            authors=paper_update.authors,
            abstract=paper_update.abstract,
            publication_date=paper_update.publication_date,
            journal=paper_update.journal,
            doi=paper_update.doi
        )
        
        if not updated_paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )
        
        return PaperResponse.model_validate(updated_paper)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update paper: {str(e)}"
        )


@router.delete("/{paper_id}", response_model=BaseResponse)
async def delete_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service)
):
    """Delete a paper"""
    try:
        success = service.delete_paper(paper_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )
        
        return BaseResponse(message="Paper deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete paper: {str(e)}"
        )


@router.get("/{paper_id}/download")
async def download_paper(
    paper_id: UUID,
    service: PaperService = Depends(get_paper_service)
):
    """Download a paper file"""
    try:
        paper = service.get_paper(paper_id, with_relations=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )
        
        file_path = Path(paper.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper file not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=f"{paper.title}.pdf" if paper.title else file_path.name,
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download paper: {str(e)}"
        )


@router.post("/{paper_id}/tags/{tag_name}", response_model=BaseResponse)
async def add_tag_to_paper(
    paper_id: UUID,
    tag_name: str,
    service: PaperService = Depends(get_paper_service)
):
    """Add a tag to a paper"""
    try:
        success = service.add_tag_to_paper(paper_id, tag_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found or tag already exists"
            )
        
        return BaseResponse(message=f"Tag '{tag_name}' added to paper")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tag: {str(e)}"
        )


@router.delete("/{paper_id}/tags/{tag_name}", response_model=BaseResponse)
async def remove_tag_from_paper(
    paper_id: UUID,
    tag_name: str,
    service: PaperService = Depends(get_paper_service)
):
    """Remove a tag from a paper"""
    try:
        success = service.remove_tag_from_paper(paper_id, tag_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found or tag not associated"
            )
        
        return BaseResponse(message=f"Tag '{tag_name}' removed from paper")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove tag: {str(e)}"
        )
