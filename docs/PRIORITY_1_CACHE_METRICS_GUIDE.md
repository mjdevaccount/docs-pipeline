# 📄 Priority 1: Cache Metrics Implementation Guide
## Cache Hit Ratio + Performance Reporting (1-2 hours)

**Status**: Ready to implement  
**Complexity**: Low  
**Impact**: High (users see real performance gains)  
**Files to Modify**: 3  

---

## Overview

**Goal**: Make diagram caching visible to users. Show:
- Cache hit ratio (% of diagrams served from cache)
- Time saved (ms)
- Number of diagrams cached
- Size reduction (% smaller than original)

**Before**:
```bash
$ python -m tools.pdf.cli.main doc.md output.pdf --verbose
[INFO] Converting doc.md to output.pdf
[OK] Created: output.pdf
```

**After**:
```bash
$ python -m tools.pdf.cli.main doc.md output.pdf --verbose
[INFO] Converting doc.md to output.pdf
[INFO] Rendering 4 diagrams...
[INFO] Cache Report:
         Hit Ratio: 75.0%
         Cached: 3/4 diagrams
         Time Saved: 2.3s
         Size Reduction: 42.5%
[OK] Created: output.pdf
```

---

## Step 1: Update Cache Class

**File**: `tools/pdf/diagram_rendering/cache.py`

Add stats tracking to existing `DiagramCache` class:

```python
from dataclasses import dataclass, field
from typing import Dict
import time

@dataclass
class CacheStats:
    """Track cache performance metrics."""
    hits: int = 0
    misses: int = 0
    time_saved_ms: float = 0.0  # Accumulated time from cache hits
    total_size_reduction_bytes: int = 0  # Accumulated size reduction
    total_original_size_bytes: int = 0
    total_cached_size_bytes: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Cache hit ratio (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def size_reduction_percent(self) -> float:
        """Size reduction percentage from caching."""
        if self.total_original_size_bytes == 0:
            return 0.0
        return (self.total_size_reduction_bytes / self.total_original_size_bytes) * 100
    
    def record_cache_hit(self, render_time_ms: float, original_size: int, cached_size: int):
        """Record a cache hit."""
        self.hits += 1
        self.time_saved_ms += render_time_ms  # Time that would have been spent rendering
        self.total_original_size_bytes += original_size
        self.total_cached_size_bytes += cached_size
        self.total_size_reduction_bytes += (original_size - cached_size)
    
    def record_cache_miss(self, render_time_ms: float, result_size: int):
        """Record a cache miss (new render)."""
        self.misses += 1
        self.total_original_size_bytes += result_size
        self.total_cached_size_bytes += result_size
    
    def report(self) -> str:
        """Generate human-readable cache report."""
        total = self.hits + self.misses
        if total == 0:
            return "No diagrams cached."
        
        return f"""\
=== Cache Performance Report ===
Hit Ratio: {self.hit_ratio:.1%} ({self.hits}/{total})
Time Saved: {self.time_saved_ms:.0f}ms
Size Reduction: {self.size_reduction_percent:.1f}%
Diagrams Cached: {self.hits}
Diagrams Rendered: {self.misses}
"""


class DiagramCache:
    """Existing cache implementation with stats tracking."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        # ... existing __init__ code ...
        self.stats = CacheStats()
    
    def get_or_render(self, diagram_type: str, diagram_spec: str, renderer) -> bytes:
        """
        Get cached diagram or render new one.
        
        Updated to track stats.
        """
        content_hash = self._hash_content(diagram_spec)
        cache_key = f"{diagram_type}_{content_hash}"
        cached_path = self.cache_dir / cache_key
        
        # Cache hit
        if cached_path.exists():
            cached_data = cached_path.read_bytes()
            original_size = len(diagram_spec.encode())
            cached_size = len(cached_data)
            # Assume rendering would have taken ~500ms for this diagram
            render_time_estimate = 500  # ms
            self.stats.record_cache_hit(render_time_estimate, original_size, cached_size)
            return cached_data
        
        # Cache miss - render new
        start_time = time.time()
        result = renderer.render(diagram_type, diagram_spec)
        
        # Store in cache
        cached_path.write_bytes(result)
        
        self.stats.record_cache_miss(0, len(result))
        return result
```

**Key Changes**:
- Add `CacheStats` dataclass to track hits/misses
- Add `record_cache_hit()` and `record_cache_miss()` methods
- Add `report()` method for human-readable output
- Update `get_or_render()` to call stats tracking

---

## Step 2: Update Pipeline to Report Stats

**File**: `tools/pdf/pipeline/__init__.py`

Update the main `process_document()` function to report cache stats:

```python
def process_document(
    input_file: str,
    output_file: str,
    output_format: OutputFormat,
    verbose: bool = False,
    **kwargs
) -> bool:
    """
    Process document through pipeline.
    
    Now reports cache stats when verbose=True.
    """
    # ... existing code ...
    
    try:
        # Build and run pipeline
        pipeline = _build_pipeline(output_format, **kwargs)
        context = PipelineContext(
            input_file=input_file,
            output_file=output_file,
            config=config
        )
        
        # Execute pipeline
        success = pipeline.execute(context)
        
        if success and verbose:
            # Report cache stats if available
            if hasattr(pipeline, 'diagram_cache') and pipeline.diagram_cache:
                print(pipeline.diagram_cache.stats.report())
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] Pipeline failed: {e}")
        return False
```

