"""
Post-processing pipeline steps.
CSS stripping, title page injection, metadata injection.
"""
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class CSSStrippingStep(PipelineStep):
    """
    Strip Pandoc's inline styles from HTML.
    Removes default styling to allow custom CSS.
    """
    
    def get_name(self) -> str:
        return "CSS Stripping"
    
    def execute(self, context: PipelineContext) -> bool:
        """Strip inline styles from HTML"""
        if not context.html_content:
            self.log("No HTML content, skipping", context)
            return True
        
        try:
            # Remove inline style attributes
            html = context.html_content
            html = re.sub(r'\s+style="[^"]*"', '', html)
            
            # Remove Pandoc's default <style> block
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            
            context.html_content = html
            
            self.log("Stripped inline styles", context)
            return True
            
        except Exception as e:
            self.log(f"WARNING: CSS stripping failed: {e}", context)
            return True  # Non-critical


class TitlePageInjectionStep(PipelineStep):
    """
    Inject title page HTML for WeasyPrint renderer.
    Creates professional cover page with metadata.
    """
    
    def get_name(self) -> str:
        return "Title Page Injection"
    
    def execute(self, context: PipelineContext) -> bool:
        """Inject title page if using WeasyPrint"""
        renderer = context.get_config('renderer', 'playwright')
        generate_cover = context.get_config('generate_cover', False)
        
        # Skip for Playwright (handles cover page separately)
        if renderer == 'playwright':
            self.log("Playwright handles cover page, skipping", context)
            return True
        
        if not generate_cover:
            self.log("Cover page not requested, skipping", context)
            return True
        
        if not context.html_content:
            self.log("No HTML content, skipping", context)
            return True
        
        try:
            metadata = context.metadata
            logo_path = context.get_config('logo_path')
            
            # Build title page HTML
            title_html = self._build_title_page(metadata, logo_path)
            
            # Inject after <body>
            if '<body>' in context.html_content:
                context.html_content = context.html_content.replace(
                    '<body>',
                    f'<body>\n{title_html}'
                )
            elif '<body ' in context.html_content:
                # Handle body with attributes
                context.html_content = re.sub(
                    r'(<body[^>]*>)',
                    r'\1\n' + title_html,
                    context.html_content
                )
            
            self.log("Injected title page", context)
            return True
            
        except Exception as e:
            self.log(f"WARNING: Title page injection failed: {e}", context)
            return True  # Non-critical
    
    def _build_title_page(self, metadata: dict, logo_path: str = None) -> str:
        """Build title page HTML"""
        title = metadata.get('title', 'Document')
        author = metadata.get('author', '')
        organization = metadata.get('organization', '')
        date = metadata.get('date', '')
        version = metadata.get('version', '')
        doc_type = metadata.get('type', 'Technical Document')
        classification = metadata.get('classification', '')
        
        logo_html = ''
        if logo_path and Path(logo_path).exists():
            logo_html = f'''
            <div class="logo">
                <img src="{logo_path}" alt="Logo">
            </div>
            '''
        
        classification_html = ''
        if classification:
            classification_html = f'''
            <div class="classification">
                <p>{classification}</p>
            </div>
            '''
        
        return f'''
        <header class="title-page">
            {logo_html}
            <div class="title-block">
                <h1 class="doc-title">{title}</h1>
                <p class="doc-type">{doc_type}</p>
            </div>
            {classification_html}
            <div class="metadata-block">
                <p><strong>Author:</strong> {author}</p>
                <p><strong>Organization:</strong> {organization}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Version:</strong> {version}</p>
            </div>
            <div class="disclaimer">
                <p>This document contains proprietary information.</p>
            </div>
        </header>
        '''


class MetadataInjectionStep(PipelineStep):
    """
    Inject metadata as HTML meta tags.
    Used by Playwright renderer to read metadata from HTML.
    """
    
    def get_name(self) -> str:
        return "Metadata Injection"
    
    def execute(self, context: PipelineContext) -> bool:
        """Inject metadata as HTML meta tags"""
        renderer = context.get_config('renderer', 'playwright')
        
        # Only needed for Playwright
        if renderer != 'playwright':
            self.log("Not using Playwright, skipping", context)
            return True
        
        if not context.html_content:
            self.log("No HTML content, skipping", context)
            return True
        
        try:
            # Try new HTMLMetadataInjector first
            try:
                from metadata import HTMLMetadataInjector, DocumentMetadata
                
                injector = HTMLMetadataInjector()
                
                # Use metadata_obj if available, else create from dict
                if context.metadata_obj:
                    metadata_obj = context.metadata_obj
                else:
                    metadata_obj = DocumentMetadata.from_dict(context.metadata)
                
                # Inject into HTML string
                context.html_content = injector.inject_into_html(
                    context.html_content,
                    metadata_obj
                )
                
            except ImportError:
                # Fallback to manual injection
                self.log("Using legacy meta tag injection", context)
                context.html_content = self._legacy_inject(
                    context.html_content,
                    context.metadata
                )
            
            # Write updated HTML to file if it exists
            if context.html_file and context.html_file.exists():
                context.html_file.write_text(context.html_content, encoding='utf-8')
            
            self.log("Injected metadata as HTML meta tags", context)
            return True
            
        except Exception as e:
            self.log(f"WARNING: Metadata injection failed: {e}", context)
            return True  # Non-critical
    
    def _legacy_inject(self, html: str, metadata: dict) -> str:
        """Legacy meta tag injection"""
        import html as html_lib
        
        meta_tags = []
        
        for key in ['title', 'author', 'organization', 'date', 'version', 'type', 'classification']:
            value = metadata.get(key)
            if value:
                escaped = html_lib.escape(str(value))
                meta_tags.append(f'<meta name="{key}" content="{escaped}" />')
        
        if not meta_tags:
            return html
        
        meta_html = '\n    '.join(meta_tags)
        
        if '<head>' in html:
            return html.replace('<head>', f'<head>\n    {meta_html}', 1)
        elif '</head>' in html:
            return html.replace('</head>', f'    {meta_html}\n</head>', 1)
        else:
            return html.replace('<html>', f'<html>\n<head>\n    {meta_html}\n</head>', 1)

