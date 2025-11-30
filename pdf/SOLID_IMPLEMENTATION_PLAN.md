# SOLID Principles Implementation Plan

## Detailed Code Structure & Examples

This document provides concrete implementation examples for refactoring the codebase to follow SOLID principles.

---

## Phase 1: Core Interfaces & Abstractions

### 1.1 Core Interfaces (`pdf_tools/core/interfaces.py`)

```python
"""Core interfaces for PDF generation and document processing"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

class IPdfGenerator(ABC):
    """Abstract interface for PDF generation from HTML"""
    
    @abstractmethod
    async def generate(self, html_file: Path, pdf_file: Path, 
                      options: Dict[str, Any]) -> bool:
        """
        Generate PDF from HTML file
        
        Args:
            html_file: Path to input HTML file
            pdf_file: Path to output PDF file
            options: Generation options (format, margins, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """
        Check if generator supports a specific feature
        
        Args:
            feature: Feature name (e.g., 'foreignObject', 'bookmarks', 'watermarks')
        
        Returns:
            True if feature is supported
        """
        pass

class IPdfMetadataWriter(ABC):
    """Abstract interface for PDF metadata operations"""
    
    @abstractmethod
    def add_metadata(self, pdf_file: Path, metadata: Dict[str, str]) -> bool:
        """Add metadata to PDF file"""
        pass
    
    @abstractmethod
    def add_bookmarks(self, pdf_file: Path, headings: List[Dict[str, Any]]) -> bool:
        """Add navigation bookmarks to PDF"""
        pass

class IDiagramRenderer(ABC):
    """Abstract interface for diagram rendering"""
    
    @abstractmethod
    def render(self, diagram_code: str, output_format: str, 
              work_dir: Path, cache_dir: Optional[Path] = None,
              theme_config: Optional[Path] = None) -> Tuple[Path, bool]:
        """
        Render diagram to specified format
        
        Args:
            diagram_code: Source code of diagram
            output_format: Desired output format ('svg', 'png', etc.)
            work_dir: Working directory for temporary files
            cache_dir: Optional cache directory
            theme_config: Optional theme configuration file
        
        Returns:
            Tuple of (output_file_path, success_flag)
        """
        pass
    
    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """Check if renderer supports output format"""
        pass
    
    @abstractmethod
    def get_cache_key(self, diagram_code: str) -> str:
        """Generate cache key for diagram"""
        pass

class IDocumentConverter(ABC):
    """Abstract interface for document format conversion"""
    
    @abstractmethod
    def convert(self, input_file: Path, output_file: Path,
               options: Dict[str, Any]) -> bool:
        """Convert document from input to output format"""
        pass
    
    @abstractmethod
    def supports_input_format(self, format: str) -> bool:
        """Check if converter supports input format"""
        pass
    
    @abstractmethod
    def supports_output_format(self, format: str) -> bool:
        """Check if converter supports output format"""
        pass

class IPdfEnhancer(ABC):
    """Abstract interface for PDF enhancement features"""
    
    @abstractmethod
    async def enhance(self, page, options: Dict[str, Any]) -> bool:
        """Apply enhancement to PDF page"""
        pass

class ITocGenerator(IPdfEnhancer):
    """Table of contents generation"""
    pass

class ICoverPageGenerator(IPdfEnhancer):
    """Cover page generation"""
    pass

class IWatermarkApplier(IPdfEnhancer):
    """Watermark application"""
    pass

class ICssInjector(ABC):
    """CSS injection interface"""
    
    @abstractmethod
    async def inject(self, page, css_content: str) -> bool:
        """Inject CSS into page"""
        pass

class IFontInjector(ABC):
    """Font injection interface"""
    
    @abstractmethod
    async def inject(self, page, font_families: List[str]) -> bool:
        """Inject web fonts into page"""
        pass
```

### 1.2 Custom Exceptions (`pdf_tools/core/exceptions.py`)

