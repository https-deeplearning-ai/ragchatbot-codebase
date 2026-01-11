import os
import sys
import tempfile
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models import Course, CourseChunk, Lesson
from vector_store import SearchResults


@pytest.fixture
def sample_course():
    """Create a sample course for testing"""
    lessons = [
        Lesson(
            lesson_number=1,
            title="Introduction",
            lesson_link="https://example.com/lesson1",
        ),
        Lesson(
            lesson_number=2,
            title="Advanced Topics",
            lesson_link="https://example.com/lesson2",
        ),
        Lesson(
            lesson_number=3,
            title="Conclusion",
            lesson_link="https://example.com/lesson3",
        ),
    ]

    return Course(
        title="Building Towards Computer Use with Anthropic",
        course_link="https://example.com/course",
        instructor="Colt Steele",
        lessons=lessons,
    )


@pytest.fixture
def sample_course_chunks():
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="Welcome to Building Toward Computer Use with Anthropic. This course covers computer automation.",
            course_title="Building Towards Computer Use with Anthropic",
            lesson_number=1,
            chunk_index=0,
        ),
        CourseChunk(
            content="In this lesson, we'll explore advanced topics including tool calling and agent workflows.",
            course_title="Building Towards Computer Use with Anthropic",
            lesson_number=2,
            chunk_index=1,
        ),
        CourseChunk(
            content="Computer use capability is built by using many features of large language models.",
            course_title="Building Towards Computer Use with Anthropic",
            lesson_number=1,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing"""
    return SearchResults(
        documents=[
            "Welcome to Building Toward Computer Use with Anthropic. This course covers computer automation.",
            "In this lesson, we'll explore advanced topics including tool calling and agent workflows.",
        ],
        metadata=[
            {
                "course_title": "Building Towards Computer Use with Anthropic",
                "lesson_number": 1,
                "chunk_index": 0,
            },
            {
                "course_title": "Building Towards Computer Use with Anthropic",
                "lesson_number": 2,
                "chunk_index": 1,
            },
        ],
        distances=[0.1, 0.2],
    )


@pytest.fixture
def empty_search_results():
    """Create empty search results for testing"""
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def error_search_results():
    """Create error search results for testing"""
    return SearchResults.empty("Search error: Database connection failed")


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing"""
    mock = Mock()
    mock.search.return_value = SearchResults(
        documents=["Sample document content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.1],
    )
    mock._resolve_course_name.return_value = "Test Course"
    mock.get_lesson_link.return_value = "https://example.com/lesson1"
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing"""
    mock_client = Mock()

    # Mock response for direct text response
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "This is a test response from Claude."
    mock_response.stop_reason = "end_turn"

    # Mock response for tool use
    mock_tool_response = Mock()
    mock_tool_response.stop_reason = "tool_use"
    mock_tool_content = Mock()
    mock_tool_content.type = "tool_use"
    mock_tool_content.name = "search_course_content"
    mock_tool_content.id = "tool_123"
    mock_tool_content.input = {"query": "test query"}
    mock_tool_response.content = [mock_tool_content]

    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_tool_manager():
    """Create a mock tool manager for testing"""
    mock = Mock()
    mock.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"}
                },
                "required": ["query"],
            },
        }
    ]
    mock.execute_tool.return_value = "Mock search result"
    mock.get_last_sources.return_value = ["Test Course - Lesson 1"]
    mock.get_last_source_links.return_value = ["https://example.com/lesson1"]
    return mock


@pytest.fixture
def test_config():
    """Create a test configuration with proper settings"""
    return Config(
        ANTHROPIC_API_KEY="test-api-key",
        ANTHROPIC_MODEL="claude-sonnet-4-20250514",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=5,  # Set to proper value, not 0
        MAX_HISTORY=2,
        CHROMA_PATH="./test_chroma_db",
    )


@pytest.fixture
def broken_config():
    """Create a configuration with the broken MAX_RESULTS=0 setting"""
    return Config(
        ANTHROPIC_API_KEY="test-api-key",
        ANTHROPIC_MODEL="claude-sonnet-4-20250514",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=0,  # This is the broken setting
        MAX_HISTORY=2,
        CHROMA_PATH="./test_chroma_db",
    )


@pytest.fixture
def temp_chroma_db():
    """Create a temporary ChromaDB directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_chroma_collection():
    """Create a mock ChromaDB collection for testing"""
    mock = Mock()
    mock.query.return_value = {
        "documents": [["Sample document"]],
        "metadatas": [[{"course_title": "Test Course", "lesson_number": 1}]],
        "distances": [[0.1]],
    }
    mock.get.return_value = {
        "ids": ["test_course_1"],
        "metadatas": [
            {
                "title": "Test Course",
                "instructor": "Test Instructor",
                "course_link": "https://example.com/course",
                "lessons_json": '[{"lesson_number": 1, "lesson_title": "Test Lesson", "lesson_link": "https://example.com/lesson1"}]',
                "lesson_count": 1,
            }
        ],
    }
    return mock


# Test data constants
SAMPLE_COURSE_TEXT = """Course Title: Building Towards Computer Use with Anthropic
Course Link: https://www.deeplearning.ai/short-courses/building-toward-computer-use-with-anthropic/
Course Instructor: Colt Steele

Lesson 1: Introduction
Lesson Link: https://learn.deeplearning.ai/courses/building-toward-computer-use-with-anthropic/lesson/1/introduction
Welcome to Building Toward Computer Use with Anthropic. This course covers computer automation.

Lesson 2: Advanced Topics  
Lesson Link: https://learn.deeplearning.ai/courses/building-toward-computer-use-with-anthropic/lesson/2/advanced
In this lesson, we'll explore advanced topics including tool calling and agent workflows.
"""

SAMPLE_QUERY_RESPONSES = {
    "general": "This is a general knowledge response.",
    "course_specific": "Based on the search results, here is information about the course content.",
    "tool_use": "I'll search for that information in the course materials.",
}


@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system for API testing"""
    mock = Mock()
    mock.query.return_value = (
        "This is a test response about course content.",
        ["Building Towards Computer Use with Anthropic - Lesson 1"],
        ["https://example.com/lesson1"],
    )
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": [
            "Building Towards Computer Use with Anthropic",
            "Advanced AI Techniques",
        ],
    }
    mock.session_manager.create_session.return_value = "test-session-123"
    mock.session_manager.clear_session.return_value = None
    return mock


@pytest.fixture
def test_app():
    """Create a test FastAPI app with mocked dependencies"""
    from typing import List, Optional

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from pydantic import BaseModel

    # Create test app without static file mounting
    app = FastAPI(title="Course Materials RAG System Test", root_path="")

    # Add middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Pydantic models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        source_links: List[Optional[str]]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    class ClearSessionRequest(BaseModel):
        session_id: str

    # Mock RAG system
    mock_rag = Mock()
    mock_rag.query.return_value = (
        "This is a test response about course content.",
        ["Building Towards Computer Use with Anthropic - Lesson 1"],
        ["https://example.com/lesson1"],
    )
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": [
            "Building Towards Computer Use with Anthropic",
            "Advanced AI Techniques",
        ],
    }
    mock_rag.session_manager.create_session.return_value = "test-session-123"
    mock_rag.session_manager.clear_session.return_value = None

    # API endpoints
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        session_id = request.session_id or mock_rag.session_manager.create_session()
        answer, sources, source_links = mock_rag.query(request.query, session_id)
        return QueryResponse(
            answer=answer,
            sources=sources,
            source_links=source_links,
            session_id=session_id,
        )

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        analytics = mock_rag.get_course_analytics()
        return CourseStats(
            total_courses=analytics["total_courses"],
            course_titles=analytics["course_titles"],
        )

    @app.post("/api/clear-session")
    async def clear_session(request: ClearSessionRequest):
        mock_rag.session_manager.clear_session(request.session_id)
        return {"status": "success", "message": "Session cleared successfully"}

    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System API"}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app"""
    return TestClient(test_app)


@pytest.fixture
def sample_query_request():
    """Sample query request for testing"""
    return {"query": "What is computer use in AI?", "session_id": "test-session-123"}


@pytest.fixture
def sample_clear_session_request():
    """Sample clear session request for testing"""
    return {"session_id": "test-session-123"}
