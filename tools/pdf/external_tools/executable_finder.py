"""
Platform-independent executable finder utility.
"""
from pathlib import Path
from typing import List, Optional
import platform
import os


class ExecutableFinder:
    """
    Utility class for finding executables across platforms.
    
    Handles:
    - Platform-specific executable extensions (.exe on Windows)
    - Common installation locations per platform
    - Environment variable expansion
    - User home directory resolution
    """
    
    @staticmethod
    def get_platform_executables(base_name: str) -> List[str]:
        """
        Get platform-specific executable names.
        
        Args:
            base_name: Base executable name (e.g., 'pandoc')
            
        Returns:
            List of possible executable names for current platform.
            Example on Windows: ['pandoc.exe', 'pandoc.cmd', 'pandoc']
        """
        system = platform.system().lower()
        
        if system == 'windows':
            return [
                f'{base_name}.exe',
                f'{base_name}.cmd',
                f'{base_name}.bat',
                base_name
            ]
        else:
            return [base_name]
    
    @staticmethod
    def get_common_install_paths(tool_name: str) -> List[Path]:
        """
        Get common installation paths for a tool based on platform.
        
        Args:
            tool_name: Name of the tool (e.g., 'Pandoc', 'Node')
            
        Returns:
            List of common installation directories for current platform.
        """
        system = platform.system().lower()
        paths = []
        
        if system == 'windows':
            # Windows common locations
            paths.extend([
                Path(f'C:/Program Files/{tool_name}'),
                Path(f'C:/Program Files (x86)/{tool_name}'),
                Path.home() / 'AppData' / 'Local' / tool_name,
                Path.home() / 'AppData' / 'Roaming' / tool_name,
            ])
            
            # Node.js global npm packages (for mermaid-cli, katex, etc.)
            if tool_name.lower() in ['npm', 'node']:
                npm_path = Path.home() / 'AppData' / 'Roaming' / 'npm'
                paths.append(npm_path)
        
        elif system == 'darwin':  # macOS
            # macOS common locations
            paths.extend([
                Path('/usr/local/bin'),
                Path('/opt/homebrew/bin'),
                Path(f'/Applications/{tool_name}.app/Contents/MacOS'),
                Path.home() / 'Applications' / f'{tool_name}.app' / 'Contents' / 'MacOS',
                Path.home() / '.local' / 'bin',
            ])
        
        elif system == 'linux':
            # Linux common locations
            paths.extend([
                Path('/usr/bin'),
                Path('/usr/local/bin'),
                Path('/opt/bin'),
                Path.home() / '.local' / 'bin',
            ])
        
        # Common to all platforms
        paths.extend([
            Path.home() / 'bin',
            Path.home() / '.bin',
        ])
        
        return [p for p in paths if p.exists()]
    
    @staticmethod
    def find_executable(
        base_name: str,
        search_paths: Optional[List[Path]] = None,
        use_path: bool = True
    ) -> Optional[str]:
        """
        Find executable in search paths or system PATH.
        
        Args:
            base_name: Base executable name (e.g., 'pandoc')
            search_paths: Optional list of directories to search
            use_path: If True, also search system PATH
            
        Returns:
            Full path to executable if found, None otherwise.
        """
        import shutil
        
        exe_names = ExecutableFinder.get_platform_executables(base_name)
        
        # Search explicit paths first
        if search_paths:
            for search_dir in search_paths:
                if not search_dir.exists():
                    continue
                    
                for exe_name in exe_names:
                    candidate = search_dir / exe_name
                    if candidate.exists() and candidate.is_file():
                        return str(candidate.resolve())
        
        # Fallback to system PATH
        if use_path:
            for exe_name in exe_names:
                found = shutil.which(exe_name)
                if found:
                    return found
        
        return None
    
    @staticmethod
    def expand_path(path: str) -> Path:
        """
        Expand environment variables and user home in path.
        
        Args:
            path: Path string potentially containing ~ or env vars
            
        Returns:
            Expanded Path object
        """
        expanded = os.path.expandvars(os.path.expanduser(path))
        return Path(expanded)