```python
"""Custom exceptions for PDF tools"""

class PdfToolsException(Exception):
    """Base exception for PDF tools"""
    pass

class PdfGenerationError(PdfToolsException):
    """Error during PDF generation"""
    pass

class DiagramRenderingError(PdfToolsException):
    """Error during diagram rendering"""
    pass

class UnsupportedFormatError(PdfToolsException):
    """Unsupported format requested"""
    pass

class DependencyNotFoundError(PdfToolsException):
    """Required dependency not found"""
    pass

class ConfigurationError(PdfToolsException):
    """Configuration error"""
    pass
```

---

## Phase 2: PDF Generation Module

### 2.1 Base PDF Generator (`pdf_tools/pdf/generators/base_generator.py`)

```python
"""Base class for PDF generators"""
from abc import ABC
from pathlib import Path
from typing import Dict, Any, Optional
from pdf_tools.core.interfaces import IPdfGenerator, IPdfMetadataWriter
from pdf_tools.core.exceptions import PdfGenerationError

class BasePdfGenerator(IPdfGenerator, ABC):
    """Base implementation for PDF generators"""
    
    def __init__(self, metadata_writer: Optional[IPdfMetadataWriter] = None):
        """
        Initialize PDF generator
        
        Args:
            metadata_writer: Optional metadata writer for PDF operations
        """
        self._metadata_writer = metadata_writer
    
    def supports_feature(self, feature: str) -> bool:
        """Default implementation - override in subclasses"""
        return False
    
    async def _add_metadata_if_available(self, pdf_file: Path, 
                                       metadata: Dict[str, str]) -> bool:
        """Helper to add metadata if writer is available"""
        if self._metadata_writer:
            return self._metadata_writer.add_metadata(pdf_file, metadata)
        return False
```

### 2.2 Playwright Generator (`pdf_tools/pdf/generators/playwright_generator.py`)

```python
"""Playwright-based PDF generator"""
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
from pdf_tools.pdf.generators.base_generator import BasePdfGenerator
from pdf_tools.pdf.enhancers import ITocGenerator, ICoverPageGenerator
from pdf_tools.pdf.processors import ICssInjector, IFontInjector
from pdf_tools.core.exceptions import PdfGenerationError, DependencyNotFoundError

class PlaywrightPdfGenerator(BasePdfGenerator):
    """Playwright-based PDF generator with perfect SVG support"""
    
    def __init__(
        self,
        metadata_writer: Optional[IPdfMetadataWriter] = None,
        toc_generator: Optional[ITocGenerator] = None,
        cover_generator: Optional[ICoverPageGenerator] = None,
        css_injector: Optional[ICssInjector] = None,
        font_injector: Optional[IFontInjector] = None
    ):
        """
        Initialize Playwright PDF generator with dependency injection
        
        Args:
            metadata_writer: PDF metadata writer
            toc_generator: Table of contents generator
            cover_generator: Cover page generator
            css_injector: CSS injection processor
            font_injector: Font injection processor
        """
        super().__init__(metadata_writer)
        self._toc_generator = toc_generator
        self._cover_generator = cover_generator
        self._css_injector = css_injector
        self._font_injector = font_injector
    
    def supports_feature(self, feature: str) -> bool:
        """Check supported features"""
        supported = {
            'foreignObject': True,
            'bookmarks': self._metadata_writer is not None,
            'watermarks': True,
            'toc': self._toc_generator is not None,
            'cover': self._cover_generator is not None,
        }
        return supported.get(feature, False)
    
    async def generate(self, html_file: Path, pdf_file: Path, 
                      options: Dict[str, Any]) -> bool:
        """Generate PDF using Playwright"""
        try:
            async with async_playwright() as p:
                browser = await self._launch_browser(p, options)
                page = await browser.new_page()
                
                # Load HTML
                await self._load_html(page, html_file)
                
                # Apply enhancements
                await self._apply_enhancements(page, options)
                
                # Generate PDF
                await page.pdf(path=str(pdf_file), **self._build_pdf_options(options))
                
                await browser.close()
                
                # Add metadata if available
                if options.get('metadata'):
                    await self._add_metadata_if_available(pdf_file, options['metadata'])
                
                return pdf_file.exists()
        except Exception as e:
            raise PdfGenerationError(f"Playwright PDF generation failed: {e}") from e
    
    async def _launch_browser(self, playwright, options: Dict[str, Any]) -> Browser:
        """Launch browser with options"""
        browser_args = options.get('browser_args', [
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
        ])
        return await playwright.chromium.launch(
            headless=True,
            args=browser_args
        )
    
    async def _load_html(self, page: Page, html_file: Path):
        """Load HTML file into page"""
        html_path = html_file.absolute()
        file_url = f"file:///{str(html_path).replace(chr(92), '/')}"
        await page.goto(file_url, wait_until='networkidle', timeout=30000)
    
    async def _apply_enhancements(self, page: Page, options: Dict[str, Any]):
        """Apply all enhancements using injected dependencies"""
        # Inject fonts
        if self._font_injector and options.get('fonts'):
            await self._font_injector.inject(page, options['fonts'])
        
        # Inject CSS
        if self._css_injector and options.get('css'):
            await self._css_injector.inject(page, options['css'])
        
        # Generate cover page
        if self._cover_generator and options.get('generate_cover'):
            await self._cover_generator.enhance(page, options)
        
        # Generate TOC
        if self._toc_generator and options.get('generate_toc'):
            await self._toc_generator.enhance(page, options)
    
    def _build_pdf_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build PDF generation options"""
        default_options = {
            'format': 'A4',
            'print_background': True,
            'display_header_footer': options.get('display_header_footer', True),
            'margin': options.get('margin', {
                'top': '0.75in',
                'right': '0.75in',
                'bottom': '0.75in',
                'left': '0.75in'
            })
        }
        default_options.update(options.get('pdf_options', {}))
        return default_options
```

