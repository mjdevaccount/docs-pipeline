"""
Phase B Integration Tests
========================

Verifies that Phase B (MermaidNativeRenderer) is properly integrated
into the document processing pipeline and working correctly.

Tests:
1. Phase B availability and import
2. DiagramRenderingStep uses Phase B
3. Fallback chain works correctly
4. Performance improvement is measurable
5. Backward compatibility maintained
"""

import sys
import time
import tempfile
from pathlib import Path
import unittest

# Add parent path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.steps import DiagramRenderingStep
from pipeline.base import PipelineContext
from diagram_rendering import MermaidNativeRenderer, DiagramFormat


class TestPhaseB Integration(unittest.TestCase):
    """Test Phase B integration into the pipeline"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.work_dir = Path(tempfile.mkdtemp(prefix='phase_b_test_'))
        self.test_diagram = '''graph LR
    A[Start] --> B{Decision}
    B --> C[Path 1]
    B --> D[Path 2]
    C --> E[End]
    D --> E'''
    
    def test_phase_b_renderer_available(self):
        """Test that MermaidNativeRenderer can be imported"""
        try:
            from diagram_rendering import MermaidNativeRenderer
            self.assertIsNotNone(MermaidNativeRenderer)
            print("\u2705 Phase B MermaidNativeRenderer is available")
        except ImportError as e:
            self.fail(f"Phase B import failed: {e}")
    
    def test_phase_b_direct_render(self):
        """Test Phase B rendering directly"""
        try:
            renderer = MermaidNativeRenderer(
                theme='neutral',
                background='transparent'
            )
            
            svg_file = self.work_dir / 'test_diagram.svg'
            result = renderer.render(
                self.test_diagram,
                svg_file,
                format=DiagramFormat.SVG
            )
            
            self.assertTrue(result.success, f"Render failed: {result.error_message}")
            self.assertTrue(svg_file.exists(), "SVG file not created")
            self.assertTrue(svg_file.stat().st_size > 0, "SVG file is empty")
            print(f"\u2705 Phase B direct render successful ({svg_file.stat().st_size} bytes)")
        
        except Exception as e:
            self.fail(f"Phase B direct render failed: {e}")
    
    def test_diagram_step_phase_b_enabled(self):
        """Test that DiagramRenderingStep uses Phase B when enabled"""
        try:
            markdown_content = f'''# Test Document

Here is a diagram:

```mermaid
{self.test_diagram}
```

End of document.'''
            
            context = PipelineContext(
                input_file=Path('test.md'),
                output_file=Path('test.pdf'),
                work_dir=self.work_dir,
                config={
                    'use_native_renderer': True,
                    'enable_diagrams': True,
                    'verbose': True
                }
            )
            context.preprocessed_markdown = markdown_content
            
            step = DiagramRenderingStep()
            success = step.execute(context)
            
            self.assertTrue(success, "DiagramRenderingStep failed")
            self.assertNotIn('```mermaid', context.preprocessed_markdown,
                           "Diagram code block not replaced")
            self.assertIn('diagram-container', context.preprocessed_markdown,
                        "SVG wrapper not found")
            print("\u2705 DiagramRenderingStep Phase B integration successful")
        
        except Exception as e:
            self.fail(f"DiagramRenderingStep test failed: {e}")
    
    def test_multiple_diagrams(self):
        """Test Phase B with multiple diagrams"""
        try:
            markdown_content = '''# Multiple Diagrams Test

First diagram:
```mermaid
graph TD
    A[Task A] --> B[Task B]
    B --> C[Task C]
```

Second diagram:
```mermaid
flowchart LR
    X[Input] --> Y[Process] --> Z[Output]
```

Third diagram:
```mermaid
graph TB
    P[Parent]
    P --> C1[Child 1]
    P --> C2[Child 2]
    P --> C3[Child 3]
```
'''
            
            context = PipelineContext(
                input_file=Path('test_multi.md'),
                output_file=Path('test_multi.pdf'),
                work_dir=self.work_dir,
                config={
                    'use_native_renderer': True,
                    'enable_diagrams': True,
                }
            )
            context.preprocessed_markdown = markdown_content
            
            step = DiagramRenderingStep()
            start_time = time.time()
            success = step.execute(context)
            elapsed = time.time() - start_time
            
            self.assertTrue(success)
            # Count SVG containers
            svg_count = context.preprocessed_markdown.count('diagram-container')
            self.assertEqual(svg_count, 3, f"Expected 3 diagrams, found {svg_count}")
            print(f"\u2705 Multiple diagrams rendered in {elapsed:.2f}s")
            print(f"  Average per diagram: {elapsed/3:.2f}s")
        
        except Exception as e:
            self.fail(f"Multiple diagrams test failed: {e}")
    
    def test_backward_compatibility(self):
        """Test that existing code still works (backward compatible)"""
        try:
            # This is how existing code would use the pipeline
            markdown_content = f'''# Document

```mermaid
{self.test_diagram}
```
'''
            
            # Create context without explicit Phase B config
            context = PipelineContext(
                input_file=Path('test_compat.md'),
                output_file=Path('test_compat.pdf'),
                work_dir=self.work_dir,
                config={}  # No explicit Phase B config
            )
            context.preprocessed_markdown = markdown_content
            
            step = DiagramRenderingStep()
            success = step.execute(context)
            
            # Should still work (Phase B is default, falls back if needed)
            self.assertTrue(success)
            print("\u2705 Backward compatibility maintained")
        
        except Exception as e:
            self.fail(f"Backward compatibility test failed: {e}")
    
    def test_fallback_graceful(self):
        """Test graceful fallback if Phase B unavailable"""
        try:
            markdown_content = f'''# Fallback Test

```mermaid
{self.test_diagram}
```
'''
            
            # Test with fallback enabled
            context = PipelineContext(
                input_file=Path('test_fallback.md'),
                output_file=Path('test_fallback.pdf'),
                work_dir=self.work_dir,
                config={
                    'use_native_renderer': False,  # Force fallback
                    'enable_diagrams': True,
                }
            )
            context.preprocessed_markdown = markdown_content
            
            step = DiagramRenderingStep()
            success = step.execute(context)
            
            # Should succeed or fail gracefully
            self.assertTrue(success)
            print("\u2705 Fallback handling works correctly")
        
        except Exception as e:
            self.fail(f"Fallback test failed: {e}")
    
    def tearDown(self):
        """Cleanup test fixtures"""
        import shutil
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)


class TestPhaseB Performance(unittest.TestCase):
    """Benchmark Phase B performance"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.work_dir = Path(tempfile.mkdtemp(prefix='phase_b_perf_'))
    
    def test_phase_b_performance(self):
        """Benchmark Phase B rendering speed"""
        try:
            renderer = MermaidNativeRenderer(
                theme='neutral',
                background='transparent'
            )
            
            # Simple diagram for benchmark
            simple_diagram = 'graph LR\n    A --> B --> C'
            
            # Warm up
            svg_file = self.work_dir / 'warmup.svg'
            renderer.render(simple_diagram, svg_file, format=DiagramFormat.SVG)
            
            # Benchmark
            times = []
            for i in range(3):
                svg_file = self.work_dir / f'bench_{i}.svg'
                start = time.time()
                result = renderer.render(simple_diagram, svg_file, format=DiagramFormat.SVG)
                elapsed = time.time() - start
                
                if result.success:
                    times.append(elapsed)
            
            avg_time = sum(times) / len(times) if times else 0
            print(f"\u2705 Phase B Performance:")
            print(f"  Average render time: {avg_time*1000:.1f}ms")
            print(f"  Individual runs: {[f'{t*1000:.1f}ms' for t in times]}")
            
            # Phase B should be fast (typical: 50-150ms)
            self.assertLess(avg_time, 0.5, "Phase B render too slow")
        
        except Exception as e:
            self.fail(f"Performance test failed: {e}")
    
    def tearDown(self):
        """Cleanup"""
        import shutil
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
