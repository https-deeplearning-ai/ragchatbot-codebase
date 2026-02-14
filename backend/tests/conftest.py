import os
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models import Document, DocumentChunk
from vector_store import SearchResults


@pytest.fixture
def test_config():
    """Create a test configuration with proper settings"""
    return Config(
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=5,
        CHROMA_PATH="./test_chroma_db",
    )


@pytest.fixture
def sample_document():
    """Create a sample document for testing"""
    return Document(
        file_name="test.md",
        file_path="/path/to/test.md",
        title="Test Document",
        sections=["Introduction", "Advanced Topics"],
    )


@pytest.fixture
def sample_document_chunks():
    """Create sample document chunks for testing"""
    return [
        DocumentChunk(
            content="[文件: test.md | 章节: Introduction]\n\nThis is the introduction content.",
            file_name="test.md",
            file_path="/path/to/test.md",
            section_title="Introduction",
            chunk_index=0,
        ),
        DocumentChunk(
            content="[文件: test.md | 章节: Advanced Topics]\n\nThis covers advanced topics.",
            file_name="test.md",
            file_path="/path/to/test.md",
            section_title="Advanced Topics",
            chunk_index=1,
        ),
    ]


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing"""
    return SearchResults(
        documents=[
            "This is sample content from a document.",
            "Another piece of relevant content.",
        ],
        metadata=[
            {
                "file_name": "test.md",
                "section_title": "Introduction",
                "chunk_index": 0,
            },
            {
                "file_name": "test.md",
                "section_title": "Advanced Topics",
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
        metadata=[{"file_name": "test.md", "section_title": "Introduction"}],
        distances=[0.1],
    )
    mock.get_existing_filenames.return_value = ["test.md", "other.md"]
    mock.get_document_count.return_value = 2
    return mock


@pytest.fixture
def mock_md_processor():
    """Create a mock MD processor for testing"""
    mock = Mock()
    mock.process_md_file.return_value = (
        Document(
            file_name="test.md",
            file_path="/path/to/test.md",
            title="Test Document",
            sections=["Introduction"],
        ),
        [
            DocumentChunk(
                content="Test content",
                file_name="test.md",
                file_path="/path/to/test.md",
                section_title="Introduction",
                chunk_index=0,
            )
        ],
    )
    return mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
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
        "metadatas": [[{"file_name": "test.md", "section_title": "Introduction"}]],
        "distances": [[0.1]],
    }
    return mock


# Sample test data
SAMPLE_MD_CONTENT = """# Introduction

This is a test document for the RAG system. It contains multiple sections with useful information.

## Advanced Topics

Here we cover more advanced concepts that are important for understanding the system.

### Implementation Details

The implementation uses vector embeddings to provide semantic search capabilities.
"""

SAMPLE_MD_WITH_FRONTMATTER = """---
title: "Custom Title"
author: "Test Author"
---

# Document Title

This document has frontmatter metadata.
"""
