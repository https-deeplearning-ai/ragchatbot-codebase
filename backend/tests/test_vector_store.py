import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DocumentChunk
from vector_store import SearchResults, VectorStore


class TestVectorStore:
    """Test cases for VectorStore"""

    def test_init(self, test_config):
        """Test VectorStore initialization"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Verify ChromaDB client was created
            mock_chromadb.PersistentClient.assert_called_once_with(
                path=test_config.CHROMA_PATH, settings=mock_chromadb.PersistentClient.call_args[1]["settings"]
            )

            # Verify collection was created
            mock_client.get_or_create_collection.assert_called_once()

    def test_search_success(self, test_config, mock_chroma_collection):
        """Test successful search"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_chroma_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Execute search
            result = vector_store.search("test query")

            # Verify ChromaDB query was called correctly
            mock_chroma_collection.query.assert_called_once_with(
                query_texts=["test query"],
                n_results=5,
                where=None,
            )

            # Verify results
            assert not result.is_empty()
            assert len(result.documents) == 1
            assert result.documents[0] == "Sample document"

    def test_search_with_file_filter(self, test_config, mock_chroma_collection):
        """Test search with file name filter"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_chroma_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Execute search with file filter
            result = vector_store.search("test query", file_name="test.md")

            # Verify search was called with file filter
            mock_chroma_collection.query.assert_called_once_with(
                query_texts=["test query"], n_results=5, where={"file_name": "test.md"}
            )

    def test_search_with_section_filter(self, test_config, mock_chroma_collection):
        """Test search with section title filter"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_chroma_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Execute search with section filter
            result = vector_store.search("test query", section_title="Introduction")

            # Verify search was called with section filter
            mock_chroma_collection.query.assert_called_once_with(
                query_texts=["test query"], n_results=5, where={"section_title": "Introduction"}
            )

    def test_search_with_both_filters(self, test_config, mock_chroma_collection):
        """Test search with both file and section filters"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_chroma_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Execute search with both filters
            result = vector_store.search(
                "test query", file_name="test.md", section_title="Introduction"
            )

            # Verify search was called with combined filter
            expected_filter = {
                "$and": [{"file_name": "test.md"}, {"section_title": "Introduction"}]
            }
            mock_chroma_collection.query.assert_called_once_with(
                query_texts=["test query"], n_results=5, where=expected_filter
            )

    def test_search_database_error(self, test_config):
        """Test search when database query fails"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client

            # Mock collection that raises exception
            mock_collection = Mock()
            mock_collection.query.side_effect = Exception("Database connection failed")
            mock_client.get_or_create_collection.return_value = mock_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Execute search that will fail
            result = vector_store.search("test query")

            # Should return error result
            assert result.error == "Search error: Database connection failed"
            assert result.is_empty()

    def test_add_document_content(self, test_config, sample_document_chunks):
        """Test adding document content chunks to vector store"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client

            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Add document content
            vector_store.add_document_content(sample_document_chunks)

            # Verify collection add was called
            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args

            # Check that correct data was passed
            assert len(call_args[1]["documents"]) == len(sample_document_chunks)
            assert len(call_args[1]["metadatas"]) == len(sample_document_chunks)
            assert len(call_args[1]["ids"]) == len(sample_document_chunks)

            # Check first chunk data
            assert call_args[1]["documents"][0] == sample_document_chunks[0].content
            assert call_args[1]["metadatas"][0]["file_name"] == sample_document_chunks[0].file_name
            assert call_args[1]["metadatas"][0]["section_title"] == sample_document_chunks[0].section_title

    def test_get_existing_filenames(self, test_config):
        """Test getting existing file names"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client

            mock_collection = Mock()
            mock_collection.get.return_value = {
                "metadatas": [
                    {"file_name": "test1.md"},
                    {"file_name": "test2.md"},
                    {"file_name": "test1.md"},  # Duplicate
                ]
            }
            mock_client.get_or_create_collection.return_value = mock_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Get existing filenames
            filenames = vector_store.get_existing_filenames()

            # Should return deduplicated list
            assert set(filenames) == {"test1.md", "test2.md"}

    def test_get_document_count(self, mock_vector_store):
        """Test getting document count"""
        count = mock_vector_store.get_document_count()
        assert count == 2  # Based on mock setup

    def test_clear_all_data(self, test_config):
        """Test clearing all data"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client

            # Mock collections
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.delete_collection = Mock()

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Clear all data
            vector_store.clear_all_data()

            # Verify collection was deleted and recreated
            mock_client.delete_collection.assert_called_once_with("document_content")
            # get_or_create_collection should be called twice (once in init, once in clear)
            assert mock_client.get_or_create_collection.call_count >= 2

    def test_build_filter_no_filters(self, test_config):
        """Test filter building with no filters"""
        with patch("vector_store.chromadb"):
            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            filter_dict = vector_store._build_filter(None, None)
            assert filter_dict is None

    def test_build_filter_file_only(self, test_config):
        """Test filter building with file filter only"""
        with patch("vector_store.chromadb"):
            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            filter_dict = vector_store._build_filter("test.md", None)
            assert filter_dict == {"file_name": "test.md"}

    def test_build_filter_section_only(self, test_config):
        """Test filter building with section filter only"""
        with patch("vector_store.chromadb"):
            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            filter_dict = vector_store._build_filter(None, "Introduction")
            assert filter_dict == {"section_title": "Introduction"}

    def test_build_filter_both(self, test_config):
        """Test filter building with both filters"""
        with patch("vector_store.chromadb"):
            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            filter_dict = vector_store._build_filter("test.md", "Introduction")
            expected = {"$and": [{"file_name": "test.md"}, {"section_title": "Introduction"}]}
            assert filter_dict == expected

    def test_search_results_from_chroma(self):
        """Test SearchResults.from_chroma method"""
        chroma_results = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"meta1": "value1"}, {"meta2": "value2"}]],
            "distances": [[0.1, 0.2]],
        }

        results = SearchResults.from_chroma(chroma_results)

        assert results.documents == ["doc1", "doc2"]
        assert results.metadata == [{"meta1": "value1"}, {"meta2": "value2"}]
        assert results.distances == [0.1, 0.2]
        assert results.error is None
        assert not results.is_empty()

    def test_search_results_empty(self):
        """Test SearchResults.empty method"""
        results = SearchResults.empty("Test error message")

        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []
        assert results.error == "Test error message"
        assert results.is_empty()

    def test_search_with_limit(self, test_config, mock_chroma_collection):
        """Test search with custom limit"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_chroma_collection

            vector_store = VectorStore(
                chroma_path=test_config.CHROMA_PATH,
                embedding_model=test_config.EMBEDDING_MODEL,
                max_results=test_config.MAX_RESULTS,
            )

            # Execute search with custom limit
            result = vector_store.search("test query", limit=3)

            # Verify ChromaDB query was called with custom limit
            mock_chroma_collection.query.assert_called_once_with(
                query_texts=["test query"],
                n_results=3,  # Custom limit
                where=None,
            )
