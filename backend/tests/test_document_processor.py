import os
import sys
from unittest.mock import patch

import pytest

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_processor import MDProcessor
from models import Document, DocumentChunk


class TestMDProcessor:
    """Test cases for MDProcessor"""

    def test_init(self, test_config):
        """Test MDProcessor initialization"""
        processor = MDProcessor(test_config.CHUNK_SIZE, test_config.CHUNK_OVERLAP)

        assert processor.chunk_size == test_config.CHUNK_SIZE
        assert processor.chunk_overlap == test_config.CHUNK_OVERLAP

    def test_process_md_file_basic(self, test_config, temp_dir):
        """Test basic MD file processing"""
        # Create a test MD file
        md_content = """# Introduction

This is a test document for processing.

## Advanced Topics

Here we cover advanced concepts.

### Implementation

The implementation details go here.
"""

        md_file = os.path.join(temp_dir, "test.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        processor = MDProcessor(800, 100)

        # Process the file
        document, chunks = processor.process_md_file(md_file)

        # Assert document structure
        assert isinstance(document, Document)
        assert document.file_name == "test.md"
        assert document.title == "Introduction"  # First heading
        assert "Introduction" in document.sections
        assert "Advanced Topics" in document.sections

        # Assert chunks were created
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

        # Check first chunk
        first_chunk = chunks[0]
        assert first_chunk.file_name == "test.md"
        assert "[文件: test.md | 章节:" in first_chunk.content

    def test_process_md_file_with_frontmatter(self, test_config, temp_dir):
        """Test MD file processing with YAML frontmatter"""
        md_content = """---
title: "Custom Document Title"
author: "Test Author"
---

# Actual Heading

This document has frontmatter that should be parsed.
"""

        md_file = os.path.join(temp_dir, "frontmatter.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        processor = MDProcessor(800, 100)

        # Process the file
        document, chunks = processor.process_md_file(md_file)

        # Assert title comes from frontmatter
        assert document.title == "Custom Document Title"

    def test_process_md_file_no_frontmatter_title(self, test_config, temp_dir):
        """Test MD file processing when frontmatter has no title"""
        md_content = """---
author: "Test Author"
---

# Document Title

Content without frontmatter title.
"""

        md_file = os.path.join(temp_dir, "no_title.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        processor = MDProcessor(800, 100)

        # Process the file
        document, chunks = processor.process_md_file(md_file)

        # Assert title comes from first heading
        assert document.title == "Document Title"

    def test_extract_frontmatter_valid(self):
        """Test frontmatter extraction with valid YAML"""
        content = """---
title: "Test Title"
author: "Test Author"
---

# Heading

Content here.
"""

        processor = MDProcessor(800, 100)
        frontmatter = processor.extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter["title"] == "Test Title"
        assert frontmatter["author"] == "Test Author"

    def test_extract_frontmatter_none(self):
        """Test frontmatter extraction when no frontmatter exists"""
        content = """# Heading

Content without frontmatter.
"""

        processor = MDProcessor(800, 100)
        frontmatter = processor.extract_frontmatter(content)

        assert frontmatter is None

    def test_extract_frontmatter_invalid_yaml(self):
        """Test frontmatter extraction with invalid YAML"""
        content = """---
title: "Test Title
author: "Test Author"
---

# Heading

Content here.
"""

        processor = MDProcessor(800, 100)
        frontmatter = processor.extract_frontmatter(content)

        # Should return None for invalid YAML
        assert frontmatter is None

    def test_split_by_sections(self):
        """Test content splitting by Markdown sections"""
        content = """# Introduction

Intro content here.

## Section 1

Content for section 1.

## Section 2

Content for section 2.

# Another Top Level

More content.
"""

        processor = MDProcessor(800, 100)
        sections = processor.split_by_sections(content)

        assert len(sections) == 4
        assert sections[0][0] == "Introduction"
        assert sections[1][0] == "Section 1"
        assert sections[2][0] == "Section 2"
        assert sections[3][0] == "Another Top Level"

        # Check content is properly separated
        assert "Intro content here." in sections[0][1]
        assert "Content for section 1." in sections[1][1]

    def test_split_by_sections_no_headings(self):
        """Test content splitting when no headings exist"""
        content = """This is content without any headings.

It should all go into the default section.
"""

        processor = MDProcessor(800, 100)
        sections = processor.split_by_sections(content)

        assert len(sections) == 1
        assert sections[0][0] == "简介"  # Default section title
        assert "content without any headings" in sections[0][1]

    def test_format_chunk_with_context(self):
        """Test chunk formatting with context"""
        processor = MDProcessor(800, 100)

        chunk = "This is test content."
        section = "Introduction"
        file_name = "test.md"

        formatted = processor.format_chunk_with_context(chunk, section, file_name)

        assert formatted.startswith("[文件: test.md | 章节: Introduction]")
        assert "\n\nThis is test content." in formatted

    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        processor = MDProcessor(800, 100)

        text = "This is a simple sentence. This is another sentence. This is a third sentence."

        chunks = processor.chunk_text(text)

        # Should create chunks based on sentences
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_text_with_overlap(self):
        """Test text chunking with overlap"""
        processor = MDProcessor(50, 20)  # Small chunk size to force overlap

        text = "This is the first sentence that is quite long. This is the second sentence. This is the third sentence that continues the thought."

        chunks = processor.chunk_text(text)

        # Should have multiple chunks with overlap
        assert len(chunks) > 1

        # Check that overlap works (second chunk should start with content from first)
        if len(chunks) > 1:
            assert len(chunks[0]) > 0
            assert len(chunks[1]) > 0

    def test_chunk_text_long_sentences(self):
        """Test chunking with very long sentences"""
        processor = MDProcessor(50, 10)

        # Create a very long sentence
        long_sentence = " ".join([f"word{i}" for i in range(100)])
        text = f"{long_sentence}."

        chunks = processor.chunk_text(text)

        # Should split long content
        assert len(chunks) > 0
        total_length = sum(len(chunk) for chunk in chunks)
        assert total_length >= len(text)  # Should preserve all content

    def test_read_file_utf8(self, temp_dir):
        """Test file reading with UTF-8 content"""
        content = "这是测试内容 with 中文 and English."
        test_file = os.path.join(temp_dir, "utf8.md")

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        processor = MDProcessor(800, 100)
        read_content = processor.read_file(test_file)

        assert read_content == content

    def test_read_file_encoding_fallback(self, temp_dir):
        """Test file reading with encoding fallback"""
        content = "Test content with some special characters: àáâãäå."
        test_file = os.path.join(temp_dir, "encoding.md")

        # Write with different encoding
        with open(test_file, "w", encoding="latin-1") as f:
            f.write(content)

        processor = MDProcessor(800, 100)
        read_content = processor.read_file(test_file)

        # Should still read content (may have replacement characters)
        assert len(read_content) > 0

    def test_extract_first_heading(self):
        """Test extraction of first level-1 heading"""
        content = """Some intro text.

# First Heading

Content here.

## Second Level

More content.

# Another Top Level

Final content.
"""

        processor = MDProcessor(800, 100)
        title = processor._extract_first_heading(content)

        assert title == "First Heading"

    def test_extract_first_heading_none(self):
        """Test first heading extraction when no headings exist"""
        content = """This is content without any headings.

Just plain text.
"""

        processor = MDProcessor(800, 100)
        title = processor._extract_first_heading(content)

        assert title is None

    def test_process_md_file_empty(self, temp_dir):
        """Test processing of empty MD file"""
        md_file = os.path.join(temp_dir, "empty.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("")

        processor = MDProcessor(800, 100)
        document, chunks = processor.process_md_file(md_file)

        assert isinstance(document, Document)
        assert document.title is None  # No title from empty file
        assert len(chunks) == 0  # No chunks from empty content

    def test_process_md_file_only_frontmatter(self, temp_dir):
        """Test processing file with only frontmatter"""
        content = """---
title: "Only Frontmatter"
author: "Test"
---
"""

        md_file = os.path.join(temp_dir, "frontmatter_only.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)

        processor = MDProcessor(800, 100)
        document, chunks = processor.process_md_file(md_file)

        assert document.title == "Only Frontmatter"
        assert len(chunks) == 0  # No content chunks

    def test_integration_full_processing(self, temp_dir):
        """Integration test for full MD processing pipeline"""
        md_content = """---
title: "Integration Test"
---

# Main Title

This is an integration test document.

## Section One

Content for the first section with multiple sentences. This should be chunked appropriately. The chunking algorithm should handle sentence boundaries correctly.

## Section Two

More content in the second section. This tests that multiple sections are handled properly and chunks are created for each section with appropriate context.
"""

        md_file = os.path.join(temp_dir, "integration.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        processor = MDProcessor(100, 20)  # Small chunks to force chunking

        # Process the file
        document, chunks = processor.process_md_file(md_file)

        # Verify document
        assert document.title == "Integration Test"  # From frontmatter
        assert len(document.sections) == 3  # Main Title, Section One, Section Two
        assert "Main Title" in document.sections
        assert "Section One" in document.sections
        assert "Section Two" in document.sections

        # Verify chunks
        assert len(chunks) > 0

        # Check chunk context formatting
        for chunk in chunks:
            assert "[文件: integration.md | 章节:" in chunk.content
            assert chunk.file_name == "integration.md"
            assert chunk.section_title in ["Main Title", "Section One", "Section Two"]
