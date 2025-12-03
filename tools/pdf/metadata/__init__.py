"""
Metadata handling for document generation pipeline.

Public API:
    - DocumentMetadata: Type-safe metadata model
    - MetadataExtractor: Extract from frontmatter
    - MetadataValidator: Sanitize and validate
    - MetadataMerger: Merge from multiple sources
    - MetadataDefaults: Default values with env var support
    - HTMLMetadataInjector: Inject into HTML for Playwright
"""

from .models import DocumentMetadata
from .extractor import MetadataExtractor
from .validator import MetadataValidator
from .merger import MetadataMerger
from .defaults import MetadataDefaults
from .injector import HTMLMetadataInjector

__all__ = [
    'DocumentMetadata',
    'MetadataExtractor',
    'MetadataValidator',
    'MetadataMerger',
    'MetadataDefaults',
    'HTMLMetadataInjector',
    'process_metadata',
]


def process_metadata(
    md_file_path=None,
    md_content=None,
    custom_overrides=None
) -> DocumentMetadata:
    """
    One-stop function to extract, validate, merge, and return metadata.
    
    Args:
        md_file_path: Path to Markdown file (optional)
        md_content: Markdown content string (optional, used if md_file_path not provided)
        custom_overrides: CLI/web overrides dict (optional)
    
    Returns:
        Validated and merged DocumentMetadata
    
    Example:
        from metadata import process_metadata
        metadata = process_metadata(
            md_file_path='document.md',
            custom_overrides={'version': '2.0'}
        )
    """
    from pathlib import Path
    
    # Extract frontmatter
    extractor = MetadataExtractor()
    if md_file_path:
        frontmatter, _ = extractor.extract_from_file(Path(md_file_path))
    elif md_content:
        frontmatter, _ = extractor.extract_from_string(md_content)
    else:
        frontmatter = {}
    
    # Validate frontmatter
    validator = MetadataValidator()
    validated_frontmatter = validator.validate(frontmatter)
    
    # Validate overrides
    validated_overrides = validator.validate(custom_overrides) if custom_overrides else None
    
    # Get defaults
    defaults = MetadataDefaults.get_defaults()
    
    # Merge all sources
    merger = MetadataMerger()
    return merger.merge(
        frontmatter=validated_frontmatter,
        overrides=validated_overrides,
        defaults=defaults
    )

