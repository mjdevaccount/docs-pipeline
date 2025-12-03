"""
Script to generate profile screenshots from PDFs.
Converts the first page of each profile PDF to a PNG image.
"""

import sys
from pathlib import Path

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    try:
        import fitz  # PyMuPDF
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

def convert_pdf_to_image_pdf2image(pdf_path, output_path, dpi=150):
    """Convert first page of PDF to image using pdf2image"""
    images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
    if images:
        images[0].save(output_path, 'PNG')
        return True
    return False

def convert_pdf_to_image_pymupdf(pdf_path, output_path, page_num=6, zoom=3.0):
    """Convert a specific page of PDF to image using PyMuPDF
    
    Args:
        pdf_path: Path to PDF file
        output_path: Path to save PNG image
        page_num: Page number to extract (0-indexed, default 6 = 7th page with code blocks)
        zoom: Zoom factor for higher quality (default 3.0 = 3x for better quality)
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # Use page 6 (7th page) which has code blocks that show profile differences well
    # Page 6 typically has "Code Examples" section with syntax highlighting
    target_page = min(page_num, total_pages - 1)
    
    if total_pages > 0:
        page = doc[target_page]
        # Use higher zoom for better quality and ensure color mode
        mat = fitz.Matrix(zoom, zoom)
        # Create pixmap in RGB color mode (not grayscale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        # Save as PNG with color
        pix.save(output_path)
        doc.close()
        print(f"    Using page {target_page + 1} with {zoom}x zoom (RGB color mode)")
        return True
    doc.close()
    return False

def main():
    profiles = [
        ('tech-whitepaper', 'tech-whitepaper-example'),
        ('dark-pro', 'dark-pro-example'),
        ('minimalist', 'minimalist-example'),
        ('enterprise-blue', 'enterprise-blue-example')
    ]
    
    # Check if we have the PDFs in output/ or use existing ones
    base_dir = Path(__file__).parent
    output_dir = base_dir / 'output'
    images_dir = base_dir / 'docs' / 'images'
    examples_dir = base_dir / 'docs' / 'examples' / 'generated'
    
    images_dir.mkdir(exist_ok=True)
    
    # Try to find PDFs - check output/ first, then examples/generated/
    pdf_base = None
    if (output_dir / 'profile-tech-whitepaper.pdf').exists():
        pdf_base = output_dir / 'profile-'
        pdf_suffix = '.pdf'
    elif (examples_dir / 'showcase-tech.pdf').exists():
        # Use existing generated PDFs
        pdf_base = examples_dir / 'showcase-'
        pdf_suffix = '.pdf'
    else:
        print("ERROR: No PDFs found. Please generate PDFs first.")
        print("Run: python -m tools.pdf.convert_final docs/examples/advanced-markdown-showcase.md output.pdf --profile <profile>")
        return 1
    
    print("Converting PDFs to images...")
    
    for profile_name, image_name in profiles:
        if pdf_base.name == 'profile-':
            pdf_path = pdf_base.parent / f'profile-{profile_name}.pdf'
        else:
            # Map profile names to existing PDF names
            profile_map = {
                'tech-whitepaper': 'tech',
                'dark-pro': 'dark',
                'minimalist': 'minimalist',
                'enterprise-blue': 'enterprise'
            }
            pdf_name = profile_map.get(profile_name, profile_name)
            pdf_path = examples_dir / f'showcase-{pdf_name}.pdf'
        
        if not pdf_path.exists():
            print(f"  WARNING: {pdf_path} not found, skipping...")
            continue
        
        output_path = images_dir / f'{image_name}.png'
        
        print(f"  Converting {profile_name}...")
        
        success = False
        if PDF2IMAGE_AVAILABLE:
            try:
                success = convert_pdf_to_image_pdf2image(str(pdf_path), str(output_path))
            except Exception as e:
                print(f"    pdf2image failed: {e}")
        
        if not success and PYMUPDF_AVAILABLE:
            try:
                # Use page 2 (3rd page) which has colored Mermaid diagrams that show profile differences best
                success = convert_pdf_to_image_pymupdf(str(pdf_path), str(output_path), page_num=2, zoom=3.0)
            except Exception as e:
                print(f"    PyMuPDF failed: {e}")
        
        if success:
            print(f"    SUCCESS: {output_path}")
        else:
            print(f"    ERROR: Could not convert {pdf_path}")
            print("    Install pdf2image or PyMuPDF:")
            print("      pip install pdf2image  # Requires poppler")
            print("      pip install pymupdf")
            return 1
    
    print("\nAll screenshots created successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())

