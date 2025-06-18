"""
FastAPI application for LibPaper
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import papers_router, collections_router, tags_router
from .dependencies import get_paper_service, get_collection_service, get_tag_service
from .schemas import StatsResponse, OverviewStats, StorageStats

# Create FastAPI app
app = FastAPI(
    title="LibPaper API",
    description="A headless library for research paper management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(papers_router)
app.include_router(collections_router)
app.include_router(tags_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "LibPaper API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/stats", response_model=StatsResponse, tags=["stats"])
async def get_stats():
    """Get system statistics"""
    try:
        from .dependencies import get_paper_service, get_collection_service, get_tag_service
        
        # Get services (this is a simplified approach)
        # In a real implementation, you'd want to properly inject dependencies
        paper_service = None
        collection_service = None
        tag_service = None
        
        # For now, return mock data
        # You would implement this properly with actual service calls
        storage_stats = StorageStats(
            total_papers=0,
            total_size=0,
            total_size_formatted="0 B",
            storage_path="/path/to/storage"
        )
        
        overview_stats = OverviewStats(
            total_papers=0,
            total_collections=0,
            total_tags=0,
            storage_stats=storage_stats
        )
        
        return StatsResponse(stats=overview_stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
