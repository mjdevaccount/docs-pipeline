"""
Glossary Processor
==================

Processes document glossaries and highlights terms:
- Parse YAML glossary files
- Extract and validate terms
- Highlight terms in documents
- Generate indexes
- Create cross-references

Usage:
    from core.glossary_processor import GlossaryProcessor
    
    processor = GlossaryProcessor('glossary.yaml')
    
    # Highlight terms in markdown
    highlighted_md = processor.highlight_terms(markdown_content)
    
    # Generate index
    index = processor.generate_index()
"""

import yaml
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class GlossaryTerm:
    """A single glossary term with definition."""
    term: str                          # Term name (e.g., "API")
    definition: str                    # Definition text
    category: Optional[str] = None     # Category (e.g., "Technical")
    synonyms: List[str] = field(default_factory=list)  # Aliases
    see_also: List[str] = field(default_factory=list)  # Related terms
    example: Optional[str] = None      # Usage example
    
    def get_search_terms(self) -> Set[str]:
        """Get all terms to search for (term + synonyms)."""
        terms = {self.term.lower()}
        terms.update(s.lower() for s in self.synonyms)
        return terms
    
    def to_markdown(self) -> str:
        """Convert to markdown definition."""
        md = f"### {self.term}\n\n{self.definition}\n"
        
        if self.category:
            md += f"\n**Category**: {self.category}\n"
        
        if self.synonyms:
            md += f"\n**Also known as**: {', '.join(self.synonyms)}\n"
        
        if self.example:
            md += f"\n**Example**: {self.example}\n"
        
        if self.see_also:
            md += f"\n**See also**: {', '.join(self.see_also)}\n"
        
        return md


@dataclass
class GlossaryStats:
    """Statistics for glossary processing."""
    total_terms: int
    terms_found: int
    terms_highlighted: int
    occurrences: int
    categories: Dict[str, int] = field(default_factory=dict)
    
    def report(self) -> str:
        """Generate human-readable report."""
        if self.total_terms == 0:
            return "[INFO] No glossary terms found"
        
        coverage = (self.terms_found / self.total_terms) * 100
        
        return f"""\
[INFO] Glossary Processing Report
       Total Terms: {self.total_terms}
       Terms Found: {self.terms_found} ({coverage:.1f}% coverage)
       Total Occurrences: {self.occurrences}
       Highlighted: {self.terms_highlighted}"""


