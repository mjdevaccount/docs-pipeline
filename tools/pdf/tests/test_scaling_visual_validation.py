#!/usr/bin/env python3
"""
Visual Validation Test for Front Matter Scaling
================================================
Generates actual PDFs and validates scaling decisions match expectations.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_pdf.pipeline import generate_pdf
from playwright_pdf.config import PdfGenerationConfig

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
    FAIL = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    OK = "[OK]"
    FAIL = "[FAIL]"
    INFO = "[INFO]"
    WARN = "[WARN]"


# Test HTML with known structure and large diagrams
TEST_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Scaling Validation Test</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 20px; 
            max-width: 900px;
            margin: 0 auto;
        }
        h1 { font-size: 24pt; margin: 20px 0; }
        h2 { font-size: 20pt; margin: 15px 0; }
        p { margin: 10px 0; line-height: 1.6; }
        figure { margin: 20px 0; }
        svg { border: 1px solid #ccc; display: block; }
    </style>
</head>
<body>
    <h1 id="intro">Introduction</h1>
    <p>This document tests scaling behavior with front matter.</p>
    <p>We have several paragraphs of content before the first diagram to simulate real-world documents.</p>
    <p>This content should be accounted for when calculating available space for diagrams.</p>
    
    <h2 id="diagram-1">First Large Diagram</h2>
    <p>This diagram is intentionally large to test scaling behavior.</p>
    <figure>
        <svg width="1000" height="800" xmlns="http://www.w3.org/2000/svg">
            <rect width="1000" height="800" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
            <text x="500" y="400" text-anchor="middle" font-size="32" fill="#1976d2">
                Diagram 1: 1000x800px
            </text>
            <text x="500" y="440" text-anchor="middle" font-size="20" fill="#666">
                Should scale down significantly
            </text>
        </svg>
    </figure>
    
    <h2 id="diagram-2">Second Large Diagram</h2>
    <p>More content here to push this diagram further down.</p>
    <p>This tests how the system handles diagrams that appear later in the document.</p>
    <figure>
        <svg width="900" height="700" xmlns="http://www.w3.org/2000/svg">
            <rect width="900" height="700" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>
            <text x="450" y="350" text-anchor="middle" font-size="32" fill="#f57c00">
                Diagram 2: 900x700px
            </text>
            <text x="450" y="390" text-anchor="middle" font-size="20" fill="#666">
                Should also scale appropriately
            </text>
        </svg>
    </figure>
    
    <h2 id="diagram-3">Third Medium Diagram</h2>
    <p>This diagram is smaller and should require less scaling.</p>
    <figure>
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="#e8f5e9" stroke="#388e3c" stroke-width="2"/>
            <text x="300" y="200" text-anchor="middle" font-size="28" fill="#388e3c">
                Diagram 3: 600x400px
            </text>
            <text x="300" y="230" text-anchor="middle" font-size="18" fill="#666">
                Minimal scaling needed
            </text>
        </svg>
    </figure>
</body>
</html>"""


async def test_without_frontmatter():
    """Generate PDF without front matter and validate"""
    print(f"\n{INFO} Visual Test 1: PDF WITHOUT front matter")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_outputs"
    test_dir.mkdir(exist_ok=True)
    
    html_file = test_dir / "test_no_frontmatter.html"
    pdf_file = test_dir / "test_no_frontmatter.pdf"
    
    html_file.write_text(TEST_HTML, encoding='utf-8')
    
    config = PdfGenerationConfig(
        html_file=html_file,
        pdf_file=pdf_file,
        title="Scaling Test - No Front Matter",
        generate_cover=False,
        generate_toc=False,
        verbose=True
    )
    
    success = await generate_pdf(config)
    
    if success and pdf_file.exists():
        size_kb = pdf_file.stat().st_size / 1024
        print(f"\n{OK} PDF generated successfully: {pdf_file.name} ({size_kb:.1f} KB)")
        print(f"{INFO} Review PDF manually to verify scaling is appropriate")
        return True
    else:
        print(f"\n{FAIL} PDF generation failed")
        return False


async def test_with_frontmatter():
    """Generate PDF WITH front matter and validate"""
    print(f"\n{INFO} Visual Test 2: PDF WITH front matter (cover + TOC)")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_outputs"
    test_dir.mkdir(exist_ok=True)
    
    html_file = test_dir / "test_with_frontmatter.html"
    pdf_file = test_dir / "test_with_frontmatter.pdf"
    
    html_file.write_text(TEST_HTML, encoding='utf-8')
    
    config = PdfGenerationConfig(
        html_file=html_file,
        pdf_file=pdf_file,
        title="Scaling Test - With Front Matter",
        author="Test Author",
        organization="Test Organization",
        date="2025",
        generate_cover=True,
        generate_toc=True,
        verbose=True
    )
    
    success = await generate_pdf(config)
    
    if success and pdf_file.exists():
        size_kb = pdf_file.stat().st_size / 1024
        print(f"\n{OK} PDF generated successfully: {pdf_file.name} ({size_kb:.1f} KB)")
        print(f"{INFO} Review PDF manually to verify:")
        print(f"    1. Cover page appears first")
        print(f"    2. TOC appears second")
        print(f"    3. Diagrams are scaled appropriately accounting for front matter")
        print(f"    4. No diagrams are cut off or overlapping")
        return True
    else:
        print(f"\n{FAIL} PDF generation failed")
        return False


async def test_comparison():
    """Compare scaling between with/without front matter"""
    print(f"\n{INFO} Visual Test 3: Comparison Analysis")
    print("=" * 60)
    
    print(f"{WARN} Manual review required:")
    print(f"    1. Open both PDFs side-by-side")
    print(f"    2. Compare scaling of first diagram:")
    print(f"       - Without front matter: Should use full page height")
    print(f"       - With front matter: Should account for content after TOC")
    print(f"    3. Verify diagrams are readable and properly scaled")
    print(f"    4. Check that no content is cut off")
    
    return True


async def run_visual_tests():
    """Run all visual validation tests"""
    print("\n" + "=" * 60)
    print("VISUAL VALIDATION TEST SUITE")
    print("=" * 60)
    print(f"{INFO} These tests generate actual PDFs for manual review")
    
    results = []
    
    try:
        results.append(await test_without_frontmatter())
        results.append(await test_with_frontmatter())
        results.append(await test_comparison())
    except Exception as e:
        print(f"\n{FAIL} Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("VISUAL TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = OK if result else FAIL
        print(f"  Test {i}: {'PASSED' if result else 'FAILED'} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print(f"\n{INFO} PDFs generated in: tests/test_outputs/")
    print(f"{WARN} Please manually review PDFs to validate scaling behavior")
    
    if passed == total:
        print(f"\n{OK} All PDFs generated successfully!")
        return True
    else:
        print(f"\n{FAIL} Some tests failed. Review output above.")
        return False


if __name__ == '__main__':
    success = asyncio.run(run_visual_tests())
    sys.exit(0 if success else 1)