### 2.3 PDF Enhancers (`pdf_tools/pdf/enhancers/__init__.py`)

```python
"""PDF enhancement modules"""
from pdf_tools.pdf.enhancers.toc_generator import TocGenerator
from pdf_tools.pdf.enhancers.cover_page_generator import CoverPageGenerator
from pdf_tools.pdf.enhancers.watermark_applier import WatermarkApplier

__all__ = [
    'TocGenerator',
    'CoverPageGenerator',
    'WatermarkApplier',
]
```

### 2.4 TOC Generator (`pdf_tools/pdf/enhancers/toc_generator.py`)

```python
"""Table of contents generator"""
from typing import Dict, Any
from playwright.async_api import Page
from pdf_tools.core.interfaces import ITocGenerator
from pdf_tools.core.exceptions import PdfGenerationError

class TocGenerator(ITocGenerator):
    """Generate table of contents for PDF"""
    
    async def enhance(self, page: Page, options: Dict[str, Any]) -> bool:
        """Generate and inject TOC"""
        try:
            await page.evaluate("""
                () => {
                    const headings = document.querySelectorAll('h1, h2, h3');
                    if (headings.length === 0) return false;
                    
                    let toc = '<div class="toc-wrapper">';
                    toc += '<h1>Table of Contents</h1>';
                    toc += '<ul>';
                    
                    headings.forEach((heading, idx) => {
                        const level = parseInt(heading.tagName[1]);
                        const text = heading.textContent.trim();
                        const id = heading.id || `heading-${idx}`;
                        if (!heading.id) heading.id = id;
                        
                        const indent = (level - 1) * 20;
                        toc += `<li style="margin-left: ${indent}px;">`;
                        toc += `<a href="#${id}">${text}</a></li>`;
                    });
                    
                    toc += '</ul></div>';
                    
                    const coverPage = document.querySelector('.cover-page-wrapper');
                    if (coverPage) {
                        coverPage.insertAdjacentHTML('afterend', toc);
                    } else {
                        document.body.insertAdjacentHTML('afterbegin', toc);
                    }
                    
                    return true;
                }
            """)
            return True
        except Exception as e:
            raise PdfGenerationError(f"TOC generation failed: {e}") from e
```

---

## Phase 3: Diagram Rendering Module

### 3.1 Base Diagram Renderer (`pdf_tools/diagrams/renderers/base_renderer.py`)

