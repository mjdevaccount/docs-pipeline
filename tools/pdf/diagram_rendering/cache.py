"""
Diagram caching system for performance optimization.

Includes cache metrics tracking for visibility into performance gains.
"""
import hashlib
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from .base import DiagramFormat


@dataclass
class CacheStats:
    """
    Track cache performance metrics.
    
    Provides visibility into caching effectiveness:
    - Hit ratio (% of diagrams served from cache)
    - Time saved (ms)
    - Size reduction (% smaller than original)
    - Number of diagrams cached vs rendered
    """
    hits: int = 0
    misses: int = 0
    time_saved_ms: float = 0.0
    total_original_size_bytes: int = 0
    total_cached_size_bytes: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Cache hit ratio (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def total_size_reduction_bytes(self) -> int:
        """Total bytes saved by caching."""
        return self.total_original_size_bytes - self.total_cached_size_bytes
    
    @property
    def size_reduction_percent(self) -> float:
        """Size reduction percentage from caching."""
        if self.total_original_size_bytes == 0:
            return 0.0
        return (self.total_size_reduction_bytes / self.total_original_size_bytes) * 100
    
    def record_cache_hit(self, original_size: int, cached_size: int, render_time_estimate_ms: float = 500.0):
        """Record a cache hit."""
        self.hits += 1
        self.time_saved_ms += render_time_estimate_ms  # Estimated time that would have been spent rendering
        self.total_original_size_bytes += original_size
        self.total_cached_size_bytes += cached_size
    
    def record_cache_miss(self, result_size: int):
        """Record a cache miss (new render)."""
        self.misses += 1
        self.total_original_size_bytes += result_size
        self.total_cached_size_bytes += result_size
    
    def report(self) -> str:
        """Generate human-readable cache report."""
        total = self.hits + self.misses
        if total == 0:
            return "[INFO] No diagrams cached."
        
        return f"""\
[INFO] Cache Performance Report
         Hit Ratio: {self.hit_ratio:.1%} ({self.hits}/{total})
         Time Saved: {self.time_saved_ms:.0f}ms
         Size Reduction: {self.size_reduction_percent:.1f}%"""


class DiagramCache:
    """
    File-based cache for rendered diagrams.
    
    Single Responsibility:
    - Store rendered diagrams to disk
    - Retrieve cached diagrams by content hash
    - Manage cache directory
    - Track cache performance metrics
    
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
        
        # Initialize cache stats
        self.stats = CacheStats()
    
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
        
        Tracks cache hits for metrics.
        
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
            
            # Track cache hit
            original_size = len(diagram_code.encode())
            cached_size = cached_file.stat().st_size
            self.stats.record_cache_hit(original_size, cached_size)
            
            return True
        
        return False
    
    def record_miss(self, result_file: Path):
        """
        Record a cache miss (diagram was newly rendered).
        
        Args:
            result_file: Path to newly rendered diagram file
        """
        if result_file.exists():
            file_size = result_file.stat().st_size
            self.stats.record_cache_miss(file_size)
    
    def clear(self) -> int:
        """
        Clear all cached diagrams and reset stats.
        
        Returns:
            Number of files deleted
        """
        count = 0
        if self.cache_dir.exists():
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    file.unlink()
                    count += 1
        
        # Reset stats
        self.stats = CacheStats()
        
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
