import os
import warnings
from pathlib import Path
from typing import List, Optional

warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

from config import config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag_system import RAGSystem

# Initialize FastAPI app
app = FastAPI(title="Markdown RAG System", root_path="")

# Add trusted host middleware for proxy
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Enable CORS with proper settings for proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for queries"""

    query: str
    limit: Optional[int] = 5


class QueryResponse(BaseModel):
    """Response model for queries"""

    answer: str
    sources: List[str]


class DocumentStats(BaseModel):
    """Response model for document statistics"""

    total_documents: int
    file_names: List[str]


# API Endpoints


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Process a query and return response with sources"""
    try:
        # Process query using RAG system
        result = rag_system.query(request.query, request.limit or 5)

        return QueryResponse(answer=result["answer"], sources=result["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents", response_model=DocumentStats)
async def get_document_stats():
    """Get document analytics and statistics"""
    try:
        stats = rag_system.get_document_stats()
        return DocumentStats(
            total_documents=stats["total_documents"],
            file_names=stats["file_names"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Load initial documents on startup"""
    # Initialize RAG system with docs folder
    docs_path = "../docs"
    rag = None

    if os.path.exists(docs_path):
        print("Loading initial documents...")
        try:
            # Initialize and load documents
            rag = RAGSystem(docs_path, chroma_path=config.CHROMA_PATH)
            print(f"RAG system initialized with documents from: {docs_path}")

            # Store globally for use in endpoints
            globals()["rag_system"] = rag
        except Exception as e:
            print(f"Error loading documents: {e}")
            # Initialize empty system
            rag = RAGSystem.__new__(RAGSystem)
            rag.md_processor = None
            rag.vector_store = None
            rag.folder_path = docs_path
            globals()["rag_system"] = rag
    else:
        print(f"Docs folder not found: {docs_path}")
        # Initialize empty system
        rag = RAGSystem.__new__(RAGSystem)
        rag.md_processor = None
        rag.vector_store = None
        rag.folder_path = docs_path
        globals()["rag_system"] = rag


# Custom static file handler with no-cache headers for development


class DevStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            # Add no-cache headers for development
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


# Serve static files for the frontend
app.mount("/", DevStaticFiles(directory="../frontend", html=True), name="static")
