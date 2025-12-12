#!/usr/bin/env python3
"""
Markdown Exporter
=================

Exports processed documents to clean, formatted markdown.

Features:
- Preserve document structure and formatting
- Extract frontmatter (metadata)
- Handle code blocks with syntax highlighting
- Generate table of contents
- Format images and links
- Support for custom templates

Usage:
    from core.markdown_exporter import MarkdownExporter
    
    exporter = MarkdownExporter()
    
    # Export HTML to markdown
    markdown = exporter.html_to_markdown(html_content)
    
    # Export with options
    markdown = exporter.html_to_markdown(
        html_content,
        include_toc=True,
        preserve_formatting=True
    )
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarkdownMetadata:
    """Document metadata for frontmatter."""
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    version: Optional[str] = None
    
    def to_yaml_frontmatter(self) -> str:
        """Convert to YAML frontmatter."""
        if not any([self.title, self.author, self.date, self.description, self.tags]):
            return ""
        
        lines = ["---"]
        if self.title:
            lines.append(f"title: {self.title}")
        if self.author:
            lines.append(f"author: {self.author}")
        if self.date:
            lines.append(f"date: {self.date}")
        if self.description:
            lines.append(f"description: {self.description}")
        if self.category:
            lines.append(f"category: {self.category}")
        if self.version:
            lines.append(f"version: {self.version}")
        if self.tags:
            tags_str = ", ".join(self.tags)
            lines.append(f"tags: [{tags_str}]")
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)


@dataclass
class MarkdownExportStats:
    """Statistics for markdown export."""
    total_headings: int = 0
    total_paragraphs: int = 0
    total_code_blocks: int = 0
    total_images: int = 0
    total_links: int = 0
    total_tables: int = 0
    preserved_formatting: int = 0
    
    def report(self) -> str:
        """Generate human-readable report."""
        return f"""\
