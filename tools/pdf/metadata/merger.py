"""
Merge metadata from multiple sources with precedence rules.
"""
from typing import Dict, Any, Optional
from .models import DocumentMetadata


class MetadataMerger:
    """
    Merge metadata from multiple sources with precedence.
    
    Precedence (highest to lowest):
    1. CLI/Web overrides (custom_metadata)
    2. Frontmatter metadata
    3. Default values
    
    Example:
        merger = MetadataMerger()
        final_metadata = merger.merge(
            frontmatter={'author': 'Alice'},
            overrides={'version': '2.0'},
            defaults=DocumentMetadata()
        )
    """
    
    def merge(
        self,
        frontmatter: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        defaults: Optional[DocumentMetadata] = None
    ) -> DocumentMetadata:
        """
        Merge metadata from all sources.
        
        Args:
            frontmatter: Metadata from document frontmatter
            overrides: CLI/Web overrides (highest priority)
            defaults: Default metadata values (lowest priority)
        
        Returns:
            Merged DocumentMetadata instance
        """
        # Start with defaults
        if defaults is None:
            merged = {}
        else:
            merged = defaults.to_dict(include_none=False)
        
        # Merge frontmatter (overrides defaults)
        if frontmatter:
            merged.update({k: v for k, v in frontmatter.items() if v is not None})
        
        # Merge CLI/web overrides (highest priority)
        if overrides:
            merged.update({k: v for k, v in overrides.items() if v is not None})
        
        # Create DocumentMetadata from merged dict
        return DocumentMetadata.from_dict(merged)

