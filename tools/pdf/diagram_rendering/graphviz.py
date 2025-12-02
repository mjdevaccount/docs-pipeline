"""
Graphviz/DOT diagram renderer.
"""
from pathlib import Path
from typing import Optional
import subprocess
import tempfile
import shutil

from .base import DiagramRenderer, DiagramFormat, RenderResult
from .cache import DiagramCache


class GraphvizRenderer(DiagramRenderer):
    """
    Renderer for Graphviz/DOT diagrams.
    
    Requires:
    - Graphviz installed (dot command available)
    
    Supports:
    - DOT graph language
    - SVG output
    - Caching
    """
    
    def __init__(self, cache: Optional[DiagramCache] = None):
        """
        Initialize Graphviz renderer.
        
        Args:
            cache: Optional DiagramCache
        """
        self.cache = cache
        
        # Check if dot command is available
        self.dot_exe = shutil.which('dot')
        self._available = self.dot_exe is not None
    
    def can_render(self, diagram_code: str, format_hint: Optional[str] = None) -> bool:
        """Check if this is a Graphviz diagram."""
        if not self._available:
            return False
        
        if format_hint:
            return format_hint.lower() in ['dot', 'graphviz']
        
        # Graphviz diagrams typically start with digraph/graph/strict
        code = diagram_code.strip().lower()
        return (
            code.startswith('digraph') or
            code.startswith('graph') or
            code.startswith('strict digraph') or
            code.startswith('strict graph')
        )
    
    def validate(self, diagram_code: str) -> bool:
        """Validate Graphviz syntax."""
        code = diagram_code.strip().lower()
        has_start = (
            code.startswith('digraph') or
            code.startswith('graph') or
            code.startswith('strict')
        )
        has_braces = '{' in code and '}' in code
        return has_start and has_braces
    
    def render(
        self,
        diagram_code: str,
        output_file: Path,
        format: DiagramFormat = DiagramFormat.SVG,
        **options
    ) -> RenderResult:
        """
        Render Graphviz diagram.
        
        Args:
            diagram_code: DOT source code
            output_file: Output file path
            format: Output format (currently only SVG)
            **options: Reserved for future options
            
        Returns:
            RenderResult with success status
        """
        if not self._available:
            return RenderResult(
                success=False,
                error_message="Graphviz not available: 'dot' command not found"
            )
        
        if format != DiagramFormat.SVG:
            return RenderResult(
                success=False,
                error_message=f"Graphviz renderer only supports SVG (requested: {format.value})"
            )
        
        # Validate
        if not self.validate(diagram_code):
            return RenderResult(
                success=False,
                error_message="Invalid Graphviz syntax"
            )
        
        # Check cache
        if self.cache:
            if self.cache.get_and_copy(diagram_code, output_file, format):
                return RenderResult(
                    success=True,
                    output_file=output_file,
                    from_cache=True
                )
        
        # Create temp input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False, encoding='utf-8') as tmp:
            tmp.write(diagram_code)
            tmp_input = Path(tmp.name)
        
        try:
            # Render: dot -Tsvg input.dot -o output.svg
            result = subprocess.run([
                self.dot_exe,
                '-Tsvg',
                str(tmp_input),
                '-o', str(output_file)
            ], capture_output=True, text=True, check=False, timeout=30)
            
            if result.returncode != 0:
                return RenderResult(
                    success=False,
                    error_message=f"Graphviz failed: {result.stderr}"
                )
            
            if not output_file.exists():
                return RenderResult(
                    success=False,
                    error_message="Graphviz did not produce output file"
                )
            
            # Save to cache
            if self.cache:
                self.cache.save(diagram_code, output_file, format)
            
            return RenderResult(
                success=True,
                output_file=output_file,
                from_cache=False
            )
            
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                error_message="Graphviz rendering timed out (30s)"
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error_message=f"Graphviz exception: {str(e)}"
            )
        finally:
            if tmp_input.exists():
                tmp_input.unlink()
    
    def get_supported_formats(self) -> list[DiagramFormat]:
        """Graphviz supports SVG."""
        return [DiagramFormat.SVG]

