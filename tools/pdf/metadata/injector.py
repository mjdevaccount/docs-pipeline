"""
Inject metadata as HTML <meta> tags for Playwright renderer.
"""
from pathlib import Path
from .models import DocumentMetadata


class HTMLMetadataInjector:
    """
    Inject metadata as HTML <meta> tags for Playwright PDF pipeline.
    
    The Playwright renderer extracts these meta tags to populate
    cover page, headers, and footers.
    
    Example:
        injector = HTMLMetadataInjector()
        injector.inject_into_file(html_file, metadata)
    """
    
    def inject_into_file(self, html_file: Path, metadata: DocumentMetadata) -> None:
        """
        Inject metadata into HTML file.
        
        Args:
            html_file: Path to HTML file to modify
            metadata: Metadata to inject
        """
        html_content = Path(html_file).read_text(encoding='utf-8')
        modified_html = self.inject_into_string(html_content, metadata)
        Path(html_file).write_text(modified_html, encoding='utf-8')
    
    def inject_into_string(self, html_content: str, metadata: DocumentMetadata) -> str:
        """
        Inject metadata into HTML string.
        
        Args:
            html_content: HTML content
            metadata: Metadata to inject
        
        Returns:
            Modified HTML with injected meta tags
        """
        meta_tags = self._generate_meta_tags(metadata)
        
        if not meta_tags:
            return html_content
        
        meta_html = '\n    '.join(meta_tags)
        
        # Try to insert into <head>
        if '<head>' in html_content:
            return html_content.replace('<head>', f'<head>\n    {meta_html}', 1)
        elif '</head>' in html_content:
            return html_content.replace('</head>', f'    {meta_html}\n</head>', 1)
        elif '<html>' in html_content:
            # No head tag, create one
            return html_content.replace('<html>', f'<html>\n<head>\n    {meta_html}\n</head>', 1)
        else:
            # No html tag either, prepend
            return f'<!DOCTYPE html>\n<html>\n<head>\n    {meta_html}\n</head>\n<body>\n{html_content}\n</body>\n</html>'
    
    def _generate_meta_tags(self, metadata: DocumentMetadata) -> list:
        """Generate HTML <meta> tags from metadata"""
        meta_tags = []
        
        # Standard fields
        if metadata.title:
            meta_tags.append(f'<meta name="title" content="{self._escape_html(metadata.title)}" />')
        if metadata.author:
            meta_tags.append(f'<meta name="author" content="{self._escape_html(metadata.author)}" />')
        if metadata.organization:
            meta_tags.append(f'<meta name="organization" content="{self._escape_html(metadata.organization)}" />')
        if metadata.date:
            meta_tags.append(f'<meta name="date" content="{self._escape_html(metadata.date)}" />')
        if metadata.version:
            meta_tags.append(f'<meta name="version" content="{self._escape_html(metadata.version)}" />')
        if metadata.type:
            meta_tags.append(f'<meta name="type" content="{self._escape_html(metadata.type)}" />')
        if metadata.classification:
            meta_tags.append(f'<meta name="classification" content="{self._escape_html(metadata.classification)}" />')
        
        # Optional enhanced fields
        if metadata.department:
            meta_tags.append(f'<meta name="department" content="{self._escape_html(metadata.department)}" />')
        if metadata.review_status:
            meta_tags.append(f'<meta name="review_status" content="{self._escape_html(metadata.review_status)}" />')
        if metadata.doc_id:
            meta_tags.append(f'<meta name="doc_id" content="{self._escape_html(metadata.doc_id)}" />')
        if metadata.prepared_for:
            meta_tags.append(f'<meta name="prepared_for" content="{self._escape_html(metadata.prepared_for)}" />')
        
        # Custom fields
        for key, value in metadata.custom.items():
            if value:
                meta_tags.append(f'<meta name="{self._escape_html(key)}" content="{self._escape_html(str(value))}" />')
        
        return meta_tags
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML entities for safe injection"""
        return (
            str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
        )

