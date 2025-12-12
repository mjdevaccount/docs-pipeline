"""
Unit tests for cache metrics functionality.

Tests the CacheStats class and cache metrics reporting.
"""
import pytest
from pathlib import Path
from tools.pdf.diagram_rendering.cache import CacheStats, DiagramCache
from tools.pdf.diagram_rendering.base import DiagramFormat


class TestCacheStats:
    """Test CacheStats dataclass."""
    
    def test_initial_state(self):
        """Test initial cache stats state."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.time_saved_ms == 0.0
        assert stats.hit_ratio == 0.0
        assert stats.size_reduction_percent == 0.0
    
    def test_record_cache_hit(self):
        """Test recording a cache hit."""
        stats = CacheStats()
        stats.record_cache_hit(original_size=1000, cached_size=800, render_time_estimate_ms=500.0)
        
        assert stats.hits == 1
        assert stats.misses == 0
        assert stats.time_saved_ms == 500.0
        assert stats.total_original_size_bytes == 1000
        assert stats.total_cached_size_bytes == 800
        assert stats.hit_ratio == 1.0
        assert stats.size_reduction_percent == 20.0  # (1000-800)/1000 * 100
    
    def test_record_cache_miss(self):
        """Test recording a cache miss."""
        stats = CacheStats()
        stats.record_cache_miss(result_size=1000)
        
        assert stats.hits == 0
        assert stats.misses == 1
        assert stats.time_saved_ms == 0.0
        assert stats.total_original_size_bytes == 1000
        assert stats.total_cached_size_bytes == 1000
        assert stats.hit_ratio == 0.0
        assert stats.size_reduction_percent == 0.0
    
    def test_mixed_hits_and_misses(self):
        """Test mixed cache hits and misses."""
        stats = CacheStats()
        
        # Record 3 hits
        stats.record_cache_hit(1000, 800, 500.0)
        stats.record_cache_hit(2000, 1500, 500.0)
        stats.record_cache_hit(1500, 1200, 500.0)
        
        # Record 1 miss
        stats.record_cache_miss(1000)
        
        assert stats.hits == 3
        assert stats.misses == 1
        assert stats.time_saved_ms == 1500.0  # 3 * 500ms
        assert stats.hit_ratio == 0.75  # 3/4
        assert stats.total_original_size_bytes == 5500  # 1000+2000+1500+1000
        assert stats.total_cached_size_bytes == 4500  # 800+1500+1200+1000
        assert stats.size_reduction_percent == pytest.approx(18.18, rel=0.01)  # (5500-4500)/5500 * 100
    
    def test_report_with_no_data(self):
        """Test report generation with no cache data."""
        stats = CacheStats()
        report = stats.report()
        assert "[INFO] No diagrams cached." in report
    
    def test_report_with_data(self):
        """Test report generation with cache data."""
        stats = CacheStats()
        stats.record_cache_hit(1000, 800, 500.0)
        stats.record_cache_hit(2000, 1500, 500.0)
        stats.record_cache_miss(1000)
        
        report = stats.report()
        assert "[INFO] Cache Performance Report" in report
        assert "Hit Ratio:" in report
        assert "Time Saved:" in report
        assert "Size Reduction:" in report
        assert "2/3" in report  # 2 hits out of 3 total


class TestDiagramCacheMetrics:
    """Test DiagramCache metrics tracking."""
    
    def test_cache_stats_initialization(self, tmp_path):
        """Test that cache initializes with stats."""
        cache = DiagramCache(cache_dir=tmp_path)
        assert cache.stats is not None
        assert isinstance(cache.stats, CacheStats)
        assert cache.stats.hits == 0
        assert cache.stats.misses == 0
    
    def test_get_and_copy_tracks_hit(self, tmp_path):
        """Test that get_and_copy tracks cache hits."""
        cache = DiagramCache(cache_dir=tmp_path)
        
        # Create a cached file manually
        diagram_code = "graph TD\nA-->B"
        cache_hash = cache._compute_hash(diagram_code, DiagramFormat.SVG)
        cached_file = cache.cache_dir / f"{cache_hash}.svg"
        cached_file.write_text("test svg content")
        
        # Get from cache
        output_file = tmp_path / "output.svg"
        result = cache.get_and_copy(diagram_code, output_file, DiagramFormat.SVG)
        
        assert result is True
        assert output_file.exists()
        assert cache.stats.hits == 1
        assert cache.stats.misses == 0
    
    def test_record_miss_tracks_miss(self, tmp_path):
        """Test that record_miss tracks cache misses."""
        cache = DiagramCache(cache_dir=tmp_path)
        
        result_file = tmp_path / "result.svg"
        result_file.write_text("rendered svg content")
        
        cache.record_miss(result_file)
        
        assert cache.stats.hits == 0
        assert cache.stats.misses == 1
    
    def test_clear_resets_stats(self, tmp_path):
        """Test that clear resets cache stats."""
        cache = DiagramCache(cache_dir=tmp_path)
        
        # Record some activity
        result_file = tmp_path / "result.svg"
        result_file.write_text("content")
        cache.record_miss(result_file)
        
        assert cache.stats.misses == 1
        
        # Clear cache
        cache.clear()
        
        assert cache.stats.hits == 0
        assert cache.stats.misses == 0
        assert cache.stats.time_saved_ms == 0.0

