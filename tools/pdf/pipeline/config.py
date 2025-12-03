"""
Pipeline configuration for document processing.
Provides typed configuration options for all pipeline steps.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class OutputFormat(Enum):
    """Supported output formats"""
    PDF = 'pdf'
    DOCX = 'docx'
    HTML = 'html'


@dataclass
class PipelineConfig:
    """
    Configuration for document processing pipeline.
    
    This config consolidates all options across pipeline steps
    to avoid passing multiple kwargs through the system.
    
    Attributes:
        output_format: Target format (PDF, DOCX, HTML)
        
        # Preprocessing options
        glossary_file: Path to glossary YAML file
        enable_math: Enable KaTeX math rendering
        enable_diagrams: Enable diagram rendering
        
        # Diagram options
        cache_dir: Directory for diagram cache
        use_cache: Whether to use cached diagrams
        theme_config: Path to Mermaid theme config
        also_png: Generate PNG alongside SVG
        
        # Pandoc options
        highlight_style: Code highlight style (default: 'pygments')
        crossref_config: Path to pandoc-crossref config
        
        # Rendering options (PDF only)
        renderer: Renderer to use ('playwright' or 'weasyprint')
        css_file: Custom CSS file
        generate_toc: Generate table of contents
        generate_cover: Generate cover page
        watermark: Watermark text
        logo_path: Path to logo image
        
        # Metadata overrides
        custom_metadata: Dict of metadata overrides
        
        # Behavior
        verbose: Enable verbose logging
    """
    # Output format
    output_format: OutputFormat = OutputFormat.PDF
    
    # Preprocessing options
    glossary_file: Optional[Path] = None
    enable_math: bool = True
    enable_diagrams: bool = True
    
    # Diagram options
    cache_dir: Optional[Path] = None
    use_cache: bool = True
    theme_config: Optional[Path] = None
    also_png: bool = False
    
    # Pandoc options
    highlight_style: str = 'pygments'
    crossref_config: Optional[Path] = None
    
    # Rendering options (PDF only)
    renderer: str = 'playwright'
    css_file: Optional[Path] = None
    generate_toc: bool = False
    generate_cover: bool = False
    watermark: Optional[str] = None
    logo_path: Optional[Path] = None
    
    # DOCX options
    reference_docx: Optional[Path] = None
    
    # Metadata overrides
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Behavior
    verbose: bool = False
    
    def __post_init__(self):
        """Convert string paths to Path objects"""
        if self.glossary_file and isinstance(self.glossary_file, str):
            self.glossary_file = Path(self.glossary_file)
        if self.cache_dir and isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)
        if self.theme_config and isinstance(self.theme_config, str):
            self.theme_config = Path(self.theme_config)
        if self.crossref_config and isinstance(self.crossref_config, str):
            self.crossref_config = Path(self.crossref_config)
        if self.css_file and isinstance(self.css_file, str):
            self.css_file = Path(self.css_file)
        if self.logo_path and isinstance(self.logo_path, str):
            self.logo_path = Path(self.logo_path)
        if self.reference_docx and isinstance(self.reference_docx, str):
            self.reference_docx = Path(self.reference_docx)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for legacy compatibility"""
        return {
            'output_format': self.output_format.value,
            'glossary_file': str(self.glossary_file) if self.glossary_file else None,
            'enable_math': self.enable_math,
            'enable_diagrams': self.enable_diagrams,
            'cache_dir': str(self.cache_dir) if self.cache_dir else None,
            'use_cache': self.use_cache,
            'theme_config': str(self.theme_config) if self.theme_config else None,
            'also_png': self.also_png,
            'highlight_style': self.highlight_style,
            'crossref_config': str(self.crossref_config) if self.crossref_config else None,
            'renderer': self.renderer,
            'css_file': str(self.css_file) if self.css_file else None,
            'generate_toc': self.generate_toc,
            'generate_cover': self.generate_cover,
            'watermark': self.watermark,
            'logo_path': str(self.logo_path) if self.logo_path else None,
            'reference_docx': str(self.reference_docx) if self.reference_docx else None,
            'custom_metadata': self.custom_metadata,
            'verbose': self.verbose,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineConfig':
        """Create config from dictionary"""
        # Handle output_format enum
        if 'output_format' in data and isinstance(data['output_format'], str):
            data['output_format'] = OutputFormat(data['output_format'])
        return cls(**data)
    
    @classmethod
    def for_pdf(cls, **kwargs) -> 'PipelineConfig':
        """Create config optimized for PDF output"""
        return cls(output_format=OutputFormat.PDF, **kwargs)
    
    @classmethod
    def for_docx(cls, **kwargs) -> 'PipelineConfig':
        """Create config optimized for DOCX output"""
        return cls(
            output_format=OutputFormat.DOCX,
            enable_math=False,  # Pandoc handles math for DOCX
            **kwargs
        )
    
    @classmethod
    def for_html(cls, **kwargs) -> 'PipelineConfig':
        """Create config optimized for HTML output"""
        return cls(
            output_format=OutputFormat.HTML,
            generate_cover=False,
            generate_toc=False,
            **kwargs
        )