```python
"""Base class for diagram renderers"""
from abc import ABC
from pathlib import Path
from typing import Optional, Tuple
import hashlib
from pdf_tools.core.interfaces import IDiagramRenderer
from pdf_tools.core.exceptions import DiagramRenderingError

class BaseDiagramRenderer(IDiagramRenderer, ABC):
    """Base implementation for diagram renderers"""
    
    def __init__(self, cache_dir: Optional[Path] = None, use_cache: bool = True):
        """
        Initialize diagram renderer
        
        Args:
            cache_dir: Optional cache directory
            use_cache: Whether to use caching
        """
        self._cache_dir = cache_dir
        self._use_cache = use_cache
    
    def get_cache_key(self, diagram_code: str) -> str:
        """Generate cache key from diagram code"""
        return hashlib.md5(diagram_code.encode()).hexdigest()[:8]
    
    def _get_cached_file(self, cache_key: str, extension: str) -> Optional[Path]:
        """Get cached file if available"""
        if not self._use_cache or not self._cache_dir:
            return None
        
        cached_file = self._cache_dir / f"{cache_key}.{extension}"
        return cached_file if cached_file.exists() else None
    
    def _save_to_cache(self, cache_key: str, file_path: Path, extension: str):
        """Save file to cache"""
        if self._use_cache and self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cached_file = self._cache_dir / f"{cache_key}.{extension}"
            import shutil
            shutil.copy2(file_path, cached_file)
```

### 3.2 Mermaid Renderer (`pdf_tools/diagrams/renderers/mermaid_renderer.py`)

```python
"""Mermaid diagram renderer"""
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from pdf_tools.diagrams.renderers.base_renderer import BaseDiagramRenderer
from pdf_tools.core.exceptions import DiagramRenderingError, DependencyNotFoundError

class MermaidRenderer(BaseDiagramRenderer):
    """Renderer for Mermaid diagrams"""
    
    def __init__(self, cache_dir: Optional[Path] = None, 
                 use_cache: bool = True, theme_config: Optional[Path] = None):
        """
        Initialize Mermaid renderer
        
        Args:
            cache_dir: Cache directory for rendered diagrams
            use_cache: Whether to use caching
            theme_config: Optional theme configuration file
        """
        super().__init__(cache_dir, use_cache)
        self._theme_config = theme_config
        self._mmdc_exe = self._find_mmdc_executable()
    
    def supports_format(self, format: str) -> bool:
        """Mermaid supports SVG and PNG"""
        return format in ['svg', 'png']
    
    def render(self, diagram_code: str, output_format: str, 
              work_dir: Path, cache_dir: Optional[Path] = None,
              theme_config: Optional[Path] = None) -> Tuple[Path, bool]:
        """
        Render Mermaid diagram
        
        Args:
            diagram_code: Mermaid diagram source code
            output_format: Output format ('svg' or 'png')
            work_dir: Working directory for temp files
            cache_dir: Override cache directory
            theme_config: Override theme config
        
        Returns:
            Tuple of (output_file_path, success_flag)
        """
        cache_key = self.get_cache_key(diagram_code)
        theme = theme_config or self._theme_config
        
        # Check cache first
        if cache_dir:
            cached = self._get_cached_file(cache_key, output_format)
            if cached:
                work_file = work_dir / f"diagram_{cache_key}.{output_format}"
                import shutil
                shutil.copy2(cached, work_file)
                return work_file, True
        
        # Render diagram
        try:
            mmd_file = work_dir / f"diagram_{cache_key}.mmd"
            output_file = work_dir / f"diagram_{cache_key}.{output_format}"
            
            mmd_file.write_text(diagram_code, encoding='utf-8')
            
            cmd = [
                self._mmdc_exe,
                '-i', str(mmd_file),
                '-o', str(output_file),
                '-t', 'neutral',
                '-b', 'transparent' if output_format == 'svg' else 'white'
            ]
            
            if theme:
                cmd.extend(['-c', str(theme)])
            
            result = subprocess.run(cmd, check=True, capture_output=True, 
                                  text=True, shell=True)
            
            if output_file.exists():
                # Save to cache
                if cache_dir:
                    self._save_to_cache(cache_key, output_file, output_format)
                return output_file, True
            else:
                return output_file, False
                
        except subprocess.CalledProcessError as e:
            raise DiagramRenderingError(
                f"Mermaid rendering failed: {e.stderr}"
            ) from e
        except Exception as e:
            raise DiagramRenderingError(
                f"Unexpected error during Mermaid rendering: {e}"
            ) from e
    
    def _find_mmdc_executable(self) -> str:
        """Find Mermaid CLI executable"""
        import shutil
        # Try common Windows locations
        windows_paths = [
            Path.home() / r'AppData\Roaming\npm\mmdc.cmd',
            Path.home() / r'AppData\Roaming\npm\mmdc',
        ]
        
        for path in windows_paths:
            if path.exists():
                return str(path)
        
        # Try PATH
        mmdc = shutil.which('mmdc') or shutil.which('mmdc.cmd')
        if mmdc:
            return mmdc
        
        raise DependencyNotFoundError(
            "Mermaid CLI (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli"
        )
```

