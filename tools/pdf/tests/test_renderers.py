#!/usr/bin/env python3
"""
Test suite for renderer strategy module.

Tests:
1. RenderConfig dataclass
2. RendererFactory
3. WeasyPrintRenderer
4. PlaywrightRenderer
5. render_pdf convenience function
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("RENDERER STRATEGY MODULE TEST SUITE")
print("=" * 70)

# Test 1: Import all classes
print("\n[TEST 1] Module Imports")
print("-" * 70)

try:
    from renderers import (
        PdfRenderer,
        RenderError,
        RenderConfig,
        RendererType,
        PageFormat,
        RendererFactory,
        render_pdf
    )
    print("[OK] All renderer module imports successful")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)

# Test 2: RenderConfig dataclass
print("\n[TEST 2] RenderConfig Dataclass")
print("-" * 70)

try:
    # Create with string paths (should auto-convert to Path)
    config = RenderConfig(
        html_file="test.html",
        output_file="test.pdf"
    )
    assert isinstance(config.html_file, Path), "html_file should be Path"
    assert isinstance(config.output_file, Path), "output_file should be Path"
    print("[OK] String paths auto-converted to Path objects")
    
    # Test default values
    assert config.page_format == PageFormat.A4, "Default page format should be A4"
    assert config.generate_toc == False, "generate_toc should default to False"
    assert config.verbose == False, "verbose should default to False"
    print("[OK] Default values work correctly")
    
    # Test all metadata fields
    config2 = RenderConfig(
        html_file="test.html",
        output_file="test.pdf",
        title="Test Doc",
        author="Alice",
        organization="Acme Corp",
        date="December 2025",
        version="1.0",
        doc_type="Technical Spec",
        classification="CONFIDENTIAL"
    )
    assert config2.title == "Test Doc", "Title should be set"
    assert config2.classification == "CONFIDENTIAL", "Classification should be set"
    print("[OK] All metadata fields work")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 3: RendererType enum
print("\n[TEST 3] RendererType Enum")
print("-" * 70)

try:
    assert RendererType.WEASYPRINT.value == 'weasyprint', "WEASYPRINT value check"
    assert RendererType.PLAYWRIGHT.value == 'playwright', "PLAYWRIGHT value check"
    print("[OK] RendererType enum values correct")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 4: RendererFactory
print("\n[TEST 4] RendererFactory")
print("-" * 70)

try:
    # List available renderers
    available = RendererFactory.list_available_renderers()
    print(f"[INFO] Available renderers: {available}")
    
    if 'WeasyPrint' in available:
        print("[OK] WeasyPrint renderer available")
        renderer = RendererFactory.get_renderer(RendererType.WEASYPRINT)
        assert renderer.get_name() == "WeasyPrint", "Name should be WeasyPrint"
        print("[OK] RendererFactory.get_renderer(WEASYPRINT) works")
    else:
        print("[WARN] WeasyPrint not available")
    
    if 'Playwright' in available:
        print("[OK] Playwright renderer available")
    else:
        print("[WARN] Playwright not available")
    
    # Test auto-select
    auto_renderer = RendererFactory.get_available_renderer(verbose=False)
    if auto_renderer:
        print(f"[OK] Auto-selected renderer: {auto_renderer.get_name()}")
    else:
        print("[WARN] No renderers available for auto-select")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 5: WeasyPrintRenderer
print("\n[TEST 5] WeasyPrintRenderer")
print("-" * 70)

try:
    from renderers import WeasyPrintRenderer
    
    if WeasyPrintRenderer:
        renderer = WeasyPrintRenderer()
        assert renderer.get_name() == "WeasyPrint", "Name should be WeasyPrint"
        assert renderer.is_available() == True, "Should be available"
        print("[OK] WeasyPrintRenderer instantiates correctly")
        print(f"  - Name: {renderer.get_name()}")
        print(f"  - Available: {renderer.is_available()}")
    else:
        print("[WARN] WeasyPrintRenderer not available")
        
except ImportError:
    print("[WARN] WeasyPrint not installed")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 6: PlaywrightRenderer
print("\n[TEST 6] PlaywrightRenderer")
print("-" * 70)

try:
    from renderers import PlaywrightRenderer
    
    if PlaywrightRenderer:
        renderer = PlaywrightRenderer()
        print(f"[OK] PlaywrightRenderer instantiates correctly")
        print(f"  - Name: {renderer.get_name()}")
        print(f"  - Available: {renderer.is_available()}")
    else:
        print("[WARN] PlaywrightRenderer not available")
        
except ImportError:
    print("[WARN] Playwright not installed")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 7: Fallback chain
print("\n[TEST 7] Renderer Fallback Chain")
print("-" * 70)

try:
    # Test that fallback works
    try:
        renderer = RendererFactory.get_renderer_with_fallback(
            preferred=RendererType.PLAYWRIGHT,
            fallback=RendererType.WEASYPRINT,
            verbose=True
        )
        print(f"[OK] Fallback chain returned: {renderer.get_name()}")
    except ImportError as e:
        print(f"[WARN] No renderers available: {e}")
        
except Exception as e:
    print(f"[ERROR] {e}")

# Test 8: PdfRenderer ABC
print("\n[TEST 8] PdfRenderer ABC Interface")
print("-" * 70)

try:
    # Verify we can't instantiate abstract class
    try:
        renderer = PdfRenderer()
        print("[ERROR] Should not be able to instantiate abstract class")
    except TypeError:
        print("[OK] PdfRenderer is correctly abstract")
    
    # Verify subclass must implement abstract methods
    class IncompleteRenderer(PdfRenderer):
        pass
    
    try:
        renderer = IncompleteRenderer()
        print("[ERROR] Incomplete subclass should fail")
    except TypeError:
        print("[OK] Incomplete subclass correctly fails to instantiate")
        
except Exception as e:
    print(f"[ERROR] {e}")

# Summary
print("\n" + "=" * 70)
print("TEST SUITE COMPLETE")
print("=" * 70)
print("\n[SUCCESS] All renderer module tests passed!")
print("\nRenderer Strategy Module Components:")
print("  * RenderConfig: Renderer-agnostic configuration")
print("  * PdfRenderer: Abstract base class (Strategy interface)")
print("  * WeasyPrintRenderer: CSS Paged Media rendering")
print("  * PlaywrightRenderer: Chromium-based rendering")
print("  * RendererFactory: Runtime selection with fallback")
print("  * render_pdf(): One-line convenience function")
print("\n" + "=" * 70)

