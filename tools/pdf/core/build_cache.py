"""
Incremental Build Cache System
===============================

Tracks document dependencies and only re-renders what changed:
- Detects modified source files
- Tracks diagram code changes
- Invalidates dependent diagrams
- Speeds up large multi-file builds

Usage:
    from core.build_cache import BuildCache
    
    cache = BuildCache()
    
    # Check if rebuild needed
    if cache.needs_rebuild('document.md'):
        # Rebuild document
        convert_document('document.md', 'output.pdf')
        # Save state
        cache.record_build('document.md', {'diagrams': [...]}, 'output.pdf')
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, List, Set, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileHash:
    """Track file content and modification time."""
    path: str
    content_hash: str  # MD5 of file content
    mod_time: float    # File modification time
    size: int          # File size in bytes
    
    def is_modified(self, other_file: Path) -> bool:
        """Check if file has been modified since this hash."""
        if not other_file.exists():
            return True
        
        current_stat = other_file.stat()
        if current_stat.st_mtime != self.mod_time:
            return True
        
        if current_stat.st_size != self.size:
            return True
        
        # Also check content hash for safety
        current_hash = self._compute_hash(other_file)
        return current_hash != self.content_hash
    
    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        """Compute MD5 hash of file content."""
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except IOError:
            return ''


@dataclass
class DiagramDependency:
    """Track diagram source code and dependencies."""
    diagram_id: str          # Unique ID for diagram
    source_code: str         # Diagram source code
    source_hash: str         # MD5 of source code
    format_type: str         # 'mermaid', 'plantuml', 'graphviz'
    output_format: str       # 'svg', 'png'
    output_file: str         # Path to generated file
    dependencies: List[str] = field(default_factory=list)  # Paths of dependent files
    rendered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    render_time_ms: float = 0.0
    output_size_bytes: int = 0
    
    def needs_rerender(self, new_source: str) -> bool:
        """Check if diagram needs re-rendering."""
        new_hash = hashlib.md5(new_source.encode()).hexdigest()
        return new_hash != self.source_hash


@dataclass
class BuildRecord:
    """Record of a successful build."""
    input_file: str                          # Input markdown file
    output_file: str                         # Output PDF/DOCX/HTML
    input_hash: FileHash                     # Hash of input file
    diagrams: List[DiagramDependency] = field(default_factory=list)
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    build_time_ms: float = 0.0
    total_diagrams: int = 0
    cached_diagrams: int = 0
    new_diagrams: int = 0
    
    @property
    def total_output_size(self) -> int:
        """Sum of all diagram output sizes."""
        return sum(d.output_size_bytes for d in self.diagrams)


class BuildCache:
    """
    Track builds and detect what needs re-rendering.
    
    Single Responsibility:
    - Track input file hashes
    - Track diagram dependencies
    - Detect changes (content, mtime, size)
    - Determine what needs re-rendering
    - Store build history
    
    Usage:
        cache = BuildCache()
        if cache.needs_rebuild('doc.md'):
            # Rebuild document
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize build cache.
        
        Args:
            cache_dir: Directory for build cache (default: .build-cache/)
        """
        self.cache_dir = cache_dir or Path('.build-cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.builds_file = self.cache_dir / 'builds.json'
        self.diagrams_file = self.cache_dir / 'diagrams.json'
        
        # Load existing data
        self.builds: Dict[str, BuildRecord] = {}
        self.diagrams: Dict[str, DiagramDependency] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        # Load builds
        if self.builds_file.exists():
            try:
                data = json.loads(self.builds_file.read_text())
                for key, record in data.items():
                    record['input_hash'] = FileHash(**record['input_hash'])
                    record['diagrams'] = [
                        DiagramDependency(**d) for d in record.get('diagrams', [])
                    ]
                    self.builds[key] = BuildRecord(**record)
                logger.debug(f"Loaded {len(self.builds)} build records")
            except Exception as e:
                logger.warning(f"Failed to load builds cache: {e}")
        
        # Load diagrams
        if self.diagrams_file.exists():
            try:
                data = json.loads(self.diagrams_file.read_text())
                for key, diagram in data.items():
                    self.diagrams[key] = DiagramDependency(**diagram)
                logger.debug(f"Loaded {len(self.diagrams)} diagram records")
            except Exception as e:
                logger.warning(f"Failed to load diagrams cache: {e}")
    
    def _save_cache(self):
        """Save cache to disk."""
        # Save builds
        builds_data = {}
        for key, record in self.builds.items():
            record_dict = asdict(record)
            record_dict['input_hash'] = asdict(record.input_hash)
            record_dict['diagrams'] = [asdict(d) for d in record.diagrams]
            builds_data[key] = record_dict
        
        self.builds_file.write_text(json.dumps(builds_data, indent=2, default=str))
        
        # Save diagrams
        diagrams_data = {
            key: asdict(diagram) for key, diagram in self.diagrams.items()
        }
        self.diagrams_file.write_text(json.dumps(diagrams_data, indent=2, default=str))
    
    def needs_rebuild(self, input_file: str) -> bool:
        """
        Check if input file needs rebuilding.
        
        Args:
            input_file: Path to input markdown file
            
        Returns:
            True if file has changed or not in cache, False otherwise
        """
        input_path = Path(input_file)
        if not input_path.exists():
            return True
        
        # Check if we have a previous build
        if input_file not in self.builds:
            return True
        
        # Check if input file has changed
        previous_build = self.builds[input_file]
        if previous_build.input_hash.is_modified(input_path):
            return True
        
        logger.debug(f"{input_file}: No changes detected (skip rebuild)")
        return False
    
    def get_changed_diagrams(self, input_file: str, current_diagrams: List[DiagramDependency]) -> List[str]:
        """
        Get list of diagram IDs that need re-rendering.
        
        Args:
            input_file: Path to input markdown file
            current_diagrams: Current diagrams in document
            
        Returns:
            List of diagram IDs that need re-rendering
        """
        if input_file not in self.builds:
            # No previous build - render all
            return [d.diagram_id for d in current_diagrams]
        
        previous_build = self.builds[input_file]
        changed = []
        
        # Check each diagram
        for current_diagram in current_diagrams:
            # Check if diagram exists in previous build
            previous_diagram = next(
                (d for d in previous_build.diagrams if d.diagram_id == current_diagram.diagram_id),
                None
            )
            
            if not previous_diagram:
                # New diagram
                changed.append(current_diagram.diagram_id)
            elif current_diagram.needs_rerender(previous_diagram.source_code):
                # Diagram source changed
                changed.append(current_diagram.diagram_id)
            else:
                # Diagram unchanged
                logger.debug(f"Diagram {current_diagram.diagram_id}: Unchanged (skip render)")
        
        return changed
    
    def record_build(
        self,
        input_file: str,
        output_file: str,
        diagrams: List[DiagramDependency],
        build_time_ms: float = 0.0
    ):
        """
        Record a successful build.
        
        Args:
            input_file: Path to input markdown file
            output_file: Path to generated output file
            diagrams: List of diagrams in this build
            build_time_ms: Total build time in milliseconds
        """
        input_path = Path(input_file)
        if not input_path.exists():
            logger.warning(f"Input file not found: {input_file}")
            return
        
        # Compute input file hash
        stat = input_path.stat()
        content_hash = FileHash._compute_hash(input_path)
        
        input_hash = FileHash(
            path=input_file,
            content_hash=content_hash,
            mod_time=stat.st_mtime,
            size=stat.st_size
        )
        
        # Record build
        record = BuildRecord(
            input_file=input_file,
            output_file=output_file,
            input_hash=input_hash,
            diagrams=diagrams,
            build_time_ms=build_time_ms,
            total_diagrams=len(diagrams),
            new_diagrams=len([d for d in diagrams if d.render_time_ms > 0])
        )
        
        self.builds[input_file] = record
        
        # Update diagrams cache
        for diagram in diagrams:
            self.diagrams[diagram.diagram_id] = diagram
        
        self._save_cache()
        logger.info(f"Recorded build: {input_file} -> {output_file}")
    
    def get_build_stats(self, input_file: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a previous build.
        
        Args:
            input_file: Path to input markdown file
            
        Returns:
            Build statistics or None if not found
        """
        if input_file not in self.builds:
            return None
        
        build = self.builds[input_file]
        return {
            'input_file': build.input_file,
            'output_file': build.output_file,
            'build_time_ms': build.build_time_ms,
            'total_diagrams': build.total_diagrams,
            'new_diagrams': build.new_diagrams,
            'cached_diagrams': build.cached_diagrams,
            'total_output_size_bytes': build.total_output_size,
            'processed_at': build.processed_at
        }
    
    def get_all_builds(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all builds.
        
        Returns:
            Dictionary mapping input files to their build stats
        """
        return {
            path: self.get_build_stats(path)
            for path in self.builds.keys()
        }
    
    def clear(self):
        """
        Clear all cache data."""
        self.builds.clear()
        self.diagrams.clear()
        if self.builds_file.exists():
            self.builds_file.unlink()
        if self.diagrams_file.exists():
            self.diagrams_file.unlink()
        logger.info("Build cache cleared")
    
    def report(self) -> str:
        """
        Generate human-readable cache report.
        
        Returns:
            Formatted cache report
        """
        if not self.builds:
            return "[INFO] No builds in cache"
        
        total_diagrams = sum(b.total_diagrams for b in self.builds.values())
        total_build_time = sum(b.build_time_ms for b in self.builds.values())
        total_output_size = sum(b.total_output_size for b in self.builds.values())
        
        return f"""\
[INFO] Build Cache Report
       Cached Builds: {len(self.builds)}
       Total Diagrams: {total_diagrams}
       Total Build Time: {total_build_time:.0f}ms
       Total Output: {total_output_size / 1024:.1f} KB"""
