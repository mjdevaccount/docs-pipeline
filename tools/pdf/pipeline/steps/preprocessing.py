"""
Preprocessing pipeline steps.
Read content, extract metadata, expand glossary, render math.
"""
import re
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class ReadContentStep(PipelineStep):
    """
    Read raw markdown content from input file.
    This is typically the first step in any pipeline.
    """
    
    def get_name(self) -> str:
        return "Read Content"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure input file exists"""
        if not context.input_file.exists():
            raise PipelineError(f"Input file not found: {context.input_file}")
    
    def execute(self, context: PipelineContext) -> bool:
        """Read markdown content from input file"""
        try:
            context.raw_content = context.input_file.read_text(encoding='utf-8')
            context.preprocessed_markdown = context.raw_content
            
            self.log(f"Read {len(context.raw_content)} characters", context)
            return True
            
        except Exception as e:
            raise PipelineError(f"Failed to read input file: {e}")


class MetadataExtractionStep(PipelineStep):
    """
    Extract and merge metadata from frontmatter, overrides, and defaults.
    Uses the metadata module for SOLID-compliant extraction.
    """
    
    def get_name(self) -> str:
        return "Metadata Extraction"
    
    def execute(self, context: PipelineContext) -> bool:
        """Extract metadata using metadata module"""
        try:
            # Ensure we have content to process
            if not context.raw_content:
                context.raw_content = context.input_file.read_text(encoding='utf-8')
            
            # Try new architecture first
            try:
                from metadata import (
                    MetadataExtractor, MetadataValidator, 
                    MetadataMerger, MetadataDefaults, DocumentMetadata
                )
                
                # Extract frontmatter
                extractor = MetadataExtractor()
                frontmatter_dict, content = extractor.extract_from_string(context.raw_content)
                
                # Validate frontmatter dict
                validator = MetadataValidator()
                if frontmatter_dict:
                    frontmatter_dict = validator.validate(frontmatter_dict)
                
                # Get defaults as DocumentMetadata object
                defaults = MetadataDefaults.get_defaults()
                
                # Validate and prepare overrides dict
                overrides = context.get_config('custom_metadata', {})
                if overrides:
                    overrides = validator.validate(overrides)
                
                # Merge using dicts (merger expects dicts, not DocumentMetadata)
                merger = MetadataMerger()
                metadata_obj = merger.merge(
                    frontmatter=frontmatter_dict,
                    overrides=overrides if overrides else None,
                    defaults=defaults
                )
                
                # Store in context
                context.metadata = metadata_obj.to_dict()
                context.metadata_obj = metadata_obj
                context.preprocessed_markdown = content
                
            except ImportError:
                # Fallback to legacy extraction
                self.log("Using legacy metadata extraction", context)
                context.metadata, context.preprocessed_markdown = self._legacy_extract(
                    context.raw_content
                )
            
            self.log(f"Extracted {len(context.metadata)} metadata fields", context)
            return True
            
        except Exception as e:
            raise PipelineError(f"Metadata extraction failed: {e}")
    
    def _legacy_extract(self, content: str) -> tuple:
        """Legacy YAML frontmatter extraction"""
        import yaml
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    content_clean = parts[2].strip()
                    return metadata if metadata else {}, content_clean
                except:
                    pass
        return {}, content


class GlossaryExpansionStep(PipelineStep):
    """
    Expand glossary terms and acronyms in markdown.
    Replaces first occurrence of terms with full definitions.
    """
    
    def get_name(self) -> str:
        return "Glossary Expansion"
    
    def execute(self, context: PipelineContext) -> bool:
        """Expand glossary if provided"""
        glossary_file = context.get_config('glossary_file')
        
        if not glossary_file:
            self.log("No glossary file configured, skipping", context)
            return True
        
        glossary_path = Path(glossary_file)
        if not glossary_path.exists():
            self.log(f"Glossary file not found: {glossary_file}, skipping", context)
            return True
        
        try:
            context.preprocessed_markdown = self._expand_glossary(
                context.preprocessed_markdown,
                glossary_path
            )
            self.log(f"Expanded glossary from {glossary_file}", context)
            return True
            
        except Exception as e:
            self.log(f"WARNING: Glossary expansion failed: {e}", context)
            return True  # Non-critical failure
    
    def _expand_glossary(self, content: str, glossary_path: Path) -> str:
        """Inline glossary expansion"""
        import yaml
        
        try:
            glossary = yaml.safe_load(glossary_path.read_text(encoding='utf-8'))
            
            if not glossary or 'terms' not in glossary:
                return content
            
            for term_def in glossary.get('terms', []):
                term = term_def.get('term', '')
                definition = term_def.get('definition', '')
                
                if term and definition:
                    # Replace first occurrence with term + definition
                    pattern = r'\b' + re.escape(term) + r'\b'
                    replacement = f"{term} ({definition})"
                    content = re.sub(pattern, replacement, content, count=1)
            
            return content
            
        except Exception:
            return content


class MathRenderingStep(PipelineStep):
    """
    Pre-render math equations with KaTeX.
    Converts $inline$ and $$display$$ math to HTML.
    """
    
    def get_name(self) -> str:
        return "Math Rendering"
    
    def execute(self, context: PipelineContext) -> bool:
        """Render math with KaTeX if present"""
        if not context.get_config('enable_math', True):
            self.log("Math rendering disabled, skipping", context)
            return True
        
        if '$' not in context.preprocessed_markdown:
            self.log("No math detected, skipping", context)
            return True
        
        try:
            from external_tools import KatexCLI, ToolNotFoundError
            
            try:
                katex = KatexCLI()
            except (ToolNotFoundError, ImportError):
                self.log("KaTeX not available, skipping math rendering", context)
                return True
            
            # Count math expressions for logging
            math_count = 0
            
            def replace_math(match):
                nonlocal math_count
                display_math = match.group(1)
                inline_math = match.group(2)
                
                is_display = display_math is not None
                math_code = display_math or inline_math
                
                try:
                    if is_display:
                        html = katex.render_display(math_code)
                    else:
                        html = katex.render_inline(math_code)
                    
                    if html:
                        math_count += 1
                        tag = 'div' if is_display else 'span'
                        cls = 'math-display' if is_display else 'math-inline'
                        return f'<{tag} class="{cls}">{html}</{tag}>'
                except Exception:
                    pass
                
                return match.group(0)
            
            # Match $$...$$ (display) and $...$ (inline)
            pattern = r'\$\$([^\$]+)\$\$|\$([^\$]+)\$'
            context.preprocessed_markdown = re.sub(
                pattern,
                replace_math,
                context.preprocessed_markdown
            )
            
            self.log(f"Rendered {math_count} math equations", context)
            return True
            
        except Exception as e:
            self.log(f"WARNING: Math rendering failed: {e}", context)
            return True  # Non-critical

