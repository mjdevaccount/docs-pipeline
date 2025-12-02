"""
KaTeX CLI wrapper for math rendering.
"""
from pathlib import Path
from typing import List, Optional
import platform

from .base import ExternalTool, CommandResult


class KatexCLI(ExternalTool):
    """
    KaTeX CLI wrapper for server-side math rendering.
    
    Converts LaTeX math expressions to HTML for embedding in documents.
    """
    
    def _get_executable_names(self) -> List[str]:
        """Get platform-specific katex executable names."""
        if platform.system().lower() == 'windows':
            return ['katex.cmd', 'katex.exe', 'katex']
        return ['katex']
    
    def _get_search_paths(self) -> List[Path]:
        """Get common KaTeX installation paths (npm global)."""
        system = platform.system().lower()
        paths = []
        
        if system == 'windows':
            paths.extend([
                Path.home() / 'AppData' / 'Roaming' / 'npm',
                Path('C:/Program Files/nodejs'),
            ])
        elif system == 'darwin':
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
    
    def render_inline(self, latex_code: str, timeout: int = 5) -> Optional[str]:
        """
        Render inline math to HTML.
        
        Args:
            latex_code: LaTeX math expression (without $ delimiters)
            timeout: Execution timeout in seconds
            
        Returns:
            Rendered HTML string, or None if rendering failed
        """
        result = self.execute(
            [],
            input_text=latex_code,
            timeout=timeout,
            check=False
        )
        
        if result.success:
            return result.stdout.strip()
        return None
    
    def render_display(self, latex_code: str, timeout: int = 5) -> Optional[str]:
        """
        Render display math (block) to HTML.
        
        Args:
            latex_code: LaTeX math expression (without $$ delimiters)
            timeout: Execution timeout in seconds
            
        Returns:
            Rendered HTML string, or None if rendering failed
        """
        result = self.execute(
            ['--display-mode'],
            input_text=latex_code,
            timeout=timeout,
            check=False
        )
        
        if result.success:
            return result.stdout.strip()
        return None