### 3.3 Diagram Renderer Factory (`pdf_tools/diagrams/renderers/factory.py`)

```python
"""Factory for creating diagram renderers"""
from typing import Dict, Type, Optional
from pathlib import Path
from pdf_tools.core.interfaces import IDiagramRenderer
from pdf_tools.diagrams.renderers.mermaid_renderer import MermaidRenderer
from pdf_tools.diagrams.renderers.plantuml_renderer import PlantUmlRenderer
from pdf_tools.diagrams.renderers.graphviz_renderer import GraphvizRenderer

class DiagramRendererFactory:
    """Factory for creating diagram renderers"""
    
    _renderers: Dict[str, Type[IDiagramRenderer]] = {
        'mermaid': MermaidRenderer,
        'plantuml': PlantUmlRenderer,
        'graphviz': GraphvizRenderer,
    }
    
    @classmethod
    def create(cls, diagram_type: str, **kwargs) -> IDiagramRenderer:
        """
        Create renderer for diagram type
        
        Args:
            diagram_type: Type of diagram ('mermaid', 'plantuml', 'graphviz')
            **kwargs: Renderer-specific arguments
        
        Returns:
            Diagram renderer instance
        
        Raises:
            ValueError: If diagram type is unknown
        """
        if diagram_type not in cls._renderers:
            raise ValueError(
                f"Unknown diagram type: {diagram_type}. "
                f"Supported types: {', '.join(cls._renderers.keys())}"
            )
        return cls._renderers[diagram_type](**kwargs)
    
    @classmethod
    def register(cls, diagram_type: str, renderer_class: Type[IDiagramRenderer]):
        """
        Register new renderer type (OCP - open for extension)
        
        Args:
            diagram_type: Type identifier
            renderer_class: Renderer class implementing IDiagramRenderer
        """
        cls._renderers[diagram_type] = renderer_class
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of supported diagram types"""
        return list(cls._renderers.keys())
```

---

## Phase 4: Document Converter Module

### 4.1 Markdown Converter (`pdf_tools/converters/markdown_converter.py`)

