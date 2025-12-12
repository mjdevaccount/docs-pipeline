"""
Diagram rendering pipeline step - FULL MERMAID SUPPORT
Proper integration of MermaidRenderer for markdown diagram embedding.
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
    2. Renders each to SVG using MermaidRenderer (mmdc CLI)
    3. Embeds SVG directly in markdown (replaces code blocks)
    4. Supports caching and profile-specific theming
    
    Features:
    - Works with or without diagram_rendering module
    - Fallback to subprocess mermaid-cli if available
    - Profile-aware theme selection
    - Verbose logging for debugging
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
        
        Strategy:
        1. Find all ```mermaid blocks
        2. For each block, render to SVG file
        3. Replace code block with embedded SVG HTML
        4. Return modified markdown
        
        Returns:
            (modified_markdown, rendered_count)
        """
        
        # Extract all mermaid blocks
        diagram_blocks = self._extract_mermaid_blocks(markdown_content)
        
        if not diagram_blocks:
            self.log("No valid Mermaid code blocks found", context)
            return markdown_content, 0
        
        self.log(f"Found {len(diagram_blocks)} Mermaid diagram blocks", context)
        
        # Process each diagram block
        rendered_count = 0
        result = markdown_content
        
        # Process in reverse order to maintain position indices
        for idx, (start, end, diagram_code) in enumerate(reversed(diagram_blocks)):
            actual_idx = len(diagram_blocks) - 1 - idx
            
            # Render this diagram
            svg_content = self._render_single_diagram(
                diagram_code, actual_idx, context
            )
            
            if svg_content:
                # Wrap SVG in div
                svg_wrapper = f'''<div class="diagram-container" style="display: flex; justify-content: center; margin: 1.5em 0;">
{svg_content}
</div>'''
                
                # Replace code block with SVG
                result = result[:start] + svg_wrapper + result[end:]
                rendered_count += 1
                self.log(f"  ✓ Diagram {actual_idx + 1}: Rendered to SVG", context)
            else:
                self.log(f"  ✗ Diagram {actual_idx + 1}: Render failed, keeping code block", context)
        
        return result, rendered_count
    
    def _extract_mermaid_blocks(self, content: str) -> list:
        """
        Extract all ```mermaid code blocks from markdown.
        
        Returns:
            List of (start_pos, end_pos, code) tuples
        """
        blocks = []
        pattern = r'```mermaid\s*\n(.*?)\n```'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            code = match.group(1).strip()
            if code:  # Only include non-empty blocks
                blocks.append((
                    match.start(),
                    match.end(),
                    code
                ))
        
        return blocks
    
    def _render_single_diagram(self, diagram_code: str, idx: int, context: PipelineContext) -> str:
        """
        Render a single Mermaid diagram to SVG.
        
        Returns SVG content as string, or None if render failed.
        """
        svg_file = context.work_dir / f"diagram_{idx:03d}.svg"
        
        try:
            # Try using diagram_rendering module first
            return self._render_with_module(diagram_code, svg_file, context)
        except Exception as e:
            self.log(f"    Module render failed: {e}, trying subprocess...", context)
            try:
                return self._render_with_subprocess(diagram_code, svg_file, context)
            except Exception as e2:
                self.log(f"    Subprocess render failed: {e2}", context)
                return None
    
    def _render_with_module(self, code: str, svg_file: Path, context: PipelineContext) -> str:
        """
        Render using diagram_rendering.MermaidRenderer module.
        """
        from diagram_rendering import MermaidRenderer, DiagramCache, DiagramFormat
        
        # Setup rendering
        cache_dir = context.get_config('cache_dir')
        use_cache = context.get_config('use_cache', True)
        theme_config = context.get_config('theme_config')
        profile = context.get_config('profile')
        
        cache = DiagramCache(cache_dir) if use_cache and cache_dir else None
        renderer = MermaidRenderer(
            cache=cache,
            theme_config=Path(theme_config) if theme_config else None
        )
        
        # Render
        result = renderer.render(
            code,
            svg_file,
            format=DiagramFormat.SVG,
            theme=self._get_theme_for_profile(profile),
            background='transparent'
        )
        
        if not result.success:
            raise Exception(f"MermaidRenderer failed: {result.error_message}")
        
        # Read and return SVG content
        with open(svg_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _render_with_subprocess(self, code: str, svg_file: Path, context: PipelineContext) -> str:
        """
        Render using mermaid-cli (mmdc) subprocess as fallback.
        """
        import subprocess
        import tempfile
        
        # Write diagram code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
            f.write(code)
            mmd_file = Path(f.name)
        
        try:
            # Call mermaid-cli
            profile = context.get_config('profile')
            theme = self._get_theme_for_profile(profile)
            
            cmd = [
                'mmdc',
                '--input', str(mmd_file),
                '--output', str(svg_file),
                '--theme', theme,
                '--backgroundColor', 'transparent'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"mmdc failed: {result.stderr}")
            
            if not svg_file.exists():
                raise Exception(f"SVG file not created: {svg_file}")
            
            # Read and return SVG content
            with open(svg_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        finally:
            # Cleanup temp file
            if mmd_file.exists():
                mmd_file.unlink()
    
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
