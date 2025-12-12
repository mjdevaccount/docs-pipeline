#!/usr/bin/env python3
"""
Glossary CLI Commands
=====================

Command-line interface for glossary management:
- Validate glossary files
- Generate indexes
- Test highlighting
- Report on glossary usage

Usage:
    python -m tools.pdf.cli.glossary_commands validate glossary.yaml
    python -m tools.pdf.cli.glossary_commands index glossary.yaml --output glossary.md
    python -m tools.pdf.cli.glossary_commands highlight document.md glossary.yaml
    python -m tools.pdf.cli.glossary_commands report glossary.yaml
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.glossary_processor import GlossaryProcessor

logger = logging.getLogger(__name__)


def validate_command(args):
    """
    Validate glossary file for issues.
    
    Args:
        args: Parsed arguments
    """
    glossary_file = Path(args.glossary)
    if not glossary_file.exists():
        print(f"[ERROR] Glossary file not found: {glossary_file}")
        return False
    
    try:
        processor = GlossaryProcessor(glossary_file)
        issues = processor.validate_glossary()
        
        if not issues:
            print(f"[OK] Glossary is valid: {len(processor.terms)} terms")
            print(processor.report())
            return True
        else:
            print(f"[ERROR] Found {len(issues)} validation issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
    
    except Exception as e:
        print(f"[ERROR] Failed to validate glossary: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def index_command(args):
    """
    Generate glossary index.
    
    Args:
        args: Parsed arguments
    """
    glossary_file = Path(args.glossary)
    if not glossary_file.exists():
        print(f"[ERROR] Glossary file not found: {glossary_file}")
        return False
    
    try:
        processor = GlossaryProcessor(glossary_file)
        
        # Generate index
        index = processor.generate_index()
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            processor.generate_index_page(output_path)
            print(f"[OK] Generated glossary index: {output_path}")
        else:
            print(index)
        
        print(processor.report())
        return True
    
    except Exception as e:
        print(f"[ERROR] Failed to generate index: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def highlight_command(args):
    """
    Highlight glossary terms in document.
    
    Args:
        args: Parsed arguments
    """
    glossary_file = Path(args.glossary)
    document_file = Path(args.document)
    
    if not glossary_file.exists():
        print(f"[ERROR] Glossary file not found: {glossary_file}")
        return False
    
    if not document_file.exists():
        print(f"[ERROR] Document file not found: {document_file}")
        return False
    
    try:
        # Load glossary
        processor = GlossaryProcessor(glossary_file)
        
        # Read document
        document_content = document_file.read_text(encoding='utf-8')
        
        # Highlight terms
        highlighted = processor.highlight_terms(
            document_content,
            case_sensitive=args.case_sensitive,
            whole_words_only=not args.partial_words
        )
        
        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(highlighted, encoding='utf-8')
            print(f"[OK] Highlighted document: {output_path}")
        else:
            print(highlighted)
        
        # Show stats
        if processor.stats:
            print(f"\n{processor.stats.report()}")
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Failed to highlight document: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def report_command(args):
    """
    Generate glossary report.
    
    Args:
        args: Parsed arguments
    """
    glossary_file = Path(args.glossary)
    if not glossary_file.exists():
        print(f"[ERROR] Glossary file not found: {glossary_file}")
        return False
    
    try:
        processor = GlossaryProcessor(glossary_file)
        
        print(processor.report())
        
        if args.verbose:
            # Show all terms
            print(f"\nAll Terms:\n")
            for i, (term_name, term) in enumerate(sorted(processor.terms.items()), 1):
                print(f"{i}. {term_name}")
                if term.synonyms:
                    print(f"   Synonyms: {', '.join(term.synonyms)}")
                if term.category:
                    print(f"   Category: {term.category}")
                print(f"   Definition: {term.definition[:100]}...")
                print()
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def search_command(args):
    """
    Search glossary for terms.
    
    Args:
        args: Parsed arguments
    """
    glossary_file = Path(args.glossary)
    if not glossary_file.exists():
        print(f"[ERROR] Glossary file not found: {glossary_file}")
        return False
    
    try:
        processor = GlossaryProcessor(glossary_file)
        query = args.query.lower()
        
        matches = []
        for term_name, term in processor.terms.items():
            # Search in term name, definition, and synonyms
            if (query in term_name.lower() or
                query in term.definition.lower() or
                any(query in s.lower() for s in term.synonyms)):
                matches.append((term_name, term))
        
        if not matches:
            print(f"[INFO] No glossary terms match '{query}'")
            return True
        
        print(f"[INFO] Found {len(matches)} matching term(s):\n")
        for term_name, term in sorted(matches):
            print(f"### {term_name}")
            print(f"{term.definition}")
            if term.synonyms:
                print(f"Synonyms: {', '.join(term.synonyms)}")
            if term.category:
                print(f"Category: {term.category}")
            print()
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Failed to search glossary: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description='Glossary management commands',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate glossary
  python -m tools.pdf.cli.glossary_commands validate glossary.yaml
  
  # Generate index
  python -m tools.pdf.cli.glossary_commands index glossary.yaml --output glossary.md
  
  # Highlight terms in document
  python -m tools.pdf.cli.glossary_commands highlight doc.md glossary.yaml --output highlighted.md
  
  # Generate report
  python -m tools.pdf.cli.glossary_commands report glossary.yaml --verbose
  
  # Search glossary
  python -m tools.pdf.cli.glossary_commands search glossary.yaml API
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate glossary')
    validate_parser.add_argument('glossary', help='Glossary file (YAML/JSON)')
    validate_parser.add_argument('--verbose', '-v', action='store_true')
    validate_parser.set_defaults(func=validate_command)
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Generate glossary index')
    index_parser.add_argument('glossary', help='Glossary file')
    index_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    index_parser.add_argument('--verbose', '-v', action='store_true')
    index_parser.set_defaults(func=index_command)
    
    # Highlight command
    highlight_parser = subparsers.add_parser('highlight', help='Highlight terms in document')
    highlight_parser.add_argument('document', help='Document file')
    highlight_parser.add_argument('glossary', help='Glossary file')
    highlight_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    highlight_parser.add_argument('--case-sensitive', action='store_true')
    highlight_parser.add_argument('--partial-words', action='store_true',
                                 help='Match partial words')
    highlight_parser.add_argument('--verbose', '-v', action='store_true')
    highlight_parser.set_defaults(func=highlight_command)
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate glossary report')
    report_parser.add_argument('glossary', help='Glossary file')
    report_parser.add_argument('--verbose', '-v', action='store_true')
    report_parser.set_defaults(func=report_command)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search glossary')
    search_parser.add_argument('glossary', help='Glossary file')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--verbose', '-v', action='store_true')
    search_parser.set_defaults(func=search_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Run command
    success = args.func(args)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