```python
"""Markdown document converter"""
from pathlib import Path
from typing import Dict, Any, List
from pdf_tools.core.interfaces import IDocumentConverter, IDiagramRenderer
from pdf_tools.diagrams.renderers.factory import DiagramRendererFactory
from pdf_tools.utils.metadata_extractor import MetadataExtractor
from pdf_tools.utils.glossary_expander import GlossaryExpander
from pdf_tools.core.exceptions import UnsupportedFormatError

class MarkdownConverter(IDocumentConverter):
    """Convert Markdown to various formats"""
    
    def __init__(
        self,
        diagram_renderers: Dict[str, IDiagramRenderer] = None,
        metadata_extractor: MetadataExtractor = None,
        glossary_expander: GlossaryExpander = None
    ):
        """
        Initialize Markdown converter
        
        Args:
            diagram_renderers: Dictionary of diagram type -> renderer
            metadata_extractor: Metadata extraction utility
            glossary_expander: Glossary expansion utility
        """
        self._diagram_renderers = diagram_renderers or {}
        self._metadata_extractor = metadata_extractor or MetadataExtractor()
        self._glossary_expander = glossary_expander or GlossaryExpander()
    
    def supports_input_format(self, format: str) -> bool:
        """Markdown converter supports markdown input"""
        return format.lower() in ['markdown', 'md']
    
    def supports_output_format(self, format: str) -> bool:
        """Check if output format is supported"""
        return format.lower() in ['pdf', 'docx', 'html']
    
    def convert(self, input_file: Path, output_file: Path,
               options: Dict[str, Any]) -> bool:
        """
        Convert Markdown file to output format
        
        Args:
            input_file: Input Markdown file
            output_file: Output file path
            options: Conversion options
        
        Returns:
            True if successful
        """
        output_format = options.get('format') or self._detect_format(output_file)
        
        if not self.supports_output_format(output_format):
            raise UnsupportedFormatError(
                f"Unsupported output format: {output_format}"
            )
        
        # Extract metadata
        md_content = input_file.read_text(encoding='utf-8')
        metadata, content = self._metadata_extractor.extract(md_content)
        
        # Expand glossary if provided
        if options.get('glossary_file'):
            content = self._glossary_expander.expand(
                content, Path(options['glossary_file'])
            )
        
        # Render diagrams
        content = self._render_diagrams(content, options)
        
        # Convert to target format
        if output_format == 'pdf':
            return self._convert_to_pdf(content, output_file, metadata, options)
        elif output_format == 'docx':
            return self._convert_to_docx(content, output_file, metadata, options)
        elif output_format == 'html':
            return self._convert_to_html(content, output_file, metadata, options)
        
        return False
    
    def _render_diagrams(self, content: str, options: Dict[str, Any]) -> str:
        """Render all diagrams in content"""
        import re
        import tempfile
        
        work_dir = Path(tempfile.mkdtemp())
        
        def render_diagram(match):
            diagram_type = match.group(1)
            diagram_code = match.group(2)
            
            # Get renderer for diagram type
            renderer = self._diagram_renderers.get(diagram_type)
            if not renderer:
                # Try factory
                try:
                    renderer = DiagramRendererFactory.create(
                        diagram_type,
                        cache_dir=options.get('cache_dir'),
                        use_cache=options.get('use_cache', True),
                        theme_config=options.get('theme_config')
                    )
                except ValueError:
                    return match.group(0)  # Return original if unsupported
            
            # Render diagram
            output_format = 'svg' if options.get('format') != 'docx' else 'png'
            output_file, success = renderer.render(
                diagram_code, output_format, work_dir,
                cache_dir=options.get('cache_dir'),
                theme_config=options.get('theme_config')
            )
            
            if success:
                return f'![Diagram]({output_file.name})'
            else:
                return match.group(0)
        
        # Replace mermaid blocks
        content = re.sub(
            r'```mermaid\n(.+?)```',
            lambda m: render_diagram(m),
            content,
            flags=re.DOTALL
        )
        
        return content
    
    def _detect_format(self, output_file: Path) -> str:
        """Detect format from file extension"""
        ext = output_file.suffix.lower()
        format_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.html': 'html',
            '.htm': 'html',
        }
        return format_map.get(ext, 'pdf')
    
    def _convert_to_pdf(self, content: str, output_file: Path,
                       metadata: Dict[str, Any], options: Dict[str, Any]) -> bool:
        """Convert to PDF - delegate to PDF converter"""
        from pdf_tools.converters.pdf_converter import PdfConverter
        converter = PdfConverter()
        # Create temporary markdown file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_md = Path(f.name)
        
        try:
            return converter.convert(temp_md, output_file, {**options, 'metadata': metadata})
        finally:
            temp_md.unlink()
    
    def _convert_to_docx(self, content: str, output_file: Path,
                         metadata: Dict[str, Any], options: Dict[str, Any]) -> bool:
        """Convert to DOCX"""
        # Implementation similar to PDF
        pass
    
    def _convert_to_html(self, content: str, output_file: Path,
                         metadata: Dict[str, Any], options: Dict[str, Any]) -> bool:
        """Convert to HTML"""
        # Implementation
        pass
```

