import os
import re
from typing import Dict, List, Optional, Tuple

from models import Document, DocumentChunk


class MDProcessor:
    """Processes Markdown documents and extracts structured information"""

    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_md_file(self, file_path: str) -> Tuple[Document, List[DocumentChunk]]:
        """
        Process a Markdown file and extract document structure and chunks.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Tuple of (Document object, list of DocumentChunk objects)
        """
        # Read file content
        content = self.read_file(file_path)
        file_name = os.path.basename(file_path)

        # Extract frontmatter (optional)
        frontmatter = self.extract_frontmatter(content)
        if frontmatter:
            # Remove frontmatter from content
            content = re.sub(
                r"^---\n.*?\n---\n",
                "",
                content,
                flags=re.DOTALL,
                count=1,
            )

        # Extract title
        title = frontmatter.get("title") if frontmatter else None
        if not title:
            title = self._extract_first_heading(content)

        # Split content by sections
        sections = self.split_by_sections(content)

        # Create document object
        document = Document(
            file_name=file_name,
            file_path=file_path,
            title=title,
            sections=[section[0] for section in sections],
        )

        # Create chunks
        chunks = []
        chunk_index = 0

        for section_title, section_content in sections:
            # Skip empty sections
            if not section_content.strip():
                continue

            # Chunk the section content
            text_chunks = self.chunk_text(section_content)

            for chunk in text_chunks:
                formatted_chunk = self.format_chunk_with_context(
                    chunk, section_title, file_name
                )

                doc_chunk = DocumentChunk(
                    content=formatted_chunk,
                    file_name=file_name,
                    file_path=file_path,
                    section_title=section_title,
                    chunk_index=chunk_index,
                )
                chunks.append(doc_chunk)
                chunk_index += 1

        return document, chunks

    def extract_frontmatter(self, content: str) -> Optional[Dict[str, str]]:
        """
        Extract YAML frontmatter from Markdown content.

        Example:
            ---
            title: "Document Title"
            author: "Author Name"
            ---
        """
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return None

        try:
            import yaml

            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter if isinstance(frontmatter, dict) else None
        except Exception:
            return None

    def split_by_sections(self, content: str) -> List[Tuple[str, str]]:
        """
        Split content by Markdown headings.

        Returns:
            List of tuples: [(section_title, section_content), ...]
        """
        sections = []
        lines = content.split("\n")

        current_title = "简介"  # Default section title
        current_content = []

        for line in lines:
            # Detect headings (#, ##, ###, etc.)
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Save previous section if it has content
                if current_content:
                    section_text = "\n".join(current_content).strip()
                    if section_text:
                        sections.append((current_title, section_text))

                # Start new section
                current_title = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save the last section
        if current_content:
            section_text = "\n".join(current_content).strip()
            if section_text:
                sections.append((current_title, section_text))

        return sections

    def format_chunk_with_context(
        self, chunk: str, section: str, file_name: str
    ) -> str:
        """Add context information to a chunk."""
        return f"[文件: {file_name} | 章节: {section}]\n\n{chunk}"

    def chunk_text(self, text: str) -> List[str]:
        """Split text into sentence-based chunks with overlap."""

        # Clean up the text
        text = re.sub(r"\s+", " ", text.strip())

        # Better sentence splitting that handles abbreviations
        # This regex looks for periods followed by whitespace and capital letters
        # but ignores common abbreviations
        sentence_endings = re.compile(
            r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])"
        )
        sentences = sentence_endings.split(text)

        # Clean sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        i = 0

        while i < len(sentences):
            current_chunk = []
            current_size = 0

            # Build chunk starting from sentence i
            for j in range(i, len(sentences)):
                sentence = sentences[j]

                # Calculate size with space
                space_size = 1 if current_chunk else 0
                total_addition = len(sentence) + space_size

                # Check if adding this sentence would exceed chunk size
                if current_size + total_addition > self.chunk_size and current_chunk:
                    break

                current_chunk.append(sentence)
                current_size += total_addition

            # Add chunk if we have content
            if current_chunk:
                chunks.append(" ".join(current_chunk))

                # Calculate overlap for next chunk
                if self.chunk_overlap > 0:
                    # Find how many sentences to overlap
                    overlap_size = 0
                    overlap_sentences = 0

                    # Count backwards from end of current chunk
                    for k in range(len(current_chunk) - 1, -1, -1):
                        sentence_len = len(current_chunk[k]) + (
                            1 if k < len(current_chunk) - 1 else 0
                        )
                        if overlap_size + sentence_len <= self.chunk_overlap:
                            overlap_size += sentence_len
                            overlap_sentences += 1
                        else:
                            break

                    # Move start position considering overlap
                    next_start = i + len(current_chunk) - overlap_sentences
                    i = max(next_start, i + 1)
                else:
                    # No overlap - move to next sentence after current chunk
                    i += len(current_chunk)
            else:
                # No sentences fit, move to next
                i += 1

        return chunks

    def read_file(self, file_path: str) -> str:
        """Read content from file with UTF-8 encoding."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try with error handling
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()

    def _extract_first_heading(self, content: str) -> Optional[str]:
        """Extract the first level-1 heading as document title."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else None
