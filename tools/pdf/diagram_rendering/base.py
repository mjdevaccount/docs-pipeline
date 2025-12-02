"""
Base abstractions for diagram rendering.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class DiagramFormat(Enum):
    """Supported diagram output formats."""
    SVG = 'svg'
    PNG = 'png'


@dataclass
class RenderResult:
    """Result of diagram rendering operation."""
    success: bool
    output_file: Optional[Path] = None
    error_message: Optional[str] = None
    from_cache: bool = False
    
    @property
    def failed(self) -> bool:
        """Check if rendering failed."""
        return not self.success


class DiagramRenderer(ABC):
    """
    Abstract base class for diagram renderers.
    
    Follows Open/Closed Principle:
    - Open for extension: Add new diagram types by subclassing
    - Closed for modification: Existing renderers don't need changes
    
    Each renderer is responsible for:
    1. Identifying if it can render a diagram (can_render)
    2. Validating diagram syntax
    3. Rendering to requested format (SVG/PNG)
    4. Error handling
    """
    
    @abstractmethod
    def can_render(self, diagram_code: str, format_hint: Optional[str] = None) -> bool:
        """
        Check if this renderer can handle the diagram.
        
        Args:
            diagram_code: Diagram source code
            format_hint: Optional format hint (e.g., 'mermaid', 'plantuml')
            
        Returns:
            True if this renderer can handle the diagram
        """
        pass
    
    @abstractmethod
    def validate(self, diagram_code: str) -> bool:
        """
        Validate diagram syntax.
        
        Args:
            diagram_code: Diagram source code
            
        Returns:
            True if diagram syntax is valid
        """
        pass
    
    @abstractmethod
    def render(
        self,
        diagram_code: str,
        output_file: Path,
        format: DiagramFormat = DiagramFormat.SVG,
        **options
    ) -> RenderResult:
        """
        Render diagram to file.
        
        Args:
            diagram_code: Diagram source code
            output_file: Output file path
            format: Output format (SVG or PNG)
            **options: Renderer-specific options
            
        Returns:
            RenderResult with success status and output file
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list[DiagramFormat]:
        """
        Get list of formats this renderer supports.
        
        Returns:
            List of supported DiagramFormat values
        """
        pass
    
    def get_name(self) -> str:
        """
        Get renderer name for logging/debugging.
        
        Returns:
            Human-readable renderer name
        """
        return self.__class__.__name__