---

## Phase 5: Dependency Injection Container

### 5.1 Simple DI Container (`pdf_tools/core/container.py`)

```python
"""Simple dependency injection container"""
from typing import Dict, Type, Any, Callable, Optional
from pathlib import Path

class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, name: str, instance: Any):
        """Register singleton instance"""
        self._singletons[name] = instance
    
    def register_factory(self, name: str, factory: Callable):
        """Register factory function"""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get service instance"""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check factories
        if name in self._factories:
            instance = self._factories[name]()
            # Cache as singleton if not already cached
            if name not in self._services:
                self._services[name] = instance
            return instance
        
        # Check services
        if name in self._services:
            return self._services[name]
        
        raise ValueError(f"Service '{name}' not registered")
    
    def configure_defaults(self, config: Dict[str, Any]):
        """Configure default services"""
        # Register PDF generators
        from pdf_tools.pdf.generators.playwright_generator import PlaywrightPdfGenerator
        from pdf_tools.pdf.generators.weasyprint_generator import WeasyPrintPdfGenerator
        
        self.register_factory('pdf_generator.playwright', 
                             lambda: PlaywrightPdfGenerator())
        self.register_factory('pdf_generator.weasyprint',
                             lambda: WeasyPrintPdfGenerator())
        
        # Register diagram renderers
        cache_dir = config.get('cache_dir')
        theme_config = config.get('theme_config')
        
        from pdf_tools.diagrams.renderers.mermaid_renderer import MermaidRenderer
        self.register_factory('diagram_renderer.mermaid',
                             lambda: MermaidRenderer(
                                 cache_dir=cache_dir,
                                 theme_config=theme_config
                             ))
        
        # Register converters
        from pdf_tools.converters.markdown_converter import MarkdownConverter
        self.register_factory('converter.markdown',
                             lambda: MarkdownConverter())
```

---

## Usage Examples

### Example 1: Using Refactored PDF Generator

```python
"""Example: Using refactored PDF generator"""
from pathlib import Path
from pdf_tools.pdf.generators.playwright_generator import PlaywrightPdfGenerator
from pdf_tools.pdf.enhancers import TocGenerator, CoverPageGenerator
from pdf_tools.pdf.processors import CssInjector, FontInjector
from pdf_tools.pdf.metadata import PyPdfMetadataWriter

# Create dependencies
toc_gen = TocGenerator()
cover_gen = CoverPageGenerator()
css_injector = CssInjector()
font_injector = FontInjector()
metadata_writer = PyPdfMetadataWriter()

# Create generator with injected dependencies
generator = PlaywrightPdfGenerator(
    metadata_writer=metadata_writer,
    toc_generator=toc_gen,
    cover_generator=cover_gen,
    css_injector=css_injector,
    font_injector=font_injector
)

# Generate PDF
import asyncio
async def main():
    success = await generator.generate(
        html_file=Path('input.html'),
        pdf_file=Path('output.pdf'),
        options={
            'generate_toc': True,
            'generate_cover': True,
            'fonts': ['Inter', 'Source Code Pro'],
            'metadata': {
                'title': 'My Document',
                'author': 'John Doe'
            }
        }
    )
    print(f"PDF generated: {success}")

asyncio.run(main())
```

### Example 2: Extending with Custom Diagram Renderer

