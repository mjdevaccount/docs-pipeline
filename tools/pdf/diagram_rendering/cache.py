"""
Diagram caching system for performance optimization.
"""
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .base import DiagramFormat


class DiagramCache:
    """
    File-based cache for rendered diagrams.
    
    Single Responsibility:
    - Store rendered diagrams to disk
    - Retrieve cached diagrams by content hash
    - Manage cache directory
    
    Cache key is MD5 hash of:
    - Diagram source code
    - Output format (SVG/PNG)
    - Renderer-specific options (for cache invalidation)
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory for cached diagrams.
                      If None, uses default: pdf-tools/output/pdf-diagrams/
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default: pdf-tools/output/pdf-diagrams/
            from pathlib import Path
            self.cache_dir = Path(__file__).parent.parent / 'output' / 'pdf-diagrams'
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _compute_hash(
        self,
        diagram_code: str,
        format: DiagramFormat,
        options: Optional[dict] = None
    ) -> str:
        """
        Compute cache key hash.
        
        Args:
            diagram_code: Diagram source code
            format: Output format
            options: Optional renderer-specific options
            
        Returns:
            8-character hex hash for cache key
        """
        # Include format and options in hash for proper cache invalidation
        cache_key = diagram_code + format.value
        if options:
            # Sort options for consistent hashing
            options_str = str(sorted(options.items()))
            cache_key += options_str
        
        return hashlib.md5(cache_key.encode()).hexdigest()[:8]
    
    def get(
        self,
        diagram_code: str,
        format: DiagramFormat,
        options: Optional[dict] = None
    ) -> Optional[Path]:
        """
        Retrieve cached diagram if available.
        
        Args:
            diagram_code: Diagram source code
            format: Output format
            options: Optional renderer-specific options
            
        Returns:
            Path to cached file if exists, None otherwise
        """
        cache_hash = self._compute_hash(diagram_code, format, options)
        cached_file = self.cache_dir / f'{cache_hash}.{format.value}'
        
        if cached_file.exists():
            return cached_file
        
        return None
    
    def save(
        self,
        diagram_code: str,
        source_file: Path,
        format: DiagramFormat,
        options: Optional[dict] = None
    ) -> Path:
        """
        Save rendered diagram to cache.
        
        Args:
            diagram_code: Diagram source code
            source_file: Path to rendered diagram file
            format: Output format
            options: Optional renderer-specific options
            
        Returns:
            Path to cached file
        """
        cache_hash = self._compute_hash(diagram_code, format, options)
        cached_file = self.cache_dir / f'{cache_hash}.{format.value}'
        
        # Copy to cache
        shutil.copy2(source_file, cached_file)
        
        return cached_file
    
    def get_and_copy(
        self,
        diagram_code: str,
        output_file: Path,
        format: DiagramFormat,
        options: Optional[dict] = None
    ) -> bool:
        """
        Get cached diagram and copy to output location.
        
        Args:
            diagram_code: Diagram source code
            output_file: Destination file path
            format: Output format
            options: Optional renderer-specific options
            
        Returns:
            True if found in cache and copied, False otherwise
        """
        cached_file = self.get(diagram_code, format, options)
        
        if cached_file:
            shutil.copy2(cached_file, output_file)
            return True
        
        return False
    
    def clear(self) -> int:
        """
        Clear all cached diagrams.
        
        Returns:
            Number of files deleted
        """
        count = 0
        if self.cache_dir.exists():
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    file.unlink()
                    count += 1
        return count
    
    def get_size(self) -> Tuple[int, int]:
        """
        Get cache statistics.
        
        Returns:
            Tuple of (file_count, total_bytes)
        """
        count = 0
        total_bytes = 0
        
        if self.cache_dir.exists():
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    count += 1
                    total_bytes += file.stat().st_size
        
        return count, total_bytes

