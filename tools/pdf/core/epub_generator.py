#!/usr/bin/env python3
"""
EPUB Generator for E-Book Export
=================================

Provides professional EPUB generation from Markdown with:
- Metadata (title, author, ISBN, publisher)
- Table of contents
- Cover image support
- Chapter organization
- Styling with embedded CSS
- Pandoc-based conversion

Usage:
    from tools.pdf.core import EPUBGenerator
    
    generator = EPUBGenerator()
    generator.markdown_to_epub(
        'book.md',
        'book.epub',
        title="My Book",
        author="Jane Doe",
        cover_image="cover.png"
    )

CLI:
    python -m tools.pdf.cli.main book.md book.epub --format epub
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import json
import tempfile
import shutil

logger = logging.getLogger(__name__)


@dataclass
class EPUBMetadata:
    """
    Metadata for EPUB generation.
    
    Attributes:
        title: Book title
        author: Author name(s)
        publisher: Publisher name
        date: Publication date
        language: Language code (e.g., 'en', 'en-US')
        isbn: ISBN number
        description: Book description
        subject: Subject/category
        rights: Copyright/license information
        identifier: Unique identifier (defaults to ISBN or generated)
    """
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    language: str = "en"
    isbn: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    rights: Optional[str] = None
    identifier: Optional[str] = None
    
    def to_pandoc_metadata(self) -> Dict[str, Any]:
        """
        Convert to Pandoc metadata format.
        
        Returns:
            Dictionary of metadata for Pandoc
        """
        metadata = {}
        
        if self.title:
            metadata['title'] = self.title
        if self.author:
            # Support multiple authors
            if isinstance(self.author, str):
                metadata['author'] = [self.author]
            else:
                metadata['author'] = self.author
        if self.publisher:
            metadata['publisher'] = self.publisher
        if self.date:
            metadata['date'] = self.date
        if self.language:
            metadata['lang'] = self.language
        if self.isbn:
            metadata['isbn'] = self.isbn
        if self.description:
            metadata['description'] = self.description
        if self.subject:
            metadata['subject'] = self.subject
        if self.rights:
            metadata['rights'] = self.rights
        if self.identifier:
            metadata['identifier'] = self.identifier
        elif self.isbn:
            metadata['identifier'] = f"isbn:{self.isbn}"
        
        return metadata


@dataclass
class EPUBGenerationStats:
    """
    Statistics from EPUB generation.
    
    Attributes:
        input_file: Input markdown file
        output_file: Output EPUB file
        chapters: Number of chapters detected
        images: Number of images embedded
        file_size: Output file size in bytes
        generation_time: Time taken in seconds
        metadata: Metadata used
    """
    input_file: str
    output_file: str
    chapters: int = 0
    images: int = 0
    file_size: int = 0
    generation_time: float = 0.0
    metadata: Optional[EPUBMetadata] = None
    
    def report(self) -> str:
        """
        Generate human-readable statistics report.
        
        Returns:
            Formatted statistics string
        """
        lines = [
            "\n[INFO] EPUB Generation Report",
            f"       Input: {self.input_file}",
            f"       Output: {self.output_file}",
            f"       Chapters: {self.chapters}",
            f"       Images: {self.images}",
            f"       File Size: {self.file_size / 1024:.1f} KB",
            f"       Generation Time: {self.generation_time:.2f}s",
        ]
        
        if self.metadata and self.metadata.title:
            lines.append(f"       Title: {self.metadata.title}")
        if self.metadata and self.metadata.author:
            lines.append(f"       Author: {self.metadata.author}")
        
        return "\n".join(lines)


class EPUBGenerator:
    """
    EPUB generator for e-book export.
    
    Converts Markdown to EPUB using Pandoc with support for:
    - Metadata (title, author, publisher, ISBN, etc.)
    - Table of contents
    - Cover images
    - Custom CSS styling
    - Chapter organization
    - Image embedding
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize EPUB generator.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.stats = None
        self._check_dependencies()
    
    def _check_dependencies(self) -> bool:
        """
        Check if Pandoc is available.
        
        Returns:
            True if Pandoc is available
        
        Raises:
            RuntimeError: If Pandoc is not available
        """
        try:
            result = subprocess.run(
                ['pandoc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                if self.verbose:
                    version = result.stdout.split('\n')[0]
                    logger.info(f"Pandoc found: {version}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(
                "Pandoc is required for EPUB generation. "
                "Install from https://pandoc.org/installing.html"
            ) from e
        
        return False
    
    def _create_metadata_file(self, metadata: EPUBMetadata, temp_dir: Path) -> Path:
        """
        Create a temporary metadata YAML file for Pandoc.
        
        Args:
            metadata: EPUB metadata
            temp_dir: Temporary directory
        
        Returns:
            Path to metadata file
        """
        metadata_file = temp_dir / "metadata.yaml"
        metadata_dict = metadata.to_pandoc_metadata()
        
        # Write YAML metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write("---\n")
            for key, value in metadata_dict.items():
                if isinstance(value, list):
                    f.write(f"{key}:\n")
                    for item in value:
                        f.write(f"  - {item}\n")
                else:
                    f.write(f"{key}: {value}\n")
            f.write("---\n")
        
        return metadata_file
    
    def _count_chapters(self, markdown_file: Path) -> int:
        """
        Count number of chapters (# headings) in markdown.
        
        Args:
            markdown_file: Path to markdown file
        
        Returns:
            Number of level 1 headings
        """
        try:
            content = markdown_file.read_text(encoding='utf-8')
            return content.count('\n# ')
        except Exception as e:
            logger.warning(f"Failed to count chapters: {e}")
            return 0
    
    def _count_images(self, markdown_file: Path) -> int:
        """
        Count number of images in markdown.
        
        Args:
            markdown_file: Path to markdown file
        
        Returns:
            Number of image references
        """
        try:
            content = markdown_file.read_text(encoding='utf-8')
            # Count markdown images: ![alt](path)
            return content.count('![')
        except Exception as e:
            logger.warning(f"Failed to count images: {e}")
            return 0
    
    def markdown_to_epub(
        self,
        input_file: str,
        output_file: str,
        metadata: Optional[EPUBMetadata] = None,
        cover_image: Optional[str] = None,
        css_file: Optional[str] = None,
        toc_depth: int = 3,
        verbose: bool = False
    ) -> bool:
        """
        Convert Markdown to EPUB.
        
        Args:
            input_file: Input Markdown file
            output_file: Output EPUB file
            metadata: EPUB metadata (optional)
            cover_image: Path to cover image (optional)
            css_file: Custom CSS file (optional)
            toc_depth: Table of contents depth (default: 3)
            verbose: Verbose output
        
        Returns:
            True if successful
        """
        import time
        start_time = time.time()
        
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_file}")
            return False
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use provided metadata or create default
        if metadata is None:
            metadata = EPUBMetadata(
                title=input_path.stem.replace('_', ' ').replace('-', ' ').title()
            )
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Build Pandoc command
                cmd = [
                    'pandoc',
                    str(input_path),
                    '-o', str(output_path),
                    '--to=epub',
                    f'--toc-depth={toc_depth}',
                    '--standalone',
                ]
                
                # Add metadata
                if metadata:
                    metadata_file = self._create_metadata_file(metadata, temp_path)
                    cmd.extend(['--metadata-file', str(metadata_file)])
                
                # Add cover image
                if cover_image and Path(cover_image).exists():
                    cmd.extend(['--epub-cover-image', cover_image])
                    if verbose:
                        logger.info(f"Using cover image: {cover_image}")
                
                # Add custom CSS
                if css_file and Path(css_file).exists():
                    cmd.extend(['--css', css_file])
                    if verbose:
                        logger.info(f"Using CSS: {css_file}")
                
                # Execute Pandoc
                if verbose:
                    logger.info(f"Generating EPUB: {output_file}")
                    logger.debug(f"Command: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )
                
                if result.returncode != 0:
                    logger.error(f"Pandoc failed: {result.stderr}")
                    return False
                
                # Collect statistics
                generation_time = time.time() - start_time
                file_size = output_path.stat().st_size if output_path.exists() else 0
                chapters = self._count_chapters(input_path)
                images = self._count_images(input_path)
                
                self.stats = EPUBGenerationStats(
                    input_file=str(input_path),
                    output_file=str(output_path),
                    chapters=chapters,
                    images=images,
                    file_size=file_size,
                    generation_time=generation_time,
                    metadata=metadata
                )
                
                if verbose:
                    print(self.stats.report())
                
                return True
        
        except subprocess.TimeoutExpired:
            logger.error("EPUB generation timed out (300s limit)")
            return False
        except Exception as e:
            logger.error(f"EPUB generation failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def get_stats(self) -> Optional[EPUBGenerationStats]:
        """
        Get statistics from last generation.
        
        Returns:
            Statistics or None
        """
        return self.stats


def markdown_to_epub(
    input_file: str,
    output_file: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    publisher: Optional[str] = None,
    cover_image: Optional[str] = None,
    css_file: Optional[str] = None,
    verbose: bool = False,
    **kwargs
) -> bool:
    """
    Convenience function for converting Markdown to EPUB.
    
    Args:
        input_file: Input Markdown file
        output_file: Output EPUB file
        title: Book title
        author: Author name
        publisher: Publisher name
        cover_image: Cover image path
        css_file: Custom CSS file
        verbose: Verbose output
        **kwargs: Additional metadata (isbn, date, language, etc.)
    
    Returns:
        True if successful
    
    Example:
        >>> markdown_to_epub(
        ...     'book.md',
        ...     'book.epub',
        ...     title="My Book",
        ...     author="Jane Doe",
        ...     isbn="978-1-234567-89-0"
        ... )
    """
    # Build metadata
    metadata = EPUBMetadata(
        title=title,
        author=author,
        publisher=publisher,
        isbn=kwargs.get('isbn'),
        date=kwargs.get('date'),
        language=kwargs.get('language', 'en'),
        description=kwargs.get('description'),
        subject=kwargs.get('subject'),
        rights=kwargs.get('rights'),
        identifier=kwargs.get('identifier')
    )
    
    generator = EPUBGenerator(verbose=verbose)
    return generator.markdown_to_epub(
        input_file,
        output_file,
        metadata=metadata,
        cover_image=cover_image,
        css_file=css_file,
        toc_depth=kwargs.get('toc_depth', 3),
        verbose=verbose
    )


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python epub_generator.py input.md output.epub")
        sys.exit(1)
    
    success = markdown_to_epub(
        sys.argv[1],
        sys.argv[2],
        verbose=True
    )
    
    sys.exit(0 if success else 1)
