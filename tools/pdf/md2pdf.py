#!/usr/bin/env python3
"""
md2pdf.py - Backward-compatible CLI wrapper
============================================

This script provides backward compatibility for the md2pdf command.
The implementation has been refactored to tools/pdf/cli/main.py.

Usage:
    python tools/pdf/md2pdf.py input.md output.pdf [options]
    
For programmatic use, prefer the pipeline API:
    from tools.pdf.convert_final import markdown_to_pdf
    markdown_to_pdf('input.md', 'output.pdf', profile='tech-whitepaper')
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cli.main import main

if __name__ == "__main__":
    main()



