#!/usr/bin/env python3
"""
Test suite for Mermaid diagram rendering in the pipeline.

Tests the complete flow:
1. Markdown with Mermaid blocks
2. DiagramRenderingStep processing
3. SVG embedding in output
4. Profile-aware theming

Usage:
    python -m pytest test_mermaid_rendering.py -v
    python test_mermaid_rendering.py  # Direct run
"""

import sys
import tempfile
from pathlib import Path

# Add tools/pdf to path
tools_pdf = Path(__file__).parent.parent
sys.path.insert(0, str(tools_pdf))

from pipeline import (
    PipelineContext,
    create_pdf_pipeline,
    create_html_pipeline,
)
from pipeline.steps import DiagramRenderingStep


# Sample Mermaid diagrams for testing
MERMAID_FLOWCHART = """
graph TD
    A[Start] --> B[Process]
    B --> C{Decision}
    C -->|Yes| D[Result]
    C -->|No| E[End]
"""

MERMAID_SEQUENCE = """
sequenceDiagram
    participant A as Client
    participant B as Server
    A->>B: Request
    B->>A: Response
"""

TEST_MARKDOWN_SINGLE = f"""
# Test Document

Here's a flowchart:

```mermaid
{MERMAID_FLOWCHART}
```

End of document.
"""

TEST_MARKDOWN_MULTIPLE = f"""
# Test Document with Multiple Diagrams

## First Diagram

```mermaid
{MERMAID_FLOWCHART}
```

## Second Diagram

```mermaid
{MERMAID_SEQUENCE}
```

End of document.
"""


def test_diagram_rendering_step():
    """
    Test DiagramRenderingStep directly.
    """
    print("\n" + "="*70)
    print("TEST: DiagramRenderingStep (Single Diagram)")
    print("="*70)
    
    with tempfile.TemporaryDirectory(prefix='diagram_test_') as work_dir:
        # Create context
        context = PipelineContext(
            input_file=Path('test.md'),
            output_file=Path('test.pdf'),
            work_dir=Path(work_dir),
            config={
                'enable_diagrams': True,
                'use_cache': False,  # Disable caching for test
                'profile': 'tech-whitepaper',
                'verbose': True
            },
            verbose=True
        )
        
        # Set markdown content
        context.preprocessed_markdown = TEST_MARKDOWN_SINGLE
        
        # Run step
        step = DiagramRenderingStep()
        success = step.execute(context)
        
        # Check results
        result = context.preprocessed_markdown
        
        print(f"\nStep success: {success}")
        print(f"Contains SVG: {'<svg' in result}")
        print(f"Contains mermaid block: {'```mermaid' in result}")
        print(f"\nResult preview (first 500 chars):")
        print(result[:500] + "...\n")
        
        assert success, "Step should succeed"
        assert '<svg' in result, "Result should contain SVG tags"
        assert '```mermaid' not in result, "Mermaid code blocks should be replaced"
        
        print("✓ Single diagram test PASSED\n")
        return True


def test_multiple_diagrams():
    """
    Test DiagramRenderingStep with multiple diagrams.
    """
    print("\n" + "="*70)
    print("TEST: Multiple Mermaid Diagrams")
    print("="*70)
    
    with tempfile.TemporaryDirectory(prefix='diagram_test_') as work_dir:
        context = PipelineContext(
            input_file=Path('test.md'),
            output_file=Path('test.pdf'),
            work_dir=Path(work_dir),
            config={
                'enable_diagrams': True,
                'use_cache': False,
                'profile': 'dark-pro',
                'verbose': True
            },
            verbose=True
        )
        
        context.preprocessed_markdown = TEST_MARKDOWN_MULTIPLE
        
        step = DiagramRenderingStep()
        success = step.execute(context)
        
        result = context.preprocessed_markdown
        svg_count = result.count('<svg')
        
        print(f"\nStep success: {success}")
        print(f"SVG count: {svg_count}")
        print(f"Expected: 2")
        
        assert success, "Step should succeed"
        assert svg_count == 2, f"Should have 2 SVGs, got {svg_count}"
        assert '```mermaid' not in result, "No mermaid blocks should remain"
        
        print("✓ Multiple diagrams test PASSED\n")
        return True


def test_pipeline_integration():
    """
    Test full PDF pipeline with diagram rendering.
    """
    print("\n" + "="*70)
    print("TEST: PDF Pipeline Integration")
    print("="*70)
    
    with tempfile.TemporaryDirectory(prefix='pipeline_test_') as work_dir:
        work_path = Path(work_dir)
        
        # Write test markdown file
        test_md = work_path / 'test.md'
        test_md.write_text(TEST_MARKDOWN_SINGLE)
        
        output_pdf = work_path / 'test.pdf'
        
        # Create pipeline
        pipeline = create_pdf_pipeline(include_math=False, include_glossary=False)
        
        # Create context
        context = PipelineContext(
            input_file=test_md,
            output_file=output_pdf,
            work_dir=work_path / 'work',
            config={
                'enable_diagrams': True,
                'use_cache': False,
                'profile': 'tech-whitepaper',
                'renderer': 'weasyprint',
                'verbose': True
            },
            verbose=True
        )
        
        print(f"\nInput: {test_md}")
        print(f"Output: {output_pdf}")
        
        try:
            # Note: This will fail if dependencies aren't installed
            success = pipeline.execute(context)
            print(f"\nPipeline success: {success}")
            
            if output_pdf.exists():
                size = output_pdf.stat().st_size
                print(f"Output PDF created: {size} bytes")
                print("✓ Pipeline integration test PASSED\n")
                return True
            else:
                print("[WARN] Output PDF not created (dependencies may be missing)")
                return False
        except Exception as e:
            print(f"\n[WARN] Pipeline test failed (expected if dependencies missing): {e}")
            return False


def test_disabled_diagrams():
    """
    Test that diagrams can be disabled.
    """
    print("\n" + "="*70)
    print("TEST: Diagrams Disabled")
    print("="*70)
    
    with tempfile.TemporaryDirectory(prefix='diagram_test_') as work_dir:
        context = PipelineContext(
            input_file=Path('test.md'),
            output_file=Path('test.pdf'),
            work_dir=Path(work_dir),
            config={
                'enable_diagrams': False,  # DISABLED
                'verbose': True
            },
            verbose=True
        )
        
        context.preprocessed_markdown = TEST_MARKDOWN_SINGLE
        original = context.preprocessed_markdown
        
        step = DiagramRenderingStep()
        success = step.execute(context)
        
        result = context.preprocessed_markdown
        
        print(f"\nStep success: {success}")
        print(f"Content unchanged: {result == original}")
        print(f"Still has mermaid blocks: {'```mermaid' in result}")
        
        assert success, "Step should succeed"
        assert result == original, "Content should be unchanged"
        
        print("✓ Disabled diagrams test PASSED\n")
        return True


if __name__ == '__main__':
    print("\n" + "#" * 70)
    print("# Mermaid Diagram Rendering Test Suite")
    print("#" * 70)
    
    tests = [
        ('Single Diagram', test_diagram_rendering_step),
        ('Multiple Diagrams', test_multiple_diagrams),
        ('Diagrams Disabled', test_disabled_diagrams),
        ('Pipeline Integration', test_pipeline_integration),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}\n")
            results[name] = False
    
    # Summary
    print("\n" + "#" * 70)
    print("# Test Summary")
    print("#" * 70)
    
    for name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed\n")
    
    sys.exit(0 if passed == total else 1)
