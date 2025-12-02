"""
Pandoc executor wrapper with platform-independent resolution.
"""
from pathlib import Path
from typing import List, Optional
import platform

from .base import ExternalTool


class PandocExecutor(ExternalTool):
    """
    Pandoc wrapper for Markdown conversion.
    
    Provides platform-independent Pandoc executable resolution
    and a convenient API for common conversion operations.
    """
    
    def _get_executable_names(self) -> List[str]:
        """Get platform-specific Pandoc executable names."""
        if platform.system().lower() == 'windows':
            return ['pandoc.exe', 'pandoc']
        return ['pandoc']
    
    def _get_search_paths(self) -> List[Path]:
        """Get common Pandoc installation paths."""
        system = platform.system().lower()
        paths = []
        
        if system == 'windows':
            paths.extend([
                Path('C:/Program Files/Pandoc'),
                Path('C:/Program Files (x86)/Pandoc'),
                Path.home() / 'AppData' / 'Local' / 'Pandoc',
            ])
        elif system == 'darwin':  # macOS
            paths.extend([
                Path('/usr/local/bin'),
                Path('/opt/homebrew/bin'),
            ])
        else:  # Linux
            paths.extend([
                Path('/usr/bin'),
                Path('/usr/local/bin'),
            ])
        
        # Common paths
        paths.append(Path.home() / '.local' / 'bin')
        
        return paths
    
    def convert_markdown_to_html(
        self,
        input_file: Path,
        output_file: Path,
        markdown_format: str = 'markdown',
        extensions: Optional[List[str]] = None,
        standalone: bool = True,
        toc: bool = True,
        toc_depth: int = 3,
        highlight_style: str = 'pygments',
        resource_path: Optional[Path] = None,
        extra_args: Optional[List[str]] = None
    ) -> bool:
        """
        Convert Markdown to HTML using Pandoc.
        
        Args:
            input_file: Input markdown file
            output_file: Output HTML file
            markdown_format: Base markdown format (default: 'markdown')
            extensions: Optional list of Pandoc extensions to enable
            standalone: Generate standalone HTML document
            toc: Generate table of contents
            toc_depth: TOC depth level
            highlight_style: Syntax highlighting style
            resource_path: Resource search path for images/assets
            extra_args: Additional Pandoc arguments
            
        Returns:
            True if conversion succeeded, False otherwise
        """
        # Build format string with extensions
        if extensions:
            format_str = f"{markdown_format}+{'+'.join(extensions)}"
        else:
            format_str = markdown_format
        
        args = [
            str(input_file),
            '-f', format_str,
            '-t', 'html5',
            '-o', str(output_file)
        ]
        
        if standalone:
            args.append('--standalone')
        
        if toc:
            args.extend(['--toc', f'--toc-depth={toc_depth}'])
        
        if highlight_style:
            args.extend(['--highlight-style', highlight_style])
        
        if resource_path:
            args.extend(['--resource-path', str(resource_path)])
        
        # Add mathjax for math rendering
        args.append('--mathjax')
        
        if extra_args:
            args.extend(extra_args)
        
        result = self.execute(args, check=False)
        return result.success
    
    def convert_markdown_to_docx(
        self,
        input_file: Path,
        output_file: Path,
        markdown_format: str = 'markdown',
        extensions: Optional[List[str]] = None,
        reference_docx: Optional[Path] = None,
        toc: bool = True,
        toc_depth: int = 3,
        highlight_style: str = 'pygments',
        resource_path: Optional[Path] = None,
        extra_args: Optional[List[str]] = None
    ) -> bool:
        """
        Convert Markdown to DOCX using Pandoc.
        
        Args:
            input_file: Input markdown file
            output_file: Output DOCX file
            markdown_format: Base markdown format
            extensions: Optional list of Pandoc extensions
            reference_docx: Optional reference DOCX template
            toc: Generate table of contents
            toc_depth: TOC depth level
            highlight_style: Syntax highlighting style
            resource_path: Resource search path
            extra_args: Additional arguments
            
        Returns:
            True if conversion succeeded, False otherwise
        """
        # Build format string
        if extensions:
            format_str = f"{markdown_format}+{'+'.join(extensions)}"
        else:
            format_str = markdown_format
        
        args = [
            str(input_file),
            '-f', format_str,
            '-t', 'docx',
            '-o', str(output_file)
        ]
        
        if toc:
            args.extend(['--toc', f'--toc-depth={toc_depth}'])
        
        if highlight_style:
            args.extend(['--highlight-style', highlight_style])
        
        if resource_path:
            args.extend(['--resource-path', str(resource_path)])
        
        if reference_docx and reference_docx.exists():
            args.extend(['--reference-doc', str(reference_docx)])
        
        if extra_args:
            args.extend(extra_args)
        
        result = self.execute(args, check=False)
        return result.success
    
    def get_default_markdown_extensions(self) -> List[str]:
        """
        Get recommended Pandoc markdown extensions.
        
        Returns:
            List of extension names for feature-rich markdown parsing
        """
        return [
            'pipe_tables',
            'backtick_code_blocks',
            'fenced_code_attributes',
            'smart',
            'tex_math_dollars',  # $...$ and $$...$$
            'tex_math_double_backslash',  # \[...\] and \(...\)
            'raw_html',
            'fenced_code_blocks',
            'autolink_bare_uris',
            'strikeout',  # ~~text~~
            'superscript',  # ^text^
            'subscript',  # ~text~
        ]