class GlossaryProcessor:
    """
    Process and highlight glossary terms in documents.
    
    Single Responsibility:
    - Load glossary from YAML/JSON
    - Parse and validate terms
    - Highlight terms in markdown
    - Generate indexes
    - Track usage statistics
    """
    
    def __init__(self, glossary_file: Optional[Path] = None):
        """
        Initialize glossary processor.
        
        Args:
            glossary_file: Path to glossary.yaml or glossary.json
        """
        self.glossary_file = glossary_file and Path(glossary_file)
        self.terms: Dict[str, GlossaryTerm] = {}
        self.term_index: Dict[str, str] = {}  # Maps lowercase term to canonical term
        self.stats = None
        
        if glossary_file:
            self.load_glossary(glossary_file)
    
    def load_glossary(self, glossary_file: Path):
        """
        Load glossary from YAML or JSON file.
        
        Args:
            glossary_file: Path to glossary file
            
        Raises:
            FileNotFoundError: If glossary file not found
            ValueError: If glossary format invalid
        """
        glossary_path = Path(glossary_file)
        if not glossary_path.exists():
            raise FileNotFoundError(f"Glossary file not found: {glossary_file}")
        
        try:
            with open(glossary_path) as f:
                if glossary_path.suffix.lower() == '.yaml':
                    data = yaml.safe_load(f)
                else:
                    import json
                    data = json.load(f)
            
            # Parse glossary data
            if isinstance(data, dict) and 'terms' in data:
                terms_data = data['terms']
            elif isinstance(data, list):
                terms_data = data
            else:
                raise ValueError("Glossary must have 'terms' key or be a list")
            
            # Load terms
            for term_data in terms_data:
                if isinstance(term_data, dict):
                    term = GlossaryTerm(
                        term=term_data.get('term', ''),
                        definition=term_data.get('definition', ''),
                        category=term_data.get('category'),
                        synonyms=term_data.get('synonyms', []),
                        see_also=term_data.get('see_also', []),
                        example=term_data.get('example')
                    )
                    
                    if term.term:
                        self.terms[term.term] = term
                        # Index all search terms
                        for search_term in term.get_search_terms():
                            self.term_index[search_term] = term.term
            
            logger.info(f"Loaded {len(self.terms)} terms from glossary")
        
        except Exception as e:
            logger.error(f"Failed to load glossary: {e}")
            raise
    
    def highlight_terms(
        self,
        markdown_content: str,
        case_sensitive: bool = False,
        whole_words_only: bool = True
    ) -> str:
        """
        Highlight glossary terms in markdown content.
        
        Args:
            markdown_content: Markdown text
            case_sensitive: Whether to match case
            whole_words_only: Only match complete words
            
        Returns:
            Markdown with highlighted terms
        """
        if not self.terms:
            logger.warning("No glossary terms loaded")
            return markdown_content
        
        result = markdown_content
        terms_found = set()
        occurrence_count = 0
        
        # Process each term
        for canonical_term, term_obj in self.terms.items():
            for search_term in term_obj.get_search_terms():
                # Build regex pattern
                if whole_words_only:
                    pattern = r'\b' + re.escape(search_term) + r'\b'
                else:
                    pattern = re.escape(search_term)
                
                flags = 0 if case_sensitive else re.IGNORECASE
                
                # Replace term with highlighted version
                # Avoid highlighting in code blocks
                def replacer(match):
                    nonlocal occurrence_count, terms_found
                    # Check if in code block
                    pos = match.start()
                    if self._in_code_block(result, pos):
                        return match.group(0)
                    
                    occurrence_count += 1
                    terms_found.add(canonical_term)
                    # Use reference-style link: [term]{glossary:canonical_term}
                    return f"[{match.group(0)}]{{glossary:{canonical_term}}}"
                
                result = re.sub(pattern, replacer, result, flags=flags)
        
        # Update stats
        self.stats = GlossaryStats(
            total_terms=len(self.terms),
            terms_found=len(terms_found),
            terms_highlighted=occurrence_count,
            occurrences=occurrence_count,
            categories=self._count_categories()
        )
        
        logger.info(f"Highlighted {occurrence_count} occurrences of {len(terms_found)} terms")
        return result
    
    def _in_code_block(self, content: str, position: int) -> bool:
        """Check if position is inside a code block."""
        # Count backticks before position
        before = content[:position]
        code_fence_count = before.count('```')
        inline_code_count = before.count('`') - (code_fence_count * 3)
        
        # If odd number of fences/backticks, we're inside code
        return (code_fence_count % 2 == 1) or (inline_code_count % 2 == 1)
    
    def _count_categories(self) -> Dict[str, int]:
        """Count terms by category."""
        counts = defaultdict(int)
        for term in self.terms.values():
            category = term.category or "Uncategorized"
            counts[category] += 1
        return dict(counts)
    
    def generate_index(self) -> str:
        """Generate markdown index of all glossary terms.
        
        Returns:
            Markdown-formatted index
        """
        if not self.terms:
            return "# Glossary\n\nNo terms defined.\n"
        
        # Group by category
        by_category = defaultdict(list)
        for term_name, term in sorted(self.terms.items()):
            category = term.category or "General"
            by_category[category].append((term_name, term))
        
        # Build markdown
        md = "# Glossary\n\n"
        md += "## Contents\n\n"
        
        # Table of contents
        for category in sorted(by_category.keys()):
            md += f"- [{category}](#{category.lower().replace(' ', '-')})\n"
        
        md += "\n---\n\n"
        
        # Term definitions by category
        for category in sorted(by_category.keys()):
            md += f"## {category}\n\n"
            for term_name, term in sorted(by_category[category]):
                md += term.to_markdown()
                md += "\n"
        
        return md
    
    def generate_index_page(self, output_file: Path):
        """
        Generate and save glossary index page.
        
        Args:
            output_file: Path to save index markdown
        """
        index_md = self.generate_index()
        output_file.write_text(index_md, encoding='utf-8')
        logger.info(f"Generated glossary index: {output_file}")
    
    def get_stats(self) -> Optional[GlossaryStats]:
        """Get statistics from last highlighting operation.
        
        Returns:
            GlossaryStats or None if no highlighting done yet
        """
        return self.stats
    
    def validate_glossary(self) -> List[str]:
        """Validate glossary for issues.
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        for term_name, term in self.terms.items():
            # Check for empty definitions
            if not term.definition or not term.definition.strip():
                issues.append(f"Term '{term_name}' has empty definition")
            
            # Check for broken cross-references
            for see_also in term.see_also:
                if see_also not in self.terms:
                    issues.append(f"Term '{term_name}' references undefined term '{see_also}'")
        
        return issues
    
    def report(self) -> str:
        """Generate comprehensive report.
        
        Returns:
            Formatted report
        """
        if not self.terms:
            return "[INFO] No glossary loaded"
        
        validation_issues = self.validate_glossary()
        
        report = f"[INFO] Glossary Report\n"
        report += f"       Total Terms: {len(self.terms)}\n"
        
        categories = self._count_categories()
        report += f"       Categories: {len(categories)}\n"
        
        for category, count in sorted(categories.items()):
            report += f"         - {category}: {count}\n"
        
        if validation_issues:
            report += f"\n[WARNING] Validation Issues: {len(validation_issues)}\n"
            for issue in validation_issues[:5]:  # Show first 5
                report += f"           - {issue}\n"
            if len(validation_issues) > 5:
                report += f"           ... and {len(validation_issues) - 5} more\n"
        
        if self.stats:
            report += f"\n{self.stats.report()}\n"
        
        return report
