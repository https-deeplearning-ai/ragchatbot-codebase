from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from models import DocumentChunk


@dataclass
class SearchResults:
    """Container for search results with metadata"""

    documents: List[str]
    metadata: List[Dict[str, Any]]
    distances: List[float]
    error: Optional[str] = None

    @classmethod
    def from_chroma(cls, chroma_results: Dict) -> "SearchResults":
        """Create SearchResults from ChromaDB query results"""
        return cls(
            documents=(
                chroma_results["documents"][0] if chroma_results["documents"] else []
            ),
            metadata=(
                chroma_results["metadatas"][0] if chroma_results["metadatas"] else []
            ),
            distances=(
                chroma_results["distances"][0] if chroma_results["distances"] else []
            ),
        )

    @classmethod
    def empty(cls, error_msg: str = "No results found") -> "SearchResults":
        """Create empty results with error message"""
        return cls(documents=[], metadata=[], distances=[], error=error_msg)

    def is_empty(self) -> bool:
        """Check if results are empty"""
        return len(self.documents) == 0


class VectorStore:
    """Vector storage using ChromaDB for document content"""

    def __init__(self, chroma_path: str, embedding_model: str, max_results: int = 5):
        self.max_results = max_results
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=chroma_path, settings=Settings(anonymized_telemetry=False)
        )

        # Set up sentence transformer embedding function
        self.embedding_function = (
            chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
        )

        # Create single collection for document content
        self.document_content = self._create_collection("document_content")

    def _create_collection(self, name: str):
        """Create or get a ChromaDB collection"""
        return self.client.get_or_create_collection(
            name=name, embedding_function=self.embedding_function
        )

    def search(
        self,
        query: str,
        file_name: Optional[str] = None,
        section_title: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> SearchResults:
        """
        Search document content with optional filters.

        Args:
            query: Search query text
            file_name: Optional file name to filter by
            section_title: Optional section title to filter by
            limit: Maximum results to return

        Returns:
            SearchResults object with documents and metadata
        """
        # Build filter from search parameters
        filter_dict = self._build_filter(file_name, section_title)

        # Use provided limit or fall back to configured max_results
        search_limit = limit if limit is not None else self.max_results

        try:
            results = self.document_content.query(
                query_texts=[query], n_results=search_limit, where=filter_dict
            )
            return SearchResults.from_chroma(results)
        except Exception as e:
            return SearchResults.empty(f"Search error: {str(e)}")

    def _build_filter(
        self, file_name: Optional[str], section_title: Optional[str]
    ) -> Optional[Dict]:
        """Build ChromaDB filter from search parameters"""
        if not file_name and not section_title:
            return None

        # Handle different filter combinations
        if file_name and section_title:
            return {
                "$and": [{"file_name": file_name}, {"section_title": section_title}]
            }

        if file_name:
            return {"file_name": file_name}

        return {"section_title": section_title}

    def add_document_content(self, chunks: List[DocumentChunk]):
        """Add document content chunks to the vector store"""
        if not chunks:
            return

        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "file_name": chunk.file_name,
                "file_path": chunk.file_path,
                "section_title": chunk.section_title,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]
        # Use file name with chunk index for unique IDs
        ids = [f"{chunk.file_name}_{chunk.chunk_index}" for chunk in chunks]

        self.document_content.add(documents=documents, metadatas=metadatas, ids=ids)

    def get_existing_filenames(self) -> List[str]:
        """Get all existing file names from the vector store"""
        try:
            results = self.document_content.get()
            if results and "metadatas" in results:
                # Deduplicate file names
                filenames = set(
                    meta.get("file_name")
                    for meta in results["metadatas"]
                    if meta.get("file_name")
                )
                return list(filenames)
            return []
        except Exception as e:
            print(f"Error getting existing file names: {e}")
            return []

    def get_document_count(self) -> int:
        """Get the total number of documents in the vector store"""
        return len(self.get_existing_filenames())

    def clear_all_data(self):
        """Clear all data from the collection"""
        try:
            self.client.delete_collection("document_content")
            # Recreate collection
            self.document_content = self._create_collection("document_content")
        except Exception as e:
            print(f"Error clearing data: {e}")
