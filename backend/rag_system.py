import os
from typing import Any, Dict, List, Tuple

from config import config
from document_processor import MDProcessor
from models import Document, DocumentChunk
from vector_store import SearchResults, VectorStore


class RAGSystem:
    """General-purpose Markdown RAG system"""

    def __init__(self, folder_path: str, chroma_path: str = "./chroma_db"):
        """
        Initialize RAG system and load MD files.

        Args:
            folder_path: Directory containing MD files
            chroma_path: ChromaDB storage path
        """
        self.folder_path = folder_path

        # Initialize core components
        self.md_processor = MDProcessor(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        self.vector_store = VectorStore(
            chroma_path, config.EMBEDDING_MODEL, config.MAX_RESULTS
        )

        # Auto-load MD files
        self.load_md_folder(folder_path, clear_existing=False)

    def query(self, query_text: str, limit: int = 5) -> Dict[str, Any]:
        """
        Query MD document content.

        Args:
            query_text: Query text
            limit: Number of results to return

        Returns:
            {
                "answer": str,              # Formatted query result
                "sources": List[str],       # Source information list
                "results": List[Dict]       # Raw search results
            }
        """
        # Execute vector search
        search_results = self.vector_store.search(query_text, limit=limit)

        if search_results.error:
            return {
                "answer": f"搜索错误: {search_results.error}",
                "sources": [],
                "results": [],
            }

        if search_results.is_empty():
            return {
                "answer": "未找到相关内容",
                "sources": [],
                "results": [],
            }

        # Format results
        answer = self._format_results(search_results)
        sources = self._extract_sources(search_results)

        # Include raw results
        results = [
            {
                "content": doc,
                "metadata": meta,
                "distance": dist,
            }
            for doc, meta, dist in zip(
                search_results.documents,
                search_results.metadata,
                search_results.distances,
            )
        ]

        return {
            "answer": answer,
            "sources": sources,
            "results": results,
        }

    def load_md_folder(
        self, folder_path: str, clear_existing: bool = False
    ) -> Tuple[int, int]:
        """
        Load all MD files from a folder.

        Args:
            folder_path: Folder path
            clear_existing: Whether to clear existing data

        Returns:
            (number of documents, number of chunks)
        """
        total_docs = 0
        total_chunks = 0

        if clear_existing:
            print("清除现有数据...")
            self.vector_store.clear_all_data()

        if not os.path.exists(folder_path):
            print(f"文件夹不存在: {folder_path}")
            return 0, 0

        # Get already processed file names
        existing_files = set(self.vector_store.get_existing_filenames())

        # Iterate through MD files
        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith(".md"):
                continue

            file_path = os.path.join(folder_path, file_name)

            # Skip already processed files
            if file_name in existing_files:
                print(f"文件已存在，跳过: {file_name}")
                continue

            try:
                # Process MD file
                document, chunks = self.md_processor.process_md_file(file_path)

                # Add to vector store
                self.vector_store.add_document_content(chunks)

                total_docs += 1
                total_chunks += len(chunks)
                print(f"已加载: {file_name} ({len(chunks)} 个分块)")

            except Exception as e:
                print(f"处理文件失败 {file_name}: {e}")

        return total_docs, total_chunks

    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        return {
            "total_documents": self.vector_store.get_document_count(),
            "file_names": self.vector_store.get_existing_filenames(),
        }

    def _format_results(self, results: SearchResults) -> str:
        """Format search results into readable text."""
        formatted = []
        for doc, meta in zip(results.documents, results.metadata):
            file_name = meta.get("file_name", "unknown")
            section = meta.get("section_title")

            header = f"## 来源: {file_name}"
            if section:
                header += f" > {section}"

            formatted.append(f"{header}\n\n{doc}")

        return "\n\n---\n\n".join(formatted)

    def _extract_sources(self, results: SearchResults) -> List[str]:
        """Extract source information."""
        sources = []
        for meta in results.metadata:
            file_name = meta.get("file_name", "unknown")
            section = meta.get("section_title")

            source = file_name
            if section:
                source += f" > {section}"
            sources.append(source)

        return sources