```python
"""Example: Adding custom diagram renderer (OCP)"""
from pdf_tools.core.interfaces import IDiagramRenderer
from pdf_tools.diagrams.renderers.base_renderer import BaseDiagramRenderer
from pdf_tools.diagrams.renderers.factory import DiagramRendererFactory
from pathlib import Path
from typing import Optional, Tuple

class CustomDiagramRenderer(BaseDiagramRenderer):
    """Custom diagram renderer"""
    
    def supports_format(self, format: str) -> bool:
        return format == 'svg'
    
    def render(self, diagram_code: str, output_format: str,
              work_dir: Path, cache_dir: Optional[Path] = None,
              theme_config: Optional[Path] = None) -> Tuple[Path, bool]:
        # Custom rendering logic
        output_file = work_dir / 'custom_diagram.svg'
        output_file.write_text('<svg>...</svg>')
        return output_file, True

# Register custom renderer (no modification of core code!)
DiagramRendererFactory.register('custom', CustomDiagramRenderer)

# Use it
renderer = DiagramRendererFactory.create('custom')
output, success = renderer.render('diagram code', 'svg', Path('/tmp'))
```

### Example 3: Using DI Container

```python
"""Example: Using dependency injection container"""
from pdf_tools.core.container import DIContainer

# Configure container
container = DIContainer()
container.configure_defaults({
    'cache_dir': Path('./cache'),
    'theme_config': Path('./theme.json')
})

# Get services
pdf_gen = container.get('pdf_generator.playwright')
mermaid_renderer = container.get('diagram_renderer.mermaid')
converter = container.get('converter.markdown')

# Use services
success = converter.convert(
    Path('input.md'),
    Path('output.pdf'),
    {'format': 'pdf'}
)
```

---

## Migration Guide

### Step 1: Update Imports

**Before:**
```python
from pdf_playwright import generate_pdf_from_html
```

**After:**
```python
from pdf_tools.pdf.generators.playwright_generator import PlaywrightPdfGenerator
from pdf_tools.pdf.enhancers import TocGenerator, CoverPageGenerator
```

### Step 2: Update Function Calls

**Before:**
```python
await generate_pdf_from_html(
    html_file, pdf_file,
    title="Title",
    author="Author",
    generate_toc=True,
    generate_cover=True
)
```

**After:**
```python
generator = PlaywrightPdfGenerator(
    toc_generator=TocGenerator(),
    cover_generator=CoverPageGenerator()
)

await generator.generate(
    html_file, pdf_file,
    options={
        'title': 'Title',
        'author': 'Author',
        'generate_toc': True,
        'generate_cover': True
    }
)
```

---

## Testing Strategy

### Unit Tests Example

```python
"""Unit tests for PDF generator"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from pdf_tools.pdf.generators.playwright_generator import PlaywrightPdfGenerator

@pytest.fixture
def mock_toc_generator():
    return Mock(spec=ITocGenerator)

@pytest.fixture
def mock_cover_generator():
    return Mock(spec=ICoverPageGenerator)

@pytest.fixture
def pdf_generator(mock_toc_generator, mock_cover_generator):
    return PlaywrightPdfGenerator(
        toc_generator=mock_toc_generator,
        cover_generator=mock_cover_generator
    )

@pytest.mark.asyncio
async def test_generate_pdf(pdf_generator, mock_toc_generator, mock_cover_generator):
    """Test PDF generation"""
    html_file = Path('test.html')
    pdf_file = Path('test.pdf')
    
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        # Mock Playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        
        # Mock TOC and cover generators
        mock_toc_generator.enhance = AsyncMock(return_value=True)
        mock_cover_generator.enhance = AsyncMock(return_value=True)
        
        # Generate PDF
        success = await pdf_generator.generate(
            html_file, pdf_file,
            options={'generate_toc': True, 'generate_cover': True}
        )
        
        assert success
        mock_toc_generator.enhance.assert_called_once()
        mock_cover_generator.enhance.assert_called_once()
```

---

## Summary

This implementation plan provides:

1. **Clear Interfaces**: Abstract base classes define contracts
2. **Single Responsibility**: Each class has one clear purpose
3. **Dependency Injection**: Dependencies are injected, not hard-coded
4. **Open/Closed**: Extend functionality via plugins/factories
5. **Interface Segregation**: Focused interfaces instead of fat ones

The refactored codebase will be:
- ✅ More maintainable
- ✅ Easier to test
- ✅ More extensible
- ✅ Better organized
- ✅ Following SOLID principles

