"""
Post-Processing Module
======================
PDF metadata embedding and bookmark addition.
Pure file operations, no DOM, no browser.
"""
from pathlib import Path
from datetime import datetime
from typing import List, Optional

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    try:
        from pypdf import PdfReader, PdfWriter
        PYPDF2_AVAILABLE = True
    except ImportError:
        PYPDF2_AVAILABLE = False

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    WARN = "[WARN]"


def extract_headings_for_bookmarks(headings_data: List[dict]) -> List[dict]:
    """
    Convert headings data to bookmark format.
    This is a pure function, no DOM access.
    """
    return headings_data  # Already in the right format


async def extract_headings_from_page(page) -> List[dict]:
    """
    Extract headings with hierarchy for PDF bookmarks.
    Returns list of heading dictionaries with level, text, and id.
    """
    headings = await page.evaluate("""
        () => {
            const headings = [];
            const elements = document.querySelectorAll('h1, h2, h3, h4');
            
            elements.forEach((el, idx) => {
                if (!el.id) el.id = `heading-${idx}`;
                
                headings.push({
                    level: parseInt(el.tagName[1]),
                    text: el.textContent.trim(),
                    id: el.id
                });
            });
            
            return headings;
        }
    """)
    return headings


def add_bookmarks_to_pdf(pdf_file: str, headings: List[dict], verbose: bool = False) -> bool:
    """
    Add navigation bookmarks to PDF using PyPDF2/pypdf.
    Creates hierarchical bookmark structure from headings.
    """
    if not PYPDF2_AVAILABLE:
        if verbose:
            print(f"{WARN} PyPDF2/pypdf not installed, skipping bookmarks")
        return False
    
    try:
        reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Build hierarchical bookmark structure
        parent_bookmarks = {}
        
        for idx, heading in enumerate(headings):
            level = heading['level']
            text = heading['text']
            # Rough page estimate (would need actual page mapping for accuracy)
            page_num = min(idx, len(reader.pages) - 1)
            
            if level == 1:
                parent = writer.add_outline_item(text, page_num)
                parent_bookmarks[1] = parent
            elif level == 2:
                parent_1 = parent_bookmarks.get(1)
                if parent_1 is not None:
                    parent = writer.add_outline_item(text, page_num, parent_1)
                    parent_bookmarks[2] = parent
                else:
                    parent = writer.add_outline_item(text, page_num)
                    parent_bookmarks[2] = parent
            elif level == 3:
                parent_2 = parent_bookmarks.get(2)
                if parent_2 is not None:
                    writer.add_outline_item(text, page_num, parent_2)
                else:
                    parent_1 = parent_bookmarks.get(1)
                    if parent_1 is not None:
                        writer.add_outline_item(text, page_num, parent_1)
                    else:
                        writer.add_outline_item(text, page_num)
            elif level == 4:
                parent_3 = parent_bookmarks.get(3)
                if parent_3 is not None:
                    writer.add_outline_item(text, page_num, parent_3)
                else:
                    parent_2 = parent_bookmarks.get(2)
                    if parent_2 is not None:
                        writer.add_outline_item(text, page_num, parent_2)
                    else:
                        writer.add_outline_item(text, page_num)
        
        # Write updated PDF
        with open(pdf_file, 'wb') as f:
            writer.write(f)
        
        if verbose:
            print(f"{INFO} Added {len(headings)} bookmarks to PDF")
        return True
    except Exception as e:
        if verbose:
            print(f"{WARN} Failed to add bookmarks: {e}")
        return False


def embed_metadata(
    pdf_file: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    keywords: Optional[str] = None,
    verbose: bool = False
) -> bool:
    """
    Embed metadata in PDF using PyPDF2.
    """
    if not PYPDF2_AVAILABLE:
        if verbose:
            print(f"{WARN} PyPDF2 not installed, skipping metadata embedding")
        return False
    
    try:
        reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Add metadata
        metadata = {}
        if title:
            metadata['/Title'] = title
        if author:
            metadata['/Author'] = author
        if subject:
            metadata['/Subject'] = subject
        if keywords:
            metadata['/Keywords'] = keywords
        
        if metadata:
            metadata['/Creator'] = 'Playwright PDF Generator'
            metadata['/Producer'] = 'Chromium'
            metadata['/CreationDate'] = datetime.now().strftime("D:%Y%m%d%H%M%S")
            writer.add_metadata(metadata)
            
            # Write updated PDF
            with open(pdf_file, 'wb') as f:
                writer.write(f)
            
            if verbose:
                print(f"{INFO} Embedded PDF metadata")
            return True
        return False
    except Exception as e:
        if verbose:
            print(f"{WARN} Failed to embed metadata: {e}")
        return False

