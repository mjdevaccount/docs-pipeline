#!/usr/bin/env python3
"""
Watch Mode - Live File Reloading and Development Loop Optimization
===================================================================

Provides file system monitoring for markdown documents with automatic rebuilds
on file changes, enabling fast development workflows.

Features:
- Monitor markdown files for changes
- Automatic rebuild on file modification
- Watch dependencies (CSS, images, glossaries, configs)
- Debounce rapid changes (batches updates)
- Multiple output formats in single watch session
- Real-time build metrics and statistics
- Graceful error handling with recovery
- Cross-platform support (Windows, macOS, Linux)

Usage:
    # Watch single file
    python -m tools.pdf.cli.watch_mode input.md output.pdf
    
    # Watch with options
    python -m tools.pdf.cli.watch_mode input.md output.pdf \
        --profile tech-whitepaper --cover --toc
    
    # Watch multiple files (config)
    python -m tools.pdf.cli.watch_mode --config watch.json
    
    # Watch with dependencies
    python -m tools.pdf.cli.watch_mode input.md output.pdf \
        --watch-css styles/ --watch-images images/ --watch-glossary glossary.yaml
    
    # Watch with verbose metrics
    python -m tools.pdf.cli.watch_mode input.md output.pdf --verbose

Metrics Tracked:
- File change frequency
- Rebuild times
- Cache hit rates
- Error frequency and types
- Total build time in session
- File dependency graph

Configuration (watch.json):
    {
        "watched_files": [
            {"input": "book.md", "output": "book.pdf"},
            {"input": "guide.md", "output": "guide.pdf", "glossary": "glossary.yaml"}
        ],
        "debounce_ms": 500,
        "watch_deps": ["styles/", "images/", "glossary.yaml"],
        "profile": "tech-whitepaper",
        "verbose": true
    }
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("[WARN] watchdog not installed. Install with: pip install watchdog")

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    markdown_to_pdf,
    markdown_to_docx,
    markdown_to_html,
    markdown_to_epub,
)

__version__ = "1.0.0"


@dataclass
class WatchMetrics:
    """Metrics for watch mode session."""
    total_rebuilds: int = 0
    successful_builds: int = 0
    failed_builds: int = 0
    total_rebuild_time: float = 0.0
    total_session_time: float = 0.0
    files_watched: Set[str] = field(default_factory=set)
    last_rebuild_time: float = 0.0
    average_rebuild_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def record_rebuild(self, success: bool, duration: float):
        """Record a rebuild attempt."""
        self.total_rebuilds += 1
        self.total_rebuild_time += duration
        self.last_rebuild_time = duration
        self.average_rebuild_time = self.total_rebuild_time / self.total_rebuilds
        
        if success:
            self.successful_builds += 1
        else:
            self.failed_builds += 1
    
    def report(self) -> str:
        """Generate metrics report."""
        success_rate = (self.successful_builds / self.total_rebuilds * 100) if self.total_rebuilds > 0 else 0
        
        return f"""
[INFO] Watch Mode Metrics
       Total Rebuilds: {self.total_rebuilds}
       Successful: {self.successful_builds}
       Failed: {self.failed_builds}
       Success Rate: {success_rate:.1f}%
       Average Build Time: {self.average_rebuild_time:.2f}s
       Last Build Time: {self.last_rebuild_time:.2f}s
       Total Session Time: {self.total_session_time:.2f}s
       Files Watched: {len(self.files_watched)}
