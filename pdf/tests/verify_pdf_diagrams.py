"""
Verify PDF Diagrams - Manual Verification Helper
=================================================

This script helps you verify that diagrams are rendering correctly in the PDF.
"""

from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
PDF_FILE = REPO_ROOT / "tools/pdf/tests/test_outputs/reporting-manager-architecture-proposal.playwright.pdf"
CACHE_DIR = REPO_ROOT / "tools/pdf/tests/test_outputs/diagram_cache"

def main():
    print("=" * 80)
    print("PDF Diagram Verification")
    print("=" * 80)
    print()
    
    # Check if PDF exists
    if not PDF_FILE.exists():
        print(f"❌ PDF not found: {PDF_FILE}")
        print("Run: python tools/pdf/tests/test_reporting_manager_layout.py")
        return
    
    print(f"✅ PDF found: {PDF_FILE}")
    print(f"   Size: {PDF_FILE.stat().st_size / 1024:.1f} KB")
    print()
    
    # Check diagram cache
    if CACHE_DIR.exists():
        svg_files = list(CACHE_DIR.glob("*.svg"))
        print(f"✅ Diagram cache: {len(svg_files)} SVG files")
        print()
        
        # Show SVG sizes
        print("Diagram Sizes (from SVG files):")
        print("-" * 80)
        for svg_file in sorted(svg_files):
            content = svg_file.read_text(encoding='utf-8')
            
            # Extract width and height
            import re
            width_match = re.search(r'width="([\d.]+)"', content)
            height_match = re.search(r'height="([\d.]+)"', content)
            
            if width_match and height_match:
                width = float(width_match.group(1))
                height = float(height_match.group(1))
                print(f"  {svg_file.name}: {width:.0f}px × {height:.0f}px")
        print()
    
    print("=" * 80)
    print("MANUAL VERIFICATION STEPS")
    print("=" * 80)
    print()
    print(f"1. Open PDF: {PDF_FILE}")
    print()
    print("2. Check each page for diagrams:")
    print("   ✅ Diagrams are visible (not missing)")
    print("   ✅ Text is readable (11px font)")
    print("   ✅ Spacing looks professional (not too loose)")
    print("   ✅ Diagrams fit on pages (not cut off)")
    print("   ✅ Colors are correct (blue, green, orange)")
    print()
    print("3. Expected diagrams:")
    print("   - Page 3-4: Current System Overview (flowchart)")
    print("   - Page 4-5: System Context (flowchart)")
    print("   - Page 6-7: Architecture Overview (flowchart)")
    print("   - Page 7-8: Job Execution Flow (sequence diagram)")
    print("   - Page 8-9: Failure Detection (state diagram)")
    print()
    print("4. If diagrams are MISSING:")
    print("   ❌ Check if HTML has broken image references")
    print("   ❌ Check if SVG files are in wrong location")
    print("   ❌ Check Playwright console for errors")
    print()
    print("5. If diagrams are TOO SMALL:")
    print("   ❌ Theme settings may be too aggressive")
    print("   ❌ Try increasing nodeSpacing/rankSpacing")
    print()
    print("6. If diagrams are TOO LARGE:")
    print("   ✅ This is what we fixed! Should be compact now.")
    print()
    print("=" * 80)
    print("QUICK TEST")
    print("=" * 80)
    print()
    print(f"Open this file in your browser to see the HTML version:")
    html_file = PDF_FILE.parent / "reporting-manager-architecture-proposal.html"
    if html_file.exists():
        print(f"  file:///{html_file.as_posix()}")
        print()
        print("If diagrams show in HTML but not PDF, it's a Playwright rendering issue.")
        print("If diagrams don't show in HTML, it's a diagram generation issue.")
    print()


if __name__ == "__main__":
    main()

