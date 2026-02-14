from typing import List, Optional

from pydantic import BaseModel


class Document(BaseModel):
    """Represents a Markdown document"""

    file_name: str  # File name (e.g., "guide.md")
    file_path: str  # Full path to the file
    title: Optional[str] = None  # Title extracted from frontmatter or first heading
    sections: List[str] = []  # List of section titles


class DocumentChunk(BaseModel):
    """Represents a text chunk from a Markdown document"""

    content: str  # The actual text content
    file_name: str  # Source file name
    file_path: str  # Source file path
    section_title: Optional[str] = None  # Section title this chunk belongs to
    chunk_index: int  # Position of this chunk in the document