"""


@dataclass
class WatchJob:
    """Single watch job (input -> output)."""
    input_file: str
    output_file: str
    output_format: str = 'pdf'
    kwargs: Dict = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)  # CSS, images, glossaries, etc.
    
    def should_rebuild(self, changed_file: str) -> bool:
        """Check if this job should rebuild based on changed file."""
        if changed_file == self.input_file:
            return True
        if Path(changed_file) in [Path(dep) for dep in self.dependencies]:
            return True
        return False


class BuildDebouncer:
    """Debounce rapid file changes to batch builds."""
    
    def __init__(self, delay_ms: int = 500):
        self.delay = delay_ms / 1000.0
        self.pending_files: Set[str] = set()
        self.last_trigger_time = 0.0
    
    def add_file(self, filepath: str) -> bool:
        """Add file and check if rebuild should trigger.
        
        Returns True if rebuild should happen now.
        """
        self.pending_files.add(filepath)
        current_time = time.time()
        
        if current_time - self.last_trigger_time >= self.delay:
            self.last_trigger_time = current_time
            return True
        return False
    
    def get_pending_files(self) -> Set[str]:
        """Get and clear pending files."""
        files = self.pending_files.copy()
        self.pending_files.clear()
        return files


class MarkdownWatchHandler(FileSystemEventHandler):
    """Handle file system events for markdown watching."""
    
    def __init__(self, watch_jobs: List[WatchJob], debouncer: BuildDebouncer, metrics: WatchMetrics, verbose: bool = False):
        self.watch_jobs = watch_jobs
        self.debouncer = debouncer
        self.metrics = metrics
        self.verbose = verbose
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        filepath = event.src_path
        if self.verbose:
            print(f"[WATCH] File changed: {filepath}")
        
        # Check if any job should rebuild
        should_rebuild = False
        for job in self.watch_jobs:
            if job.should_rebuild(filepath):
                should_rebuild = True
                if self.verbose:
                    print(f"[WATCH] Triggering rebuild for: {job.input_file}")
                break
        
        if should_rebuild and self.debouncer.add_file(filepath):
            self._trigger_rebuild()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        filepath = event.src_path
        if self.verbose:
            print(f"[WATCH] File created: {filepath}")
        
        # Check dependencies only (new files shouldn't trigger unless dependency)
        for job in self.watch_jobs:
            if Path(filepath) in [Path(dep) for dep in job.dependencies]:
                if self.debouncer.add_file(filepath):
                    self._trigger_rebuild()
                    break
    
    def _trigger_rebuild(self):
        """Trigger rebuild for affected jobs."""
        pending_files = self.debouncer.get_pending_files()
        
        for job in self.watch_jobs:
            should_rebuild = False
            for filepath in pending_files:
                if job.should_rebuild(filepath):
                    should_rebuild = True
                    break
            
            if should_rebuild:
                self._rebuild_job(job)
    
    def _rebuild_job(self, job: WatchJob):
        """Rebuild a single job."""
        start_time = time.time()
        
        try:
            print(f"\n[BUILD] {job.input_file} -> {job.output_file}")
            print(f"[TIME] {datetime.now().strftime('%H:%M:%S')}")
            
            format_map = {
                'pdf': markdown_to_pdf,
                'docx': markdown_to_docx,
                'html': markdown_to_html,
                'epub': markdown_to_epub
            }
            
            converter = format_map.get(job.output_format)
            if not converter:
                raise ValueError(f"Unknown format: {job.output_format}")
            
            success = converter(job.input_file, job.output_file, **job.kwargs)
            
            duration = time.time() - start_time
            self.metrics.record_rebuild(success, duration)
            
            if success:
                print(f"[OK] Built in {duration:.2f}s")
            else:
                print(f"[ERROR] Build failed after {duration:.2f}s")
                self.metrics.errors.append(f"{job.input_file}: build failed")
        
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_rebuild(False, duration)
            print(f"[ERROR] Exception: {e}")
            self.metrics.errors.append(f"{job.input_file}: {str(e)}")


class WatchModeManager:
    """Manage watch mode operations."""
    
    def __init__(self, watch_jobs: List[WatchJob], debounce_ms: int = 500, verbose: bool = False):
        self.watch_jobs = watch_jobs
        self.debouncer = BuildDebouncer(debounce_ms)
        self.metrics = WatchMetrics()
        self.verbose = verbose
        self.observer: Optional[Observer] = None
        self.start_time = 0.0
        
        # Collect all files and directories to watch
        self.watched_paths = self._collect_watched_paths()
    
    def _collect_watched_paths(self) -> Set[str]:
        """Collect all unique paths to watch (input files and dependencies)."""
        paths = set()
        
        for job in self.watch_jobs:
            input_path = Path(job.input_file)
            if input_path.exists():
                self.metrics.files_watched.add(job.input_file)
                # Watch the directory containing the input file
                paths.add(str(input_path.parent))
            
            # Watch dependencies
            for dep in job.dependencies:
                dep_path = Path(dep)
                if dep_path.exists():
                    self.metrics.files_watched.add(dep)
                    if dep_path.is_dir():
                        paths.add(str(dep_path))
                    else:
                        paths.add(str(dep_path.parent))
        
        return paths
    
    def start(self):
        """Start watching files."""
        if not WATCHDOG_AVAILABLE:
            print("[ERROR] watchdog not installed. Install with: pip install watchdog")
            return False
        
        self.start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"  Watch Mode Active")
        print(f"{'='*60}")
        print(f"[WATCH] Monitoring {len(self.metrics.files_watched)} files")
        print(f"[WATCH] Watching {len(self.watched_paths)} directories")
        print(f"[WATCH] Debounce: 500ms")
        print(f"[WATCH] Press Ctrl+C to stop\n")
        
        # Create observer
        self.observer = Observer()
        handler = MarkdownWatchHandler(
            self.watch_jobs,
            self.debouncer,
            self.metrics,
            self.verbose
        )
        
        # Schedule watchers for each path
        for path in self.watched_paths:
            try:
                self.observer.schedule(handler, path, recursive=True)
                if self.verbose:
                    print(f"[WATCH] Scheduled: {path}")
            except Exception as e:
                print(f"[ERROR] Failed to watch {path}: {e}")
        
        try:
            self.observer.start()
            self.observer.join()
        except KeyboardInterrupt:
            print("\n[WATCH] Stopping...")
            self.stop()
        except Exception as e:
            print(f"[ERROR] Watch failed: {e}")
            self.stop()
            return False
        
        return True
    
    def stop(self):
        """Stop watching files and report metrics."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.metrics.total_session_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"  Watch Mode Complete")
        print(f"{'='*60}")
        print(self.metrics.report())
        
        if self.metrics.errors:
            print("\n[ERRORS] Issues encountered:")
            for error in self.metrics.errors:
                print(f"  - {error}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Watch Mode - Live file reloading for development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch single file for PDF rebuilds
  python -m tools.pdf.cli.watch_mode doc.md doc.pdf
  
  # Watch with options
  python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
      --profile tech-whitepaper --cover --toc
  
  # Watch with dependencies
  python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
      --watch-css styles/ --watch-images images/
  
  # Watch with glossary
  python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
      --glossary glossary.yaml
  
  # Watch multiple files (config)
  python -m tools.pdf.cli.watch_mode --config watch.json
  
  # Watch with verbose metrics
  python -m tools.pdf.cli.watch_mode doc.md doc.pdf --verbose
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input markdown file')
    parser.add_argument('output', nargs='?', help='Output file')
    parser.add_argument('--config', help='JSON config file for watch jobs')
    parser.add_argument('--format', default='pdf', choices=['pdf', 'docx', 'html', 'epub'],
                       help='Output format (default: pdf)')
    parser.add_argument('--debounce', type=int, default=500,
                       help='Debounce delay in milliseconds (default: 500)')
    
    # Dependency watching
    parser.add_argument('--watch-css', action='append', help='Watch CSS directory/file')
    parser.add_argument('--watch-images', action='append', help='Watch images directory')
    parser.add_argument('--watch-glossary', help='Watch glossary file')
    parser.add_argument('--watch-deps', action='append', help='Watch additional dependencies')
    
    # Build options
    parser.add_argument('--profile', help='CSS profile')
    parser.add_argument('--cover', action='store_true', help='Generate cover page')
    parser.add_argument('--toc', action='store_true', help='Generate TOC')
    parser.add_argument('--glossary', help='Glossary file')
    parser.add_argument('--css', help='Custom CSS file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    return parser.parse_args()


def load_config_file(config_path: str) -> Tuple[List[WatchJob], int, bool]:
    """Load watch jobs from JSON config file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    watch_jobs = []
    for job_config in config.get('watched_files', []):
        input_file = job_config['input']
        output_file = job_config.get('output', input_file.replace('.md', f".{job_config.get('format', 'pdf')}"))
        output_format = job_config.get('format', 'pdf')
        
        # Build kwargs from job config
        kwargs = {}
        for key in ['profile', 'cover', 'toc', 'glossary', 'css', 'verbose']:
            if key in job_config:
                kwargs[key] = job_config[key]
        
        # Collect dependencies
        dependencies = set()
        for dep_type in ['watch_css', 'watch_images', 'watch_glossary', 'watch_deps']:
            if dep_type in job_config:
                deps = job_config[dep_type]
                if isinstance(deps, list):
                    dependencies.update(deps)
                else:
                    dependencies.add(deps)
        
        watch_jobs.append(WatchJob(
            input_file=input_file,
            output_file=output_file,
            output_format=output_format,
            kwargs=kwargs,
            dependencies=dependencies
        ))
    
    debounce_ms = config.get('debounce_ms', 500)
    verbose = config.get('verbose', False)
    
    return watch_jobs, debounce_ms, verbose


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load watch jobs
    if args.config:
        watch_jobs, debounce_ms, verbose = load_config_file(args.config)
    else:
        if not args.input or not args.output:
            print("[ERROR] Input and output files required (or use --config)")
            sys.exit(1)
        
        # Build kwargs from CLI args
        kwargs = {}
        if args.profile:
            kwargs['profile'] = args.profile
        if args.cover:
            kwargs['generate_cover'] = True
        if args.toc:
            kwargs['generate_toc'] = True
        if args.glossary:
            kwargs['glossary_file'] = args.glossary
        if args.css:
            kwargs['css_file'] = args.css
        if args.verbose:
            kwargs['verbose'] = True
        
        # Collect dependencies
        dependencies = set()
        if args.watch_css:
            dependencies.update(args.watch_css)
        if args.watch_images:
            dependencies.update(args.watch_images)
        if args.watch_glossary:
            dependencies.add(args.watch_glossary)
        if args.watch_deps:
            dependencies.update(args.watch_deps)
        
        watch_jobs = [
            WatchJob(
                input_file=args.input,
                output_file=args.output,
                output_format=args.format,
                kwargs=kwargs,
                dependencies=dependencies
            )
        ]
        debounce_ms = args.debounce
        verbose = args.verbose
    
    # Start watch mode
    manager = WatchModeManager(watch_jobs, debounce_ms, verbose)
    success = manager.start()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
