"""
Mermaid diagram renderer.
"""
from pathlib import Path
from typing import Optional
import tempfile

from .base import DiagramRenderer, DiagramFormat, RenderResult
from .cache import DiagramCache

# Handle both direct execution and module import
try:
    from external_tools import MermaidCLI, ToolNotFoundError, SvgoCLI
except ImportError:
    from ..external_tools import MermaidCLI, ToolNotFoundError, SvgoCLI


class MermaidRenderer(DiagramRenderer):
    """
    Renderer for Mermaid diagrams.
    
    Supports:
    - All Mermaid diagram types (flowchart, sequence, class, etc.)
    - SVG and PNG output
    - Theme customization
    - Caching for performance
    - Optional SVG optimization
    """
    
    def __init__(
        self,
        cache: Optional[DiagramCache] = None,
        theme_config: Optional[Path] = None,
        optimize_svg: bool = True
    ):
        """
        Initialize Mermaid renderer.
        
        Args:
            cache: Optional DiagramCache for caching rendered diagrams
            theme_config: Optional path to Mermaid theme config JSON
            optimize_svg: If True, optimize SVG output with SVGO (if available)
        """
        # Initialize Mermaid CLI
        try:
            self.mermaid_cli = MermaidCLI()
        except ToolNotFoundError as e:
            raise ToolNotFoundError(
                "Mermaid CLI (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli"
            ) from e
        
        self.cache = cache
        self.theme_config = theme_config
        self.optimize_svg = optimize_svg
        
        # Try to initialize SVGO (optional)
        self.svgo_cli = None
        if optimize_svg:
            try:
                self.svgo_cli = SvgoCLI()
            except ToolNotFoundError:
                # SVGO is optional - just skip optimization
                pass
    
    def can_render(self, diagram_code: str, format_hint: Optional[str] = None) -> bool:
        """Check if this is a Mermaid diagram."""
        if format_hint:
            return format_hint.lower() == 'mermaid'
        
        # Check for Mermaid keywords
        return self.validate(diagram_code)
    
    def validate(self, diagram_code: str) -> bool:
        """Validate Mermaid diagram syntax."""
        return self.mermaid_cli.validate_diagram(diagram_code)
    
    def render(
        self,
        diagram_code: str,
        output_file: Path,
        format: DiagramFormat = DiagramFormat.SVG,
        **options
    ) -> RenderResult:
        """
        Render Mermaid diagram.
        
        Args:
            diagram_code: Mermaid diagram source code
            output_file: Output file path
            format: Output format (SVG or PNG)
            **options: Additional options:
                - theme: str = 'neutral'
                - background: str = 'transparent' (SVG) or 'white' (PNG)
                - scale: float = 1.0 (SVG) or 2.0 (PNG)
                
        Returns:
            RenderResult with success status
        """
        # Validate first
        if not self.validate(diagram_code):
            return RenderResult(
                success=False,
                error_message="Invalid Mermaid syntax: no valid diagram keywords found"
            )
        
        # Check cache first
        if self.cache:
            cache_options = self._get_cache_options(format, options)
            if self.cache.get_and_copy(diagram_code, output_file, format, cache_options):
                return RenderResult(
                    success=True,
                    output_file=output_file,
                    from_cache=True
                )
        
        # Extract options with defaults
        theme = options.get('theme', 'neutral')
        background = options.get('background', 'transparent' if format == DiagramFormat.SVG else 'white')
        scale = options.get('scale', 1.0 if format == DiagramFormat.SVG else 2.0)
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
            tmp.write(diagram_code)
            tmp_input = Path(tmp.name)
        
        try:
            # Render based on format
            if format == DiagramFormat.SVG:
                result = self.mermaid_cli.render_to_svg(
                    tmp_input,
                    output_file,
                    theme=theme,
                    background=background,
                    theme_config=self.theme_config,
                    scale=scale
                )
            else:  # PNG
                result = self.mermaid_cli.render_to_png(
                    tmp_input,
                    output_file,
                    theme=theme,
                    background=background,
                    theme_config=self.theme_config,
                    scale=scale
                )
            
            if not result.success:
                return RenderResult(
                    success=False,
                    error_message=f"Mermaid rendering failed: {result.stderr}"
                )
            
            # Optimize SVG if enabled
            if format == DiagramFormat.SVG and self.optimize_svg and self.svgo_cli:
                self.svgo_cli.optimize(output_file, output_file)
            
            # Save to cache
            if self.cache and output_file.exists():
                cache_options = self._get_cache_options(format, options)
                self.cache.save(diagram_code, output_file, format, cache_options)
            
            return RenderResult(
                success=True,
                output_file=output_file,
                from_cache=False
            )
            
        except Exception as e:
            return RenderResult(
                success=False,
                error_message=f"Mermaid rendering exception: {str(e)}"
            )
        finally:
            # Cleanup temp file
            if tmp_input.exists():
                tmp_input.unlink()
    
    def get_supported_formats(self) -> list[DiagramFormat]:
        """Mermaid supports both SVG and PNG."""
        return [DiagramFormat.SVG, DiagramFormat.PNG]
    
    def _get_cache_options(self, format: DiagramFormat, options: dict) -> dict:
        """
        Extract cache-relevant options.
        
        Only options that affect rendering should be in cache key.
        """
        return {
            'theme': options.get('theme', 'neutral'),
            'background': options.get('background', 'transparent' if format == DiagramFormat.SVG else 'white'),
        }

