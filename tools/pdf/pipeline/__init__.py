"""
Document Processing Pipeline Module

Provides a flexible pipeline architecture for document processing
following the Pipeline + Template Method patterns.

Features:
- Composable pipeline steps
- Shared context for inter-step communication
- Easy testing of individual steps
- Code reuse across PDF/DOCX/HTML converters
- Extensible (add custom steps without modifying existing code)

Usage:
    from pipeline import Pipeline, PipelineContext, create_pdf_pipeline
    
    # Use pre-built pipeline
    pipeline = create_pdf_pipeline()
    
    context = PipelineContext(
        input_file='document.md',
        output_file='document.pdf',
        work_dir=tempfile.mkdtemp(),
        config={'renderer': 'playwright', 'generate_cover': True}
    )
    
    success = pipeline.execute(context)
    
    # Or build custom pipeline
    from pipeline.steps import (
        ReadContentStep, MetadataExtractionStep,
        DiagramRenderingStep, PandocConversionStep, PdfRenderingStep
    )
    
    custom_pipeline = Pipeline([
        ReadContentStep(),
        MetadataExtractionStep(),
        DiagramRenderingStep(),
        PandocConversionStep(),
        PdfRenderingStep()
    ])
"""

from .base import (
    PipelineContext,
    PipelineStep,
    Pipeline,
    PipelineError,
)

from .config import (
    PipelineConfig,
    OutputFormat,
)

from .steps import (
    # Preprocessing
    ReadContentStep,
    MetadataExtractionStep,
    GlossaryExpansionStep,
    MathRenderingStep,
    
    # Conversion
    DiagramRenderingStep,
    PandocConversionStep,
    
    # Enhancement
    MermaidEnhancementStep,
    
    # Path Correction (NEW)
    ImagePathCorrectionStep,
    
    # Post-processing
    CSSStrippingStep,
    TitlePageInjectionStep,
    MetadataInjectionStep,
    
    # Rendering
    PdfRenderingStep,
    DocxRenderingStep,
    HtmlRenderingStep,
)

__all__ = [
    # Core
    'PipelineContext',
    'PipelineStep',
    'Pipeline',
    'PipelineError',
    'PipelineConfig',
    'OutputFormat',
    
    # Steps
    'ReadContentStep',
    'MetadataExtractionStep',
    'GlossaryExpansionStep',
    'MathRenderingStep',
    'DiagramRenderingStep',
    'PandocConversionStep',
    'MermaidEnhancementStep',
    'ImagePathCorrectionStep',
    'CSSStrippingStep',
    'TitlePageInjectionStep',
    'MetadataInjectionStep',
    'PdfRenderingStep',
    'DocxRenderingStep',
    'HtmlRenderingStep',
    
    # Factory functions
    'create_pdf_pipeline',
    'create_docx_pipeline',
    'create_html_pipeline',
]


def create_pdf_pipeline(include_math: bool = True, include_glossary: bool = True) -> Pipeline:
    """
    Create a standard PDF generation pipeline.
    
    Step Order (FIXED):
    1. ReadContentStep - Read markdown
    2. MetadataExtractionStep - Extract YAML
    3. GlossaryExpansionStep - Expand glossary terms
    4. MathRenderingStep - Pre-render LaTeX
    5. DiagramRenderingStep - Render Mermaid diagrams
    6. PandocConversionStep - Convert Markdown to HTML
    7. ImagePathCorrectionStep - FIX: Correct diagram paths after Pandoc
    8. MermaidEnhancementStep - Inject Mermaid 11 CSS variables
    9. CSSStrippingStep - Remove inline styles
    10. TitlePageInjectionStep - Inject cover page
    11. MetadataInjectionStep - Inject metadata tags
    12. PdfRenderingStep - Generate PDF via Playwright
    
    Args:
        include_math: Include KaTeX math rendering step
        include_glossary: Include glossary expansion step
    
    Returns:
        Configured Pipeline for PDF generation
    
    Example:
        pipeline = create_pdf_pipeline()
        context = PipelineContext(
            input_file='doc.md',
            output_file='doc.pdf',
            work_dir=Path(tempfile.mkdtemp())
        )
        success = pipeline.execute(context)
    """
    steps = [
        ReadContentStep(),
        MetadataExtractionStep(),
    ]
    
    if include_glossary:
        steps.append(GlossaryExpansionStep())
    
    if include_math:
        steps.append(MathRenderingStep())
    
    steps.extend([
        DiagramRenderingStep(),
        PandocConversionStep(),
        ImagePathCorrectionStep(),  # NEW: Fix diagram paths after Pandoc
        MermaidEnhancementStep(),
        CSSStrippingStep(),
        TitlePageInjectionStep(),
        MetadataInjectionStep(),
        PdfRenderingStep(),
    ])
    
    return Pipeline(steps, name="PDF Generation")


def create_docx_pipeline(include_glossary: bool = True) -> Pipeline:
    """
    Create a standard DOCX generation pipeline.
    
    Args:
        include_glossary: Include glossary expansion step
    
    Returns:
        Configured Pipeline for DOCX generation
    """
    steps = [
        ReadContentStep(),
        MetadataExtractionStep(),
    ]
    
    if include_glossary:
        steps.append(GlossaryExpansionStep())
    
    steps.extend([
        DiagramRenderingStep(),
        DocxRenderingStep(),
    ])
    
    return Pipeline(steps, name="DOCX Generation")


def create_html_pipeline(include_math: bool = True, include_glossary: bool = True) -> Pipeline:
    """
    Create a standard HTML generation pipeline.
    
    Args:
        include_math: Include KaTeX math rendering step
        include_glossary: Include glossary expansion step
    
    Returns:
        Configured Pipeline for HTML generation
    """
    steps = [
        ReadContentStep(),
        MetadataExtractionStep(),
    ]
    
    if include_glossary:
        steps.append(GlossaryExpansionStep())
    
    if include_math:
        steps.append(MathRenderingStep())
    
    steps.extend([
        DiagramRenderingStep(),
        PandocConversionStep(),
        ImagePathCorrectionStep(),  # NEW: Fix diagram paths
        MermaidEnhancementStep(),
        CSSStrippingStep(),
        HtmlRenderingStep(),
    ])
    
    return Pipeline(steps, name="HTML Generation")


def process_document(
    input_file: str,
    output_file: str,
    output_format: OutputFormat = OutputFormat.PDF,
    **kwargs
) -> bool:
    """
    Convenience function to process a document in one call.
    
    Args:
        input_file: Path to input Markdown file
        output_file: Path to output file
        output_format: Target format (PDF, DOCX, HTML)
        **kwargs: Additional configuration options
    
    Returns:
        True if processing succeeded
    
    Example:
        success = process_document(
            'document.md',
            'document.pdf',
            output_format=OutputFormat.PDF,
            renderer='playwright',
            generate_cover=True
        )
    """
    import tempfile
    from pathlib import Path
    
    # Select pipeline based on format
    if output_format == OutputFormat.PDF:
        pipeline = create_pdf_pipeline()
    elif output_format == OutputFormat.DOCX:
        pipeline = create_docx_pipeline()
    else:
        pipeline = create_html_pipeline()
    
    # Create context
    context = PipelineContext(
        input_file=Path(input_file),
        output_file=Path(output_file),
        work_dir=Path(tempfile.mkdtemp(prefix='doc_')),
        config=kwargs,
        verbose=kwargs.get('verbose', False)
    )
    
    try:
        return pipeline.execute(context)
    finally:
        # Cleanup work directory
        import shutil
        if context.work_dir.exists():
            shutil.rmtree(context.work_dir, ignore_errors=True)