[INFO] Markdown Export Report
       Headings: {self.total_headings}
       Paragraphs: {self.total_paragraphs}
       Code Blocks: {self.total_code_blocks}
       Images: {self.total_images}
       Links: {self.total_links}
       Tables: {self.total_tables}
       Formatting Preserved: {self.preserved_formatting}"""


class MarkdownExporter:
    """
    Export documents to clean, formatted markdown.
    
    Supports:
    - HTML to Markdown conversion
    - Frontmatter generation
    - Table of contents generation
    - Link and image preservation
    - Code block formatting
    """
    
    def __init__(self, preserve_formatting: bool = True):
        """
        Initialize exporter.
        
        Args:
            preserve_formatting: Keep original formatting where possible
        """
        self.preserve_formatting = preserve_formatting
        self.stats = MarkdownExportStats()
        self.heading_levels: Dict[str, int] = {}
    
    def export_to_file(
        self,
        content: str,
        output_path: Path,
        metadata: Optional[MarkdownMetadata] = None,
        include_toc: bool = False,
        verbose: bool = False
    ) -> bool:
        """
        Export markdown to file.
        
        Args:
            content: Markdown content
            output_path: Path to save file
            metadata: Optional document metadata
            include_toc: Generate table of contents
            verbose: Verbose output
        
        Returns:
            True if successful
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build final content
            final_content = ""
            
            # Add frontmatter
            if metadata:
                final_content += metadata.to_yaml_frontmatter()
            
            # Add TOC if requested
            if include_toc:
                toc = self._generate_toc(content)
                if toc:
                    final_content += toc
                    final_content += "\n---\n\n"
            
            # Add content
            final_content += content
            
            # Write file
            output_path.write_text(final_content, encoding='utf-8')
            
            if verbose:
                print(f"[OK] Exported markdown: {output_path}")
                print(self.stats.report())
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to export markdown: {e}")
            return False
    
    def html_to_markdown(
        self,
        html_content: str,
        include_toc: bool = False,
        extract_metadata: bool = True
    ) -> Tuple[str, Optional[MarkdownMetadata]]:
        """
        Convert HTML to markdown.
        
        Args:
            html_content: HTML content to convert
            include_toc: Generate table of contents
            extract_metadata: Extract metadata from HTML
        
        Returns:
            Tuple of (markdown_content, metadata)
        """
        self.stats = MarkdownExportStats()  # Reset stats
        
        md_content = html_content
        metadata = None
        
        try:
            # Extract metadata
            if extract_metadata:
                metadata = self._extract_metadata(md_content)
            
            # Convert HTML tags to markdown
            md_content = self._convert_headings(md_content)
            md_content = self._convert_bold_italic(md_content)
            md_content = self._convert_lists(md_content)
            md_content = self._convert_code_blocks(md_content)
            md_content = self._convert_tables(md_content)
            md_content = self._convert_images(md_content)
            md_content = self._convert_links(md_content)
            md_content = self._convert_blockquotes(md_content)
            md_content = self._clean_whitespace(md_content)
            
            logger.info(f"Converted HTML to markdown: {self.stats.total_headings} headings, {self.stats.total_paragraphs} paragraphs")
            
            return md_content, metadata
        
        except Exception as e:
            logger.error(f"Failed to convert HTML to markdown: {e}")
            return html_content, metadata
    
    def _extract_metadata(self, content: str) -> Optional[MarkdownMetadata]:
        """Extract metadata from content."""
        metadata = MarkdownMetadata()
        
        # Look for title (first H1)
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
        if h1_match:
            metadata.title = h1_match.group(1).strip()
        
        # Look for metadata in meta tags or comments
        author_match = re.search(r'author["\']?\s*[:=]\s*["\']?([^"\'>]+)', content, re.IGNORECASE)
        if author_match:
            metadata.author = author_match.group(1).strip()
        
        date_match = re.search(r'date["\']?\s*[:=]\s*["\']?([^"\'>]+)', content, re.IGNORECASE)
        if date_match:
            metadata.date = date_match.group(1).strip()
        
        return metadata if any([metadata.title, metadata.author, metadata.date]) else None
    
    def _convert_headings(self, content: str) -> str:
        """Convert HTML headings to markdown."""
        for level in range(1, 7):
            pattern = f'<h{level}[^>]*>([^<]+)</h{level}>'
            replacement = lambda m: '#' * level + ' ' + m.group(1) + '\n'
            
            matches = re.findall(pattern, content, re.IGNORECASE)
            self.stats.total_headings += len(matches)
            
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        return content
    
    def _convert_bold_italic(self, content: str) -> str:
        """Convert bold and italic tags."""
        # Bold
        content = re.sub(r'<strong[^>]*>([^<]+)</strong>', r'**\1**', content, flags=re.IGNORECASE)
        content = re.sub(r'<b[^>]*>([^<]+)</b>', r'**\1**', content, flags=re.IGNORECASE)
        
        # Italic
        content = re.sub(r'<em[^>]*>([^<]+)</em>', r'*\1*', content, flags=re.IGNORECASE)
        content = re.sub(r'<i[^>]*>([^<]+)</i>', r'*\1*', content, flags=re.IGNORECASE)
        
        return content
    
    def _convert_lists(self, content: str) -> str:
        """Convert HTML lists to markdown."""
        # Unordered lists
        content = re.sub(r'<ul[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</ul>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<li[^>]*>([^<]+)</li>', r'- \1\n', content, flags=re.IGNORECASE)
        
        # Ordered lists
        content = re.sub(r'<ol[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</ol>', '', content, flags=re.IGNORECASE)
        
        # Convert ordered list items with counter
        ol_pattern = r'<li[^>]*>([^<]+)</li>'
        ol_counter = [0]
        
        def ol_replacement(match):
            ol_counter[0] += 1
            return f'{ol_counter[0]}. {match.group(1)}\n'
        
        content = re.sub(ol_pattern, ol_replacement, content, flags=re.IGNORECASE)
        
        return content
    
    def _convert_code_blocks(self, content: str) -> str:
        """Convert code blocks."""
        # Pre/code blocks
        pattern = r'<pre[^>]*>\s*<code[^>]*language="?([^"]+)?"?[^>]*>([^<]*)</code>\s*</pre>'
        
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        self.stats.total_code_blocks += len(matches)
        
        def code_replacement(match):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            return f'\n```{language}\n{code}\n```\n'
        
        content = re.sub(pattern, code_replacement, content, flags=re.IGNORECASE | re.DOTALL)
        
        # Inline code
        content = re.sub(r'<code[^>]*>([^<]+)</code>', r'`\1`', content, flags=re.IGNORECASE)
        
        return content
    
    def _convert_tables(self, content: str) -> str:
        """Convert HTML tables to markdown."""
        table_pattern = r'<table[^>]*>([^<]*(?:(?!<table|</table>)[^<])*)</table>'
        
        def table_replacement(match):
            self.stats.total_tables += 1
            table_html = match.group(1)
            
            # Extract rows
            row_pattern = r'<tr[^>]*>([^<]*(?:(?!</tr>)[^<])*)</tr>'
            rows = re.findall(row_pattern, table_html, re.IGNORECASE | re.DOTALL)
            
            if not rows:
                return ""
            
            md_rows = []
            for row_html in rows:
                # Extract cells
                cell_pattern = r'<(?:td|th)[^>]*>([^<]*)</(?:td|th)>'
                cells = re.findall(cell_pattern, row_html, re.IGNORECASE)
                md_rows.append('| ' + ' | '.join(cells) + ' |')
            
            # Add separator after first row if it's a header
            if len(md_rows) > 1:
                separator = '| ' + ' | '.join(['---'] * len(md_rows[0].split('|')[1:-1])) + ' |'
                md_rows.insert(1, separator)
            
            return '\n' + '\n'.join(md_rows) + '\n'
        
        content = re.sub(table_pattern, table_replacement, content, flags=re.IGNORECASE | re.DOTALL)
        return content
    
    def _convert_images(self, content: str) -> str:
        """Convert image tags."""
        pattern = r'<img[^>]*src="?([^"\s>]+)"?[^>]*alt="?([^"\s>]*)"?[^>]*>'
        
        matches = re.findall(pattern, content, re.IGNORECASE)
        self.stats.total_images += len(matches)
        
        def img_replacement(match):
            src = match.group(1)
            alt = match.group(2) or 'Image'
            return f'![{alt}]({src})'
        
        content = re.sub(pattern, img_replacement, content, flags=re.IGNORECASE)
        return content
    
    def _convert_links(self, content: str) -> str:
        """Convert links."""
        pattern = r'<a[^>]*href="?([^"\s>]+)"?[^>]*>([^<]+)</a>'
        
        matches = re.findall(pattern, content, re.IGNORECASE)
        self.stats.total_links += len(matches)
        
        def link_replacement(match):
            href = match.group(1)
            text = match.group(2)
            return f'[{text}]({href})'
        
        content = re.sub(pattern, link_replacement, content, flags=re.IGNORECASE)
        return content
    
    def _convert_blockquotes(self, content: str) -> str:
        """Convert blockquotes."""
        pattern = r'<blockquote[^>]*>([^<]*(?:(?!</blockquote>)[^<])*)</blockquote>'
        
        def quote_replacement(match):
            quote_content = match.group(1).strip()
            lines = quote_content.split('\n')
            return '\n' + '\n'.join(f'> {line}' if line.strip() else '>' for line in lines) + '\n'
        
        content = re.sub(pattern, quote_replacement, content, flags=re.IGNORECASE | re.DOTALL)
        return content
    
    def _clean_whitespace(self, content: str) -> str:
        """Clean up whitespace."""
        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove multiple blank lines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Fix spacing around markdown elements
        content = re.sub(r'\n\n(#{1,6} )', r'\n\1', content)
        content = re.sub(r'(#{1,6} .+)\n\n(\S)', r'\1\n\2', content)
        
        # Trim leading/trailing whitespace
        content = content.strip()
        
        self.stats.total_paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        
        return content
    
    def _generate_toc(self, content: str, max_depth: int = 3) -> Optional[str]:
        """Generate table of contents."""
        headings = re.findall(r'^(#{1,6}) (.+)$', content, re.MULTILINE)
        
        if not headings:
            return None
        
        toc_lines = ['## Table of Contents\n']
        
        for level, text in headings:
            depth = len(level)
            if depth > max_depth:
                continue
            
            # Generate anchor
            anchor = text.lower()
            anchor = re.sub(r'[^\w\s-]', '', anchor)
            anchor = re.sub(r'\s+', '-', anchor)
            
            indent = '  ' * (depth - 1)
            toc_lines.append(f'{indent}- [{text}](#{anchor})')
        
        return '\n'.join(toc_lines) + '\n'
    
    def get_stats(self) -> MarkdownExportStats:
        """Get export statistics."""
        return self.stats
