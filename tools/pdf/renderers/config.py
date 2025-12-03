"""
Rendering configuration for PDF generation.
Encapsulates all options needed by any renderer.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class PageFormat(Enum):
    """Supported page formats"""
    A4 = 'A4'
    LETTER = 'Letter'
    LEGAL = 'Legal'


class RendererType(Enum):
    """Available PDF renderers"""
    WEASYPRINT = 'weasyprint'
    PLAYWRIGHT = 'playwright'
    # Future: PRINCE = 'prince', WKHTMLTOPDF = 'wkhtmltopdf'


@dataclass
class RenderConfig:
    """
    Configuration for PDF rendering operations.
    
    This config is renderer-agnostic - different renderers use different subsets.
    
    Required Fields:
        html_file: Path to HTML input file
        output_file: Path to PDF output file
    
    Optional Fields:
        css_file: Custom CSS file path
        page_format: Page format (A4, Letter, Legal)
        generate_toc: Whether to generate table of contents
        generate_cover: Whether to generate cover page
        watermark: Watermark text (e.g., "DRAFT")
        verbose: Verbose output
    
    Renderer-Specific:
        logo_path: Logo for cover page (Playwright only)
        title, author, organization, date, version, classification: Metadata
    """
    
    # Required fields
    html_file: Path
    output_file: Path
    
    # Optional rendering options
    css_file: Optional[Path] = None
    page_format: PageFormat = PageFormat.A4
    generate_toc: bool = False
    generate_cover: bool = False
    watermark: Optional[str] = None
    verbose: bool = False
    
    # Metadata (used for cover page, headers, bookmarks)
    title: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[str] = None
    version: Optional[str] = None
    doc_type: Optional[str] = None
    classification: Optional[str] = None
    
    # Additional options
    logo_path: Optional[Path] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert string paths to Path objects"""
        if isinstance(self.html_file, str):
            self.html_file = Path(self.html_file)
        if isinstance(self.output_file, str):
            self.output_file = Path(self.output_file)
        if self.css_file and isinstance(self.css_file, str):
            self.css_file = Path(self.css_file)
        if self.logo_path and isinstance(self.logo_path, str):
            self.logo_path = Path(self.logo_path)
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if config is valid
        
        Raises:
            ValueError: If config is invalid
        """
        if not self.html_file.exists():
            raise ValueError(f"HTML file not found: {self.html_file}")
        
        if self.css_file and not self.css_file.exists():
            raise ValueError(f"CSS file not found: {self.css_file}")
        
        if self.logo_path and not self.logo_path.exists():
            raise ValueError(f"Logo file not found: {self.logo_path}")
        
        return True