**Key Changes**:
- Check for `diagram_cache` on pipeline object
- Call `report()` method on cache stats
- Only show if `verbose=True`

---

## Step 3: Update CLI to Show Stats

**File**: `tools/pdf/cli/main.py`

Update the conversion calls to show cache stats:

```python
def main():
    # ... existing argparse setup ...
    
    # In single file mode, after successful conversion:
    try:
        if args.format == 'pdf':
            success = markdown_to_pdf(args.input, output_file, **kwargs)
        elif args.format == 'docx':
            success = markdown_to_docx(args.input, output_file, **kwargs)
        else:
            success = markdown_to_html(args.input, output_file, **kwargs)
        
        if success:
            print(f"[OK] Created: {output_file}")
            
            # NEW: Show cache stats if verbose
            if args.verbose:
                # Try to extract and show cache stats
                # (depends on whether core functions expose them)
                pass
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        sys.exit(1)
```

**Alternative (simpler)**: Update `core/converter.py` functions to accept a `verbose` flag and print stats directly.

---

## Step 4: Update Core Converter Functions

**File**: `tools/pdf/core/converter.py`

Update `markdown_to_pdf()`, `markdown_to_docx()`, etc. to report stats:

```python
def markdown_to_pdf(
    md_file: str,
    output_pdf: str,
    verbose: bool = False,
    **kwargs
) -> bool:
    """
    Convert Markdown to PDF with optional cache stats reporting.
    """
    try:
        # ... existing conversion code ...
        
        success = process_document(
            input_file=md_file,
            output_file=output_pdf,
            output_format=OutputFormat.PDF,
            verbose=verbose,  # Pass through
            **kwargs
        )
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] PDF conversion failed: {e}")
        return False
```

---

## Testing

### Test Case 1: Single Document (First Run)
```bash
$ python -m tools.pdf.cli.main docs/examples/advanced-markdown-showcase.md output.pdf --verbose
[INFO] Converting docs/examples/advanced-markdown-showcase.md to output.pdf
[INFO] Rendering 5 diagrams...
[INFO] Cache Report:
         Hit Ratio: 0.0%
         Cached: 0/5 diagrams
         Time Saved: 0ms
         Size Reduction: 0.0%
[OK] Created: output.pdf
```

### Test Case 2: Single Document (Second Run - Should Have Cache Hits)
```bash
$ python -m tools.pdf.cli.main docs/examples/advanced-markdown-showcase.md output.pdf --verbose
[INFO] Converting docs/examples/advanced-markdown-showcase.md to output.pdf
[INFO] Rendering 5 diagrams...
[INFO] Cache Report:
         Hit Ratio: 100.0%
         Cached: 5/5 diagrams
         Time Saved: 2500ms
         Size Reduction: 35.2%
[OK] Created: output.pdf
```

### Test Case 3: Batch Processing
```bash
$ python -m tools.pdf.cli.main --batch doc1.md doc2.md --verbose
[INFO] Processing 2 files with 1 threads...
[INFO] Converting doc1.md to output/doc1.pdf
[INFO] Cache Report:
         Hit Ratio: 75.0%
         Cached: 3/4 diagrams
         Time Saved: 1500ms
         Size Reduction: 38.1%
[OK] Generated: output/doc1.pdf
[INFO] Converting doc2.md to output/doc2.pdf
[INFO] Cache Report:
         Hit Ratio: 100.0%
         Cached: 6/6 diagrams
         Time Saved: 3000ms
         Size Reduction: 42.3%
[OK] Generated: output/doc2.pdf
```

---

## Implementation Checklist

- [ ] Add `CacheStats` dataclass to `diagram_rendering/cache.py`
- [ ] Add tracking methods to `DiagramCache` class
- [ ] Update `get_or_render()` to call tracking methods
- [ ] Update pipeline to report stats when verbose
- [ ] Update CLI to accept and pass `--verbose` flag
- [ ] Test single file (first and second run)
- [ ] Test batch processing
- [ ] Test with different diagram types
- [ ] Document in CLI help (`python -m tools.pdf.cli.main --help`)
- [ ] Add example output to README

---

## Success Criteria

✅ **Done When**:
1. Cache stats print to console with `--verbose` flag
2. Hit ratio shows correctly (0-100%)
3. Time saved is calculated accurately
4. Size reduction shows correct percentage
5. Works with single and batch processing
6. All tests pass
7. No breaking changes to existing API
8. Documented in README

---

## Time Estimate

- **Implementation**: 45 minutes
- **Testing**: 20 minutes
- **Documentation**: 10 minutes
- **Total**: ~1.5 hours

---

## Next Steps After This Priority

Once cache metrics are complete:
1. **Priority 2**: Test coverage dashboard (pytest, coverage reports)
2. **Priority 3**: Test tooling (Makefile targets)
3. **Priority 4**: Watch mode for development

Each builds naturally on the previous one.

---

## Questions?

If you get stuck:
1. Check existing `diagram_rendering/cache.py` structure
2. Look at how `PipelineContext` passes data between steps
3. Test incrementally (one test case at a time)
4. Use `--verbose` flag to debug

**Ready to code?** Start with Step 1 above. The structure is already there - you're just adding stats tracking! 🚀
