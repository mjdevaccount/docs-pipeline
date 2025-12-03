"""
Pandoc conversion pipeline step.
Markdown → HTML conversion with extensions.
"""
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class PandocConversionStep(PipelineStep):
    """
    Convert Markdown to HTML using Pandoc.
    Uses PandocExecutor for SOLID-compliant execution.
    """
    
    def get_name(self) -> str:
        return "Pandoc Conversion"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure work directory exists and content is available"""
        if not context.work_dir.exists():
            context.work_dir.mkdir(parents=True, exist_ok=True)
        
        if not context.preprocessed_markdown:
            raise PipelineError("No markdown content to convert")
    
    def execute(self, context: PipelineContext) -> bool:
        """Convert MD→HTML using PandocExecutor"""
        try:
            # Write preprocessed markdown to temp file
            tmp_md = context.work_dir / 'preprocessed.md'
            tmp_md.write_text(context.preprocessed_markdown, encoding='utf-8')
            context.temp_files.append(tmp_md)
            
            # Setup output file
            tmp_html = context.work_dir / 'output.html'
            
            # Get configuration
            highlight_style = context.get_config('highlight_style', 'pygments')
            crossref_config = context.get_config('crossref_config')
            
            # Try new architecture first
            try:
                from external_tools import PandocExecutor, ToolNotFoundError
                
                try:
                    pandoc = PandocExecutor()
                except ToolNotFoundError as e:
                    raise PipelineError(f"Pandoc not available: {e}")
                
                extensions = pandoc.get_default_markdown_extensions()
                
                # Build extra args for crossref
                extra_args = []
                if crossref_config and Path(crossref_config).exists():
                    crossref_filter = shutil.which('pandoc-crossref') or 'pandoc-crossref'
                    extra_args.extend(['--filter', crossref_filter])
                    extra_args.extend(['--metadata', f'crossrefYaml={crossref_config}'])
                
                # Convert
                success = pandoc.convert_markdown_to_html(
                    tmp_md,
                    tmp_html,
                    extensions=extensions,
                    highlight_style=highlight_style,
                    resource_path=context.work_dir,
                    extra_args=extra_args if extra_args else None
                )
                
                if not success:
                    raise PipelineError("Pandoc conversion returned failure")
                
            except ImportError:
                # Fallback to subprocess
                self.log("Using legacy Pandoc subprocess", context)
                success = self._legacy_convert(tmp_md, tmp_html, context)
                
                if not success:
                    raise PipelineError("Legacy Pandoc conversion failed")
            
            # Read HTML content
            context.html_content = tmp_html.read_text(encoding='utf-8')
            context.html_file = tmp_html
            context.temp_files.append(tmp_html)
            
            self.log(f"Converted to HTML ({len(context.svg_files)} diagrams embedded)", context)
            return True
            
        except PipelineError:
            raise
        except Exception as e:
            raise PipelineError(f"Pandoc conversion failed: {e}")
    
    def _legacy_convert(self, input_file: Path, output_file: Path, context: PipelineContext) -> bool:
        """Fallback to direct subprocess call"""
        import subprocess
        
        pandoc_exe = shutil.which('pandoc') or 'pandoc'
        highlight_style = context.get_config('highlight_style', 'pygments')
        
        cmd = [
            pandoc_exe,
            str(input_file),
            '-o', str(output_file),
            '--standalone',
            '--highlight-style', highlight_style,
            '--from', 'markdown+yaml_metadata_block+raw_html+fenced_code_blocks+tables+pipe_tables',
            '--to', 'html5',
            '--resource-path', str(context.work_dir),
        ]
        
        # Add crossref if available
        crossref_config = context.get_config('crossref_config')
        if crossref_config and Path(crossref_config).exists():
            crossref_filter = shutil.which('pandoc-crossref')
            if crossref_filter:
                cmd.extend(['--filter', crossref_filter])
                cmd.extend(['--metadata', f'crossrefYaml={crossref_config}'])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Pandoc error: {e.stderr}", context)
            return False

