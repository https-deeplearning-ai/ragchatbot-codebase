import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Document
from rag_system import RAGSystem


class TestRAGSystem:
    """Test cases for RAGSystem"""

    def test_init(self, test_config):
        """Test RAGSystem initialization"""
        with (
            patch("rag_system.MDProcessor") as mock_md_processor,
            patch("rag_system.VectorStore") as mock_vector_store,
        ):
            rag_system = RAGSystem("./data", "./chroma_db")

            # Verify components are initialized
            assert rag_system.folder_path == "./data"
            assert rag_system.md_processor is not None
            assert rag_system.vector_store is not None

            # Verify MDProcessor was created with correct config values
            mock_md_processor.assert_called_once_with(
                test_config.CHUNK_SIZE, test_config.CHUNK_OVERLAP
            )

            # Verify VectorStore was created with correct parameters
            mock_vector_store.assert_called_once_with(
                "./chroma_db", test_config.EMBEDDING_MODEL, test_config.MAX_RESULTS
            )

    def test_init_with_custom_path(self, test_config):
        """Test RAGSystem initialization with custom paths"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore"),
        ):
            rag_system = RAGSystem("/custom/data", "/custom/chroma")

            assert rag_system.folder_path == "/custom/data"

    def test_query_success(self, test_config, sample_search_results):
        """Test successful query"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
        ):
            mock_vector_store.return_value.search.return_value = sample_search_results

            rag_system = RAGSystem("./data")

            # Execute query
            result = rag_system.query("test query")

            # Verify vector store search was called
            mock_vector_store.return_value.search.assert_called_once_with("test query", limit=5)

            # Verify result structure
            assert "answer" in result
            assert "sources" in result
            assert "results" in result
            assert not result["answer"] == "未找到相关内容"

    def test_query_no_results(self, test_config, empty_search_results):
        """Test query with no results"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
        ):
            mock_vector_store.return_value.search.return_value = empty_search_results

            rag_system = RAGSystem("./data")

            # Execute query
            result = rag_system.query("nonexistent query")

            # Verify result indicates no content found
            assert result["answer"] == "未找到相关内容"
            assert result["sources"] == []
            assert result["results"] == []

    def test_query_with_error(self, test_config, error_search_results):
        """Test query when search fails"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
        ):
            mock_vector_store.return_value.search.return_value = error_search_results

            rag_system = RAGSystem("./data")

            # Execute query
            result = rag_system.query("test query")

            # Verify error is handled
            assert "搜索错误" in result["answer"]
            assert result["sources"] == []
            assert result["results"] == []

    def test_query_with_custom_limit(self, test_config, sample_search_results):
        """Test query with custom limit"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
        ):
            mock_vector_store.return_value.search.return_value = sample_search_results

            rag_system = RAGSystem("./data")

            # Execute query with custom limit
            result = rag_system.query("test query", limit=3)

            # Verify custom limit was passed to search
            mock_vector_store.return_value.search.assert_called_once_with("test query", limit=3)

    def test_load_md_folder_success(self, test_config, sample_document_chunks, temp_dir):
        """Test successful loading of MD folder"""
        with (
            patch("rag_system.MDProcessor") as mock_md_processor_class,
            patch("rag_system.VectorStore") as mock_vector_store_class,
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
        ):
            # Setup mocks
            mock_exists.return_value = True
            mock_listdir.return_value = ["test1.md", "test2.md", "not_md.txt"]

            # Create mock instances
            mock_md_processor = Mock()
            mock_vector_store = Mock()
            mock_md_processor_class.return_value = mock_md_processor
            mock_vector_store_class.return_value = mock_vector_store

            # Mock document processing
            mock_document1 = Document(
                file_name="test1.md",
                file_path=os.path.join(temp_dir, "test1.md"),
                title="Test Doc 1",
                sections=["Introduction"],
            )
            mock_document2 = Document(
                file_name="test2.md",
                file_path=os.path.join(temp_dir, "test2.md"),
                title="Test Doc 2",
                sections=["Advanced"],
            )

            mock_md_processor.process_md_file.side_effect = [
                (mock_document1, sample_document_chunks[:1]),  # test1.md
                (mock_document2, sample_document_chunks[1:]),  # test2.md
            ]

            mock_vector_store.get_existing_filenames.return_value = []

            rag_system = RAGSystem("./data")

            # Execute
            total_docs, total_chunks = rag_system.load_md_folder(temp_dir)

            # Assert
            assert total_docs == 2  # Only .md files processed
            assert total_chunks == 2

            # Verify MD processor was called for each .md file
            assert mock_md_processor.process_md_file.call_count == 2

            # Verify chunks were added to vector store
            mock_vector_store.add_document_content.assert_called()

    def test_load_md_folder_skip_existing(self, test_config, temp_dir):
        """Test that existing files are skipped"""
        with (
            patch("rag_system.MDProcessor") as mock_md_processor,
            patch("rag_system.VectorStore") as mock_vector_store,
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
        ):
            mock_exists.return_value = True
            mock_listdir.return_value = ["existing.md", "new.md"]

            # Mock existing filenames
            mock_vector_store.return_value.get_existing_filenames.return_value = ["existing.md"]

            rag_system = RAGSystem("./data")

            # Execute
            total_docs, total_chunks = rag_system.load_md_folder(temp_dir)

            # Assert only new file was processed
            assert total_docs == 1
            assert total_chunks == 0  # No chunks from new file in this test

            # Verify only new.md was processed
            mock_md_processor.return_value.process_md_file.assert_called_once()

    def test_load_md_folder_nonexistent(self, test_config):
        """Test loading from nonexistent folder"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore"),
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.return_value = False

            rag_system = RAGSystem("./data")

            # Execute
            total_docs, total_chunks = rag_system.load_md_folder("/nonexistent")

            # Assert
            assert total_docs == 0
            assert total_chunks == 0

    def test_load_md_folder_with_clear_existing(self, test_config, temp_dir):
        """Test loading with clear_existing=True"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore") as mock_vector_store,
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
        ):
            mock_exists.return_value = True
            mock_listdir.return_value = []

            rag_system = RAGSystem("./data")

            # Execute with clear_existing=True
            rag_system.load_md_folder(temp_dir, clear_existing=True)

            # Verify data was cleared
            mock_vector_store.return_value.clear_all_data.assert_called_once()

    def test_load_md_folder_processing_error(self, test_config, temp_dir):
        """Test handling of processing errors"""
        with (
            patch("rag_system.MDProcessor") as mock_md_processor,
            patch("rag_system.VectorStore") as mock_vector_store,
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
        ):
            mock_exists.return_value = True
            mock_listdir.return_value = ["bad.md"]

            # Mock processing to raise exception
            mock_md_processor.return_value.process_md_file.side_effect = Exception("Processing failed")

            rag_system = RAGSystem("./data")

            # Execute
            total_docs, total_chunks = rag_system.load_md_folder(temp_dir)

            # Assert error was handled gracefully
            assert total_docs == 0
            assert total_chunks == 0

    def test_get_document_stats(self, mock_vector_store):
        """Test getting document statistics"""
        rag_system = RAGSystem("./data")

        # Mock the vector store methods
        rag_system.vector_store = mock_vector_store

        # Execute
        stats = rag_system.get_document_stats()

        # Assert
        assert "total_documents" in stats
        assert "file_names" in stats
        assert stats["total_documents"] == 2
        assert "test.md" in stats["file_names"]
        assert "other.md" in stats["file_names"]

    def test_format_results(self, sample_search_results):
        """Test result formatting"""
        rag_system = RAGSystem("./data")

        # Execute formatting
        formatted = rag_system._format_results(sample_search_results)

        # Assert formatting includes file and section info
        assert "test.md" in formatted
        assert "Introduction" in formatted
        assert "---" in formatted  # Section separator

    def test_extract_sources(self, sample_search_results):
        """Test source extraction"""
        rag_system = RAGSystem("./data")

        # Execute source extraction
        sources = rag_system._extract_sources(sample_search_results)

        # Assert sources are properly formatted
        assert len(sources) == 2
        assert "test.md" in sources[0]
        assert "Introduction" in sources[0]

    def test_auto_load_on_init(self, test_config):
        """Test that MD folder is automatically loaded on initialization"""
        with (
            patch("rag_system.MDProcessor"),
            patch("rag_system.VectorStore"),
            patch.object(RAGSystem, "load_md_folder") as mock_load,
        ):
            mock_load.return_value = (3, 15)

            rag_system = RAGSystem("./data")

            # Verify load_md_folder was called during initialization
            mock_load.assert_called_once_with("./data", clear_existing=False)
