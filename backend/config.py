import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Configuration settings for the RAG system"""

    # Embedding model settings
    EMBEDDING_MODEL: str = r"C:\Users\PC\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\all-MiniLM-L6-v2"

    # Document processing settings
    CHUNK_SIZE: int = 800  # Size of text chunks for vector storage
    CHUNK_OVERLAP: int = 100  # Characters to overlap between chunks
    MAX_RESULTS: int = 3  # Maximum search results to return

    # Database paths
    CHROMA_PATH: str = "./chroma_db"  # ChromaDB storage location


config = Config()
