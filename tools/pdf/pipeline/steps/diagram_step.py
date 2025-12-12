"""
Diagram rendering pipeline step - NOW WITH FULL MERMAID SUPPORT
Proper integration of DiagramOrchestrator for markdown diagram embedding.
"""
from pathlib import Path
import re
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class DiagramRenderingStep(PipelineStep):
    """
    Render Mermaid diagrams to SVG and embed them inline in markdown.
    
    This step:
    1. Finds all ```mermaid code blocks
    2. Renders each to SVG using MermaidRenderer
    3. Embeds SVG directly in markdown (not just references)
    4. Supports caching and profile-specific theming
    """
    
    def get_name(self) -> str:
        return "Diagram Rendering (Mermaid → SVG)"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure work directory exists"""
        if not context.work_dir.exists():
            context.work_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: PipelineContext) -> bool:
        """Render Mermaid diagrams and embed as SVG in markdown"""
        
        if not context.get_config('enable_diagrams', True):
            self.log("Diagram rendering disabled, skipping", context)
            return True
        
        content = context.preprocessed_markdown
        
        # Check for Mermaid code blocks
        if '```mermaid' not in content:
            self.log("No Mermaid diagrams detected, skipping", context)
            return True
        
        try:
            # Try to render diagrams
            result_markdown, rendered_count = self._render_mermaid_diagrams(
                content, context
            )
            
            if rendered_count > 0:
                context.preprocessed_markdown = result_markdown
                self.log(f"Rendered and embedded {rendered_count} Mermaid diagrams", context)
            else:
                self.log("No valid Mermaid diagrams found to render", context)
            
            return True
            
        except Exception as e:
            self.log(f"ERROR: Diagram rendering failed: {e}", context)
            # Non-critical: Continue without diagrams
            return True
    
    def _render_mermaid_diagrams(self, markdown_content: str, context: PipelineContext) -> tuple:
        """
        Find all mermaid code blocks and render them to embedded SVG.
        
        Returns:
            (modified_markdown, rendered_count)
        """
        from diagram_rendering import MermaidRenderer, DiagramCache, DiagramFormat
        
        # Setup rendering
        cache_dir = context.get_config('cache_dir')
        use_cache = context.get_config('use_cache', True)
        theme_config = context.get_config('theme_config')
        profile = context.get_config('profile')  # For profile-specific theming
        
        cache = DiagramCache(cache_dir) if use_cache and cache_dir else None
        renderer = MermaidRenderer(cache=cache, theme_config=Path(theme_config) if theme_config else None)
        
        # Extract mermaid blocks with their positions
        pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = list(re.finditer(pattern, markdown_content, re.DOTALL))
        
        if not matches:
            return markdown_content, 0
        
        self.log(f"Found {len(matches)} Mermaid diagram blocks", context)
        
        # Render diagrams (reverse order to maintain positions)
        rendered_count = 0
        offset = 0  # Track position shifts as we replace text
        
        for match_idx, match in enumerate(matches):
            diagram_code = match.group(1).strip()
            
            # Validate diagram
            if not renderer.validate(diagram_code):
                self.log(f"  ⚠️  Diagram {match_idx + 1}: Invalid Mermaid syntax, skipping", context)
                continue
            
            # Render to SVG
            svg_file = context.work_dir / f"diagram_{match_idx:03d}.svg"
            
            try:
                result = renderer.render(
                    diagram_code,
                    svg_file,
                    format=DiagramFormat.SVG,
                    theme=self._get_theme_for_profile(profile),
                    background='transparent'
                )
                
                if not result.success:
                    self.log(f"  ⚠️  Diagram {match_idx + 1}: Render failed ({result.error_message})", context)
                    continue
                
                # Read SVG content
                with open(svg_file, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # Wrap SVG in a div with styling
                svg_wrapper = f'''<div class="diagram-container" style="display: flex; justify-content: center; margin: 1.5em 0;">
{svg_content}
</div>'''
                
                # Replace the code block with embedded SVG
                start_pos = match.start() + offset
                end_pos = match.end() + offset
                
                before = markdown_content[:start_pos]
                after = markdown_content[end_pos:]
                markdown_content = before + svg_wrapper + after
                
                # Update offset for next match
                offset += len(svg_wrapper) - (end_pos - start_pos)
                rendered_count += 1
                
                self.log(f"  ✓ Diagram {match_idx + 1}: Rendered to SVG ({svg_file.name})", context)
                
            except Exception as e:
                self.log(f"  ✗ Diagram {match_idx + 1}: Exception - {e}", context)
                continue
        
        return markdown_content, rendered_count
    
    def _get_theme_for_profile(self, profile: str = None) -> str:
        """
        Get Mermaid theme name based on CSS profile.
        Maps docs-pipeline profiles to Mermaid themes.
        """
        theme_map = {
            'tech-whitepaper': 'neutral',      # Clean, professional
            'dark-pro': 'dark',                 # Dark mode optimized
            'enterprise-blue': 'default',       # Corporate standard
            'minimalist': 'neutral',            # Clean and minimal
        }
        
        return theme_map.get(profile, 'neutral')
