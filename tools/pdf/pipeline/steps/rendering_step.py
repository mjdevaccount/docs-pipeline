"""
Rendering pipeline steps.
PDF, DOCX, and HTML output generation.
"""
import shutil
import subprocess
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class PdfRenderingStep(PipelineStep):
    """
    Generate PDF from HTML using renderer strategy.
    Uses RendererFactory for pluggable rendering backends.
    """
    
    def get_name(self) -> str:
        return "PDF Rendering"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure HTML content is available"""
        if not context.html_content and not context.html_file:
            raise PipelineError("No HTML content to render")
    
    def execute(self, context: PipelineContext) -> bool:
        """Render PDF using RendererFactory"""
        try:
            # Ensure HTML file exists
            if not context.html_file or not context.html_file.exists():
                # Write HTML content to temp file
                context.html_file = context.work_dir / 'output.html'
                context.html_file.write_text(context.html_content, encoding='utf-8')
                context.temp_files.append(context.html_file)
            
            # Try new architecture first
            try:
                from renderers import RendererFactory, RenderConfig, RendererType
                
                renderer_name = context.get_config('renderer', 'playwright')
                
                # Get renderer with fallback
                renderer_type = RendererType(renderer_name)
                pdf_renderer = RendererFactory.get_renderer_with_fallback(
                    preferred=renderer_type,
                    fallback=RendererType.WEASYPRINT,
                    verbose=context.verbose
                )
                
                # Build configuration
                config = RenderConfig(
                    html_file=context.html_file,
                    output_file=context.output_file,
                    css_file=Path(context.get_config('css_file')) if context.get_config('css_file') else None,
                    generate_toc=context.get_config('generate_toc', False),
                    generate_cover=context.get_config('generate_cover', False),
                    watermark=context.get_config('watermark'),
                    title=context.metadata.get('title'),
                    author=context.metadata.get('author'),
                    organization=context.metadata.get('organization'),
                    date=context.metadata.get('date'),
                    version=context.metadata.get('version'),
                    doc_type=context.metadata.get('type'),
                    classification=context.metadata.get('classification'),
                    logo_path=Path(context.get_config('logo_path')) if context.get_config('logo_path') else None,
                    verbose=context.verbose
                )
                
                success = pdf_renderer.render(config)
                
                if success:
                    self.log(f"Created {context.output_file}", context)
                    return True
                else:
                    raise PipelineError("PDF rendering returned failure")
                
            except ImportError:
                # Fallback to legacy rendering
                self.log("Using legacy PDF rendering", context)
                return self._legacy_render(context)
            
        except PipelineError:
            raise
        except Exception as e:
            raise PipelineError(f"PDF rendering failed: {e}")
    
    def _legacy_render(self, context: PipelineContext) -> bool:
        """Fallback to WeasyPrint direct call"""
        try:
            from weasyprint import HTML, CSS
            
            html = HTML(filename=str(context.html_file))
            
            css_file = context.get_config('css_file')
            if css_file and Path(css_file).exists():
                stylesheets = [CSS(filename=str(css_file))]
            else:
                stylesheets = None
            
            html.write_pdf(str(context.output_file), stylesheets=stylesheets)
            
            self.log(f"Created {context.output_file} (WeasyPrint legacy)", context)
            return True
            
        except Exception as e:
            raise PipelineError(f"Legacy PDF rendering failed: {e}")


class DocxRenderingStep(PipelineStep):
    """
    Generate DOCX from Markdown using Pandoc.
    """
    
    def get_name(self) -> str:
        return "DOCX Rendering"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure markdown content is available"""
        if not context.preprocessed_markdown:
            raise PipelineError("No markdown content to convert")
    
    def execute(self, context: PipelineContext) -> bool:
        """Generate DOCX using Pandoc"""
        try:
            # Write preprocessed markdown to temp file
            tmp_md = context.work_dir / 'preprocessed.md'
            tmp_md.write_text(context.preprocessed_markdown, encoding='utf-8')
            context.temp_files.append(tmp_md)
            
            # Try new architecture first
            try:
                from external_tools import PandocExecutor, ToolNotFoundError
                
                pandoc = PandocExecutor()
                extensions = pandoc.get_default_markdown_extensions()
                
                # Build extra args
                extra_args = []
                reference_docx = context.get_config('reference_docx')
                if reference_docx and Path(reference_docx).exists():
                    extra_args.extend(['--reference-doc', str(reference_docx)])
                
                success = pandoc.convert(
                    tmp_md,
                    context.output_file,
                    from_format=f'markdown{extensions}',
                    to_format='docx',
                    extra_args=extra_args if extra_args else None
                )
                
                if success:
                    self.log(f"Created {context.output_file}", context)
                    return True
                else:
                    raise PipelineError("Pandoc DOCX conversion failed")
                
            except ImportError:
                # Fallback to subprocess
                return self._legacy_render(context, tmp_md)
            
        except PipelineError:
            raise
        except Exception as e:
            raise PipelineError(f"DOCX rendering failed: {e}")
    
    def _legacy_render(self, context: PipelineContext, tmp_md: Path) -> bool:
        """Fallback to direct Pandoc subprocess"""
        pandoc_exe = shutil.which('pandoc') or 'pandoc'
        
        cmd = [
            pandoc_exe,
            str(tmp_md),
            '-o', str(context.output_file),
            '--from', 'markdown+yaml_metadata_block+raw_html+fenced_code_blocks+tables+pipe_tables',
            '--to', 'docx',
        ]
        
        reference_docx = context.get_config('reference_docx')
        if reference_docx and Path(reference_docx).exists():
            cmd.extend(['--reference-doc', str(reference_docx)])
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.log(f"Created {context.output_file} (Pandoc legacy)", context)
            return True
        except subprocess.CalledProcessError as e:
            raise PipelineError(f"Pandoc DOCX failed: {e.stderr}")


class HtmlRenderingStep(PipelineStep):
    """
    Generate standalone HTML output.
    Copies HTML to output location with optional styling.
    """
    
    def get_name(self) -> str:
        return "HTML Rendering"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure HTML content is available"""
        if not context.html_content:
            raise PipelineError("No HTML content to output")
    
    def execute(self, context: PipelineContext) -> bool:
        """Write HTML to output file"""
        try:
            # Get custom CSS if provided
            css_file = context.get_config('css_file')
            
            if css_file and Path(css_file).exists():
                # Inject CSS into HTML
                css_content = Path(css_file).read_text(encoding='utf-8')
                style_tag = f'<style>\n{css_content}\n</style>'
                
                if '</head>' in context.html_content:
                    context.html_content = context.html_content.replace(
                        '</head>',
                        f'{style_tag}\n</head>'
                    )
            
            # Write output
            context.output_file.write_text(context.html_content, encoding='utf-8')
            
            # Copy SVG files to output directory
            output_dir = context.output_file.parent
            for svg_file in context.svg_files:
                if svg_file.exists():
                    dest = output_dir / svg_file.name
                    shutil.copy2(svg_file, dest)
            
            self.log(f"Created {context.output_file}", context)
            return True
            
        except Exception as e:
            raise PipelineError(f"HTML rendering failed: {e}")

