"""
Diagram rendering orchestrator.

Coordinates multiple diagram renderers and selects the appropriate one
for each diagram based on content and format hints.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import hashlib

from .base import DiagramRenderer, DiagramFormat, RenderResult
from .cache import DiagramCache
from .mermaid import MermaidRenderer
from .plantuml import PlantUMLRenderer
from .graphviz import GraphvizRenderer


class DiagramOrchestrator:
    """
    Orchestrates multiple diagram renderers.
    
    Responsibilities:
    1. Maintain list of available renderers
    2. Select appropriate renderer for each diagram
    3. Process markdown content to find and render all diagrams
    4. Replace diagram code blocks with image references
    5. Coordinate caching across all renderers
    6. Track cache performance metrics
    
    Follows Open/Closed Principle:
    - Add new diagram types by registering new renderer
    - No modification to orchestrator code needed
    """
    
    def __init__(
        self,
        cache: Optional[DiagramCache] = None,
        theme_config: Optional[Path] = None,
        optimize_svg: bool = True,
        plantuml_jar: Optional[Path] = None
    ):
        """
        Initialize orchestrator with default renderers.
        
        Args:
            cache: Optional shared cache for all renderers
            theme_config: Optional Mermaid theme config
            optimize_svg: Enable SVG optimization (SVGO)
            plantuml_jar: Optional path to plantuml.jar
        """
        self.cache = cache or DiagramCache()
        self.renderers: List[DiagramRenderer] = []
        
        # Register default renderers
        # Order matters - first match wins
        try:
            self.register_renderer(
                MermaidRenderer(
                    cache=self.cache,
                    theme_config=theme_config,
                    optimize_svg=optimize_svg
                )
            )
        except Exception as e:
            print(f"    [WARN] Mermaid renderer not available: {e}")
        
        try:
            self.register_renderer(
                PlantUMLRenderer(cache=self.cache, plantuml_jar=plantuml_jar)
            )
        except Exception as e:
            # PlantUML is optional
            pass
        
        try:
            self.register_renderer(GraphvizRenderer(cache=self.cache))
        except Exception as e:
            # Graphviz is optional
            pass
    
    def register_renderer(self, renderer: DiagramRenderer) -> None:
        """
        Register a diagram renderer.
        
        Args:
            renderer: DiagramRenderer instance to register
        """
        self.renderers.append(renderer)
    
    def find_renderer(
        self,
        diagram_code: str,
        format_hint: Optional[str] = None
    ) -> Optional[DiagramRenderer]:
        """
        Find appropriate renderer for diagram.
        
        Args:
            diagram_code: Diagram source code
            format_hint: Optional format hint (e.g., 'mermaid')
            
        Returns:
            Appropriate DiagramRenderer or None if not found
        """
        for renderer in self.renderers:
            if renderer.can_render(diagram_code, format_hint):
                return renderer
        return None
    
    def render_diagram(
        self,
        diagram_code: str,
        output_file: Path,
        format_hint: Optional[str] = None,
        output_format: DiagramFormat = DiagramFormat.SVG,
        **options
    ) -> RenderResult:
        """
        Render a single diagram using appropriate renderer.
        
        Tracks cache hits/misses in cache.stats.
        
        Args:
            diagram_code: Diagram source code
            output_file: Output file path
            format_hint: Optional format hint
            output_format: Output format (SVG/PNG)
            **options: Renderer-specific options
            
        Returns:
            RenderResult with success status
        """
        renderer = self.find_renderer(diagram_code, format_hint)
        
        if not renderer:
            return RenderResult(
                success=False,
                error_message=f"No renderer found for diagram (hint: {format_hint})"
            )
        
        # Try to get from cache first
        if self.cache.get_and_copy(diagram_code, output_file, output_format, options):
            # Cache hit - metrics already tracked in get_and_copy()
            return RenderResult(success=True)
        
        # Cache miss - render new
        result = renderer.render(diagram_code, output_file, output_format, **options)
        
        # Track cache miss if successful
        if result.success and output_file.exists():
            self.cache.record_miss(output_file)
        
        return result
    
    def process_markdown(
        self,
        md_content: str,
        work_dir: Path,
        output_format: DiagramFormat = DiagramFormat.SVG,
        **options
    ) -> tuple[str, List[Path]]:
        """
        Process markdown content: find diagrams, render them, replace with image refs.
        
        Args:
            md_content: Markdown content with diagram code blocks
            work_dir: Working directory for output files
            output_format: Output format (SVG or PNG)
            **options: Renderer-specific options
            
        Returns:
            Tuple of (modified_markdown, list_of_rendered_files)
        """
        rendered_files = []
        
        # Pattern to match code blocks with optional language hint
        # Matches: ```mermaid ... ```, ```plantuml ... ```, ```dot ... ```
        pattern = r'```(mermaid|plantuml|dot|graphviz)\n(.+?)```'
        
        def replace_diagram(match):
            format_hint = match.group(1)
            diagram_code = match.group(2).strip()
            
            # Generate unique filename
            code_hash = hashlib.md5(diagram_code.encode()).hexdigest()[:8]
            output_file = work_dir / f'diagram_{format_hint}_{code_hash}.{output_format.value}'
            
            # Render diagram
            result = self.render_diagram(
                diagram_code,
                output_file,
                format_hint=format_hint,
                output_format=output_format,
                **options
            )
            
            if result.success:
                rendered_files.append(output_file)
                # Return markdown image reference
                return f'![Diagram]({output_file.name})'
            else:
                # Return error placeholder
                error_preview = diagram_code[:50].replace('\n', ' ')
                print(f"    ! Warning: {format_hint} diagram failed: {result.error_message}")
                return f'```\n[{format_hint} diagram error: {error_preview}...]\n```'
        
        # Process all diagrams
        md_with_images = re.sub(pattern, replace_diagram, md_content, flags=re.DOTALL)
        
        return md_with_images, rendered_files
    
    def get_available_renderers(self) -> List[str]:
        """
        Get list of available renderer names.
        
        Returns:
            List of renderer names
        """
        return [renderer.get_name() for renderer in self.renderers]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        file_count, total_bytes = self.cache.get_size()
        return {
            'cache_dir': str(self.cache.cache_dir),
            'file_count': file_count,
            'total_bytes': total_bytes,
            'total_mb': round(total_bytes / (1024 * 1024), 2)
        }
    
    def get_cache_metrics_report(self) -> str:
        """
        Get formatted cache metrics report.
        
        Returns:
            Human-readable cache report
        """
        return self.cache.stats.report()
