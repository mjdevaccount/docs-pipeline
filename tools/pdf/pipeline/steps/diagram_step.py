"""
Diagram rendering pipeline step.
Wraps DiagramOrchestrator for pluggable diagram rendering.
"""
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class DiagramRenderingStep(PipelineStep):
    """
    Render all diagrams (Mermaid, PlantUML, Graphviz) to SVG/PNG.
    Uses DiagramOrchestrator for SOLID-compliant rendering.
    """
    
    def get_name(self) -> str:
        return "Diagram Rendering"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure work directory exists"""
        if not context.work_dir.exists():
            context.work_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: PipelineContext) -> bool:
        """Render diagrams using DiagramOrchestrator"""
        if not context.get_config('enable_diagrams', True):
            self.log("Diagram rendering disabled, skipping", context)
            return True
        
        # Check if there are any diagrams to render
        content = context.preprocessed_markdown
        has_diagrams = any(marker in content for marker in [
            '```mermaid', '```plantuml', '```graphviz', '```dot'
        ])
        
        if not has_diagrams:
            self.log("No diagrams detected, skipping", context)
            return True
        
        try:
            # Try new architecture first
            try:
                from diagram_rendering import DiagramOrchestrator, DiagramCache, DiagramFormat
                
                # Get configuration
                cache_dir = context.get_config('cache_dir')
                use_cache = context.get_config('use_cache', True)
                theme_config = context.get_config('theme_config')
                also_png = context.get_config('also_png', False)
                
                # Setup cache
                cache = DiagramCache(cache_dir) if use_cache and cache_dir else None
                
                # Create orchestrator
                orchestrator = DiagramOrchestrator(
                    cache=cache,
                    theme_config=Path(theme_config) if theme_config else None,
                    optimize_svg=True
                )
                
                # Render diagrams
                output_format = DiagramFormat.PNG if also_png else DiagramFormat.SVG
                md_with_diagrams, rendered_files = orchestrator.process_markdown(
                    context.preprocessed_markdown,
                    context.work_dir,
                    output_format=output_format
                )
                
                # Update context
                context.preprocessed_markdown = md_with_diagrams
                context.svg_files = rendered_files
                
                self.log(f"Rendered {len(rendered_files)} diagrams", context)
                return True
                
            except ImportError:
                # Fallback to legacy render_all_diagrams
                self.log("Using legacy diagram rendering", context)
                return self._legacy_render(context)
            
        except Exception as e:
            raise PipelineError(f"Diagram rendering failed: {e}")
    
    def _legacy_render(self, context: PipelineContext) -> bool:
        """Fallback to legacy render_all_diagrams function"""
        try:
            from convert_final import render_all_diagrams
            
            md_with_diagrams, svg_files = render_all_diagrams(
                context.preprocessed_markdown,
                context.work_dir,
                also_png=context.get_config('also_png', False),
                cache_dir=context.get_config('cache_dir'),
                use_cache=context.get_config('use_cache', True),
                theme_config=context.get_config('theme_config')
            )
            
            context.preprocessed_markdown = md_with_diagrams
            context.svg_files = svg_files
            
            self.log(f"Rendered {len(svg_files)} diagrams (legacy)", context)
            return True
            
        except ImportError as e:
            self.log(f"WARNING: Legacy diagram rendering not available: {e}", context)
            return True  # Non-critical

