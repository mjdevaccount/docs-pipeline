"""
Base abstraction for external command-line tools.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import subprocess


class ToolNotFoundError(Exception):
    """Raised when an external tool executable cannot be found."""
    pass


@dataclass
class CommandResult:
    """Result of executing an external command."""
    returncode: int
    stdout: str
    stderr: str
    success: bool
    
    @property
    def failed(self) -> bool:
        """Check if command failed."""
        return not self.success


class ExternalTool(ABC):
    """
    Abstract base class for external command-line tool wrappers.
    
    Provides:
    - Platform-independent executable resolution
    - Consistent command execution interface
    - Error handling
    - Testability (can be mocked)
    """
    
    def __init__(self, executable_path: Optional[str] = None):
        """
        Initialize tool wrapper.
        
        Args:
            executable_path: Optional explicit path to executable.
                           If None, will search common locations.
        """
        self._executable = executable_path or self._find_executable()
        if not self._executable:
            raise ToolNotFoundError(
                f"{self.__class__.__name__}: Executable not found. "
                f"Searched: {self._get_search_paths()}"
            )
    
    @property
    def executable(self) -> str:
        """Get path to executable."""
        return self._executable
    
    @abstractmethod
    def _get_executable_names(self) -> List[str]:
        """
        Get list of possible executable names (platform-specific).
        
        Returns:
            List of executable names to search for.
            Example: ['pandoc.exe', 'pandoc'] for Windows
        """
        pass
    
    @abstractmethod
    def _get_search_paths(self) -> List[Path]:
        """
        Get list of paths to search for executable.
        
        Returns:
            List of paths to check (in order of priority).
        """
        pass
    
    def _find_executable(self) -> Optional[str]:
        """
        Find executable in search paths or system PATH.
        
        Returns:
            Path to executable if found, None otherwise.
        """
        import shutil
        
        # First check explicit search paths
        for search_path in self._get_search_paths():
            for exe_name in self._get_executable_names():
                candidate = search_path / exe_name
                if candidate.exists() and candidate.is_file():
                    return str(candidate)
        
        # Fallback to system PATH
        for exe_name in self._get_executable_names():
            found = shutil.which(exe_name)
            if found:
                return found
        
        return None
    
    def execute(
        self,
        args: List[str],
        input_text: Optional[str] = None,
        timeout: Optional[int] = None,
        check: bool = True,
        shell: bool = False,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Execute the tool with given arguments.
        
        Args:
            args: Command arguments (executable will be prepended)
            input_text: Optional stdin input
            timeout: Optional timeout in seconds
            check: If True, raise exception on non-zero exit code
            shell: If True, run command through shell
            cwd: Optional working directory
            env: Optional environment variables
            
        Returns:
            CommandResult with execution details
            
        Raises:
            subprocess.CalledProcessError: If check=True and command fails
            subprocess.TimeoutExpired: If timeout exceeded
        """
        cmd = [self._executable] + args
        
        try:
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check,
                shell=shell,
                cwd=cwd,
                env=env
            )
            
            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                success=(result.returncode == 0)
            )
            
        except subprocess.CalledProcessError as e:
            return CommandResult(
                returncode=e.returncode,
                stdout=e.stdout or '',
                stderr=e.stderr or '',
                success=False
            )
    
    def is_available(self) -> bool:
        """
        Check if tool is available and working.
        
        Returns:
            True if tool can be executed, False otherwise.
        """
        try:
            # Try running with --version or --help
            version_flags = ['--version', '-v', '--help', '-h']
            for flag in version_flags:
                try:
                    result = self.execute([flag], timeout=5, check=False)
                    if result.success:
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(executable='{self._executable}')"

