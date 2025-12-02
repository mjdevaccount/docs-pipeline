"""
SVGO wrapper for SVG optimization.
"""
from pathlib import Path
from typing import List, Optional
import platform

from .base import ExternalTool, CommandResult


class SvgoCLI(ExternalTool):
    """
    SVGO (SVG Optimizer) wrapper.
    
    Optimizes SVG files by removing unnecessary metadata and
    reducing file size by 30-50% without quality loss.
    """
    
    def _get_executable_names(self) -> List[str]:
        """Get platform-specific svgo executable names."""
        if platform.system().lower() == 'windows':
            return ['svgo.cmd', 'svgo.exe', 'svgo']
        return ['svgo']
    
    def _get_search_paths(self) -> List[Path]:
        """Get common SVGO installation paths (npm global)."""
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
    
    def optimize(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        multipass: bool = True,
        timeout: int = 10
    ) -> CommandResult:
        """
        Optimize SVG file.
        
        Args:
            input_file: Input SVG file
            output_file: Output file (if None, optimizes in-place)
            multipass: Enable multipass optimization for better results
            timeout: Execution timeout in seconds
            
        Returns:
            CommandResult with execution details
        """
        if output_file is None:
            output_file = input_file
        
        args = [
            '--input', str(input_file),
            '--output', str(output_file)
        ]
        
        if multipass:
            args.append('--multipass')
        
        return self.execute(args, timeout=timeout, check=False)
    
    def is_available(self) -> bool:
        """
        Check if SVGO is available.
        
        SVGO is optional - if not available, diagrams will work
        but won't be optimized.
        
        Returns:
            True if SVGO can be executed
        """
        try:
            result = self.execute(['--version'], timeout=5, check=False)
            return result.success
        except:
            return False

