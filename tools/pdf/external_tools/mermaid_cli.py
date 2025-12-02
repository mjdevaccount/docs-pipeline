"""
Mermaid CLI wrapper for diagram rendering.
"""
from pathlib import Path
from typing import List, Optional
import platform

from .base import ExternalTool, CommandResult


class MermaidCLI(ExternalTool):
    """
    Mermaid CLI (mmdc) wrapper for rendering diagrams.
    
    Supports rendering Mermaid diagrams to SVG and PNG formats
    with theme customization and quality settings.
    """
    
    def _get_executable_names(self) -> List[str]:
        """Get platform-specific mmdc executable names."""
        if platform.system().lower() == 'windows':
            return ['mmdc.cmd', 'mmdc.exe', 'mmdc']
        return ['mmdc']
    
    def _get_search_paths(self) -> List[Path]:
        """Get common Mermaid CLI installation paths (npm global)."""
        system = platform.system().lower()
        paths = []
        
        if system == 'windows':
            # Windows npm global packages
            paths.extend([
                Path.home() / 'AppData' / 'Roaming' / 'npm',
                Path('C:/Program Files/nodejs'),
            ])
        elif system == 'darwin':  # macOS
            paths.extend([
                Path('/usr/local/bin'),
                Path('/opt/homebrew/bin'),
                Path.home() / '.npm-global' / 'bin',
            ])
        else:  # Linux
            paths.extend([
                Path('/usr/local/bin'),
                Path('/usr/bin'),
                Path.home() / '.npm-global' / 'bin',
                Path.home() / '.local' / 'bin',
            ])
        
        return paths
    
    def render_to_svg(
        self,
        input_file: Path,
        output_file: Path,
        theme: str = 'neutral',
        background: str = 'transparent',
        theme_config: Optional[Path] = None,
        scale: float = 1.0
    ) -> CommandResult:
        """
        Render Mermaid diagram to SVG.
        
        Args:
            input_file: Input .mmd file with Mermaid code
            output_file: Output .svg file
            theme: Mermaid theme ('default', 'neutral', 'dark', 'forest', 'base')
            background: Background color ('transparent', 'white', etc.)
            theme_config: Optional path to theme config JSON file
            scale: Scale factor for output
            
        Returns:
            CommandResult with execution details
        """
        args = [
            '-i', str(input_file),
            '-o', str(output_file),
            '-t', theme,
            '-b', background
        ]
        
        if theme_config and theme_config.exists():
            args.extend(['-c', str(theme_config)])
        
        if scale != 1.0:
            args.extend(['-s', str(scale)])
        
        return self.execute(args, check=False, shell=(platform.system().lower() == 'windows'))
    
    def render_to_png(
        self,
        input_file: Path,
        output_file: Path,
        theme: str = 'neutral',
        background: str = 'white',
        theme_config: Optional[Path] = None,
        scale: float = 2.0
    ) -> CommandResult:
        """
        Render Mermaid diagram to PNG (high resolution).
        
        Args:
            input_file: Input .mmd file
            output_file: Output .png file
            theme: Mermaid theme
            background: Background color (recommended: 'white' for PNG)
            theme_config: Optional theme config JSON
            scale: Scale factor (2.0 = high res, good for printing)
            
        Returns:
            CommandResult with execution details
        """
        args = [
            '-i', str(input_file),
            '-o', str(output_file),
            '-t', theme,
            '-b', background,
            '-s', str(scale)
        ]
        
        if theme_config and theme_config.exists():
            args.extend(['-c', str(theme_config)])
        
        return self.execute(args, check=False, shell=(platform.system().lower() == 'windows'))
    
    def validate_diagram(self, mermaid_code: str) -> bool:
        """
        Validate that mermaid code contains valid diagram syntax.
        
        Args:
            mermaid_code: Mermaid diagram source code
            
        Returns:
            True if code contains valid Mermaid keywords, False otherwise
        """
        mermaid_keywords = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'journey', 'gantt', 'pie',
            'gitGraph', 'mindmap', 'timeline', 'C4Context', 'C4Container'
        ]
        
        # Check if code starts with image reference (invalid)
        if mermaid_code.strip().startswith('!['):
            return False
        
        # Check if any valid keyword is present
        return any(keyword in mermaid_code for keyword in mermaid_keywords)

