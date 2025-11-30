"""
Configuration Models
====================
Dataclasses for PDF generation options.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class CoverConfig:
    """Cover page configuration"""
    title: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[str] = None
    logo_path: Optional[Path] = None
    type: Optional[str] = None
    classification: Optional[str] = None
    version: Optional[str] = None


@dataclass
class MetadataConfig:
    """PDF metadata configuration"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None


@dataclass
class PdfGenerationConfig:
    """Complete PDF generation configuration"""
    html_file: Path
    pdf_file: Path
    
    # Document metadata
    title: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    date: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    
    # Features
    generate_cover: bool = False
    generate_toc: bool = False
    watermark: Optional[str] = None
    
    # Assets
    logo_path: Optional[Path] = None
    css_file: Optional[Path] = None
    
    # Fonts
    font_families: List[str] = field(default_factory=lambda: ["Inter", "Source Code Pro"])
    
    # Output
    verbose: bool = False
    
    # Additional metadata fields
    type: Optional[str] = None
    classification: Optional[str] = None
    version: Optional[str] = None
    
    # Page format (A4, Letter, Legal, or custom dimensions)
    page_format: str = 'A4'  # Options: 'A4', 'Letter', 'Legal', or custom like '8.5in 11in'
    
    @property
    def cover(self) -> CoverConfig:
        """Get cover page configuration"""
        return CoverConfig(
            title=self.title,
            author=self.author,
            organization=self.organization,
            date=self.date,
            logo_path=self.logo_path,
            type=self.type,
            classification=self.classification,
            version=self.version
        )
    
    @property
    def metadata(self) -> Optional[MetadataConfig]:
        """Get metadata configuration if any fields are set"""
        if self.title or self.author or self.subject or self.keywords:
            return MetadataConfig(
                title=self.title,
                author=self.author,
                subject=self.subject,
                keywords=self.keywords
            )
        return None

