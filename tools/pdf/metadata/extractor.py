"""
Extract YAML frontmatter from Markdown files.
Handles both YAML and TOML frontmatter formats.
"""
from pathlib import Path
from typing import Tuple, Dict, Any
import yaml

try:
    import tomli  # Python 3.11+ has tomllib built-in
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        tomli = None


class MetadataExtractor:
    """
    Extract structured metadata from Markdown frontmatter.
    
    Supported formats:
    - YAML (---...---)
    - TOML (+++...+++)
    
    Example:
        extractor = MetadataExtractor()
        metadata, content = extractor.extract_from_file('document.md')
    """
    
    def extract_from_file(self, md_file: Path) -> Tuple[Dict[str, Any], str]:
        """
        Extract metadata and content from Markdown file.
        
        Args:
            md_file: Path to Markdown file
        
        Returns:
            Tuple of (metadata dict, cleaned content without frontmatter)
        """
        content = Path(md_file).read_text(encoding='utf-8')
        return self.extract_from_string(content)
    
    def extract_from_string(self, md_content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract metadata and content from Markdown string.
        
        Args:
            md_content: Markdown content string
        
        Returns:
            Tuple of (metadata dict, cleaned content without frontmatter)
        
        Raises:
            ValueError: If frontmatter is malformed
        """
        # Try YAML frontmatter (---...---)
        if md_content.startswith('---'):
            return self._extract_yaml(md_content)
        
        # Try TOML frontmatter (+++...+++)
        elif md_content.startswith('+++'):
            return self._extract_toml(md_content)
        
        # No frontmatter found
        return {}, md_content
    
    def _extract_yaml(self, md_content: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter"""
        parts = md_content.split('---', 2)
        if len(parts) < 3:
            return {}, md_content
        
        try:
            metadata = yaml.safe_load(parts[1])
            content = parts[2].strip()
            return metadata if metadata else {}, content
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}")
    
    def _extract_toml(self, md_content: str) -> Tuple[Dict[str, Any], str]:
        """Extract TOML frontmatter"""
        if tomli is None:
            raise ImportError("TOML support requires 'tomli' package: pip install tomli")
        
        parts = md_content.split('+++', 2)
        if len(parts) < 3:
            return {}, md_content
        
        try:
            metadata = tomli.loads(parts[1])
            content = parts[2].strip()
            return metadata, content
        except Exception as e:
            raise ValueError(f"Invalid TOML frontmatter: {e}")

