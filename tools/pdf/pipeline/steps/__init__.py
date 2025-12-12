"""
Pipeline steps for document processing.

Exports all available pipeline steps for building custom pipelines.

Preprocessing Steps:
    - ReadContentStep: Read raw markdown from input file
    - MetadataExtractionStep: Extract and merge metadata
    - GlossaryExpansionStep: Expand glossary terms
    - MathRenderingStep: Pre-render math with KaTeX

Conversion Steps:
    - DiagramRenderingStep: Render Mermaid/PlantUML/Graphviz diagrams
    - PandocConversionStep: Convert Markdown to HTML

Enhancement Steps:
    - MermaidEnhancementStep: Inject Mermaid 11 with CSS variable theming

Post-processing Steps:
    - CSSStrippingStep: Strip inline styles from HTML
    - TitlePageInjectionStep: Inject title page HTML
    - MetadataInjectionStep: Inject metadata as HTML meta tags

Rendering Steps:
    - PdfRenderingStep: Generate PDF from HTML
    - DocxRenderingStep: Generate DOCX from Markdown
    - HtmlRenderingStep: Generate standalone HTML
"""

from .preprocessing import (
    ReadContentStep,
    MetadataExtractionStep,
    GlossaryExpansionStep,
    MathRenderingStep,
)

from .diagram_step import DiagramRenderingStep

from .pandoc_step import PandocConversionStep

from .mermaid_enhancement_step import MermaidEnhancementStep

from .postprocessing import (
    CSSStrippingStep,
    TitlePageInjectionStep,
    MetadataInjectionStep,
)

from .rendering_step import (
    PdfRenderingStep,
    DocxRenderingStep,
    HtmlRenderingStep,
)

__all__ = [
    # Preprocessing
    'ReadContentStep',
    'MetadataExtractionStep',
    'GlossaryExpansionStep',
    'MathRenderingStep',
    
    # Conversion
    'DiagramRenderingStep',
    'PandocConversionStep',
    
    # Enhancement
    'MermaidEnhancementStep',
    
    # Post-processing
    'CSSStrippingStep',
    'TitlePageInjectionStep',
    'MetadataInjectionStep',
    
    # Rendering
    'PdfRenderingStep',
    'DocxRenderingStep',
    'HtmlRenderingStep',
]
