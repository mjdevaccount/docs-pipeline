"""
Abstract base class for PDF renderers.
Defines the interface that all renderers must implement.
"""
from abc import ABC, abstractmethod
from .config import RenderConfig


class PdfRenderer(ABC):
    """
    Abstract base class for PDF rendering engines.
    
    Implementations must provide:
    - render(): Convert HTML to PDF
    - is_available(): Check if renderer is installed
    - get_name(): Return renderer name for logging
    
    Example:
        class MyRenderer(PdfRenderer):
            def render(self, config: RenderConfig) -> bool:
                # Implementation
                pass
            
            def is_available(self) -> bool:
                # Check if executable exists
                pass
            
            def get_name(self) -> str:
                return "MyRenderer"
    """
    
    @abstractmethod
    def render(self, config: RenderConfig) -> bool:
        """
        Render HTML to PDF.
        
        Args:
            config: Rendering configuration
        
        Returns:
            True if rendering succeeded, False otherwise
        
        Raises:
            RenderError: If rendering fails critically
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this renderer is available on the system.
        
        Returns:
            True if renderer can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get human-readable renderer name.
        
        Returns:
            Renderer name (e.g., "WeasyPrint", "Playwright")
        """
        pass
    
    def validate_config(self, config: RenderConfig) -> None:
        """
        Validate configuration for this renderer.
        Subclasses can override to add renderer-specific validation.
        
        Args:
            config: Configuration to validate
        
        Raises:
            ValueError: If configuration is invalid
        """
        config.validate()
    
    def log(self, message: str, config: RenderConfig) -> None:
        """
        Log a message if verbose mode is enabled.
        
        Args:
            message: Message to log
            config: Configuration (for verbose flag)
        """
        if config.verbose:
            print(f"[{self.get_name()}] {message}")


class RenderError(Exception):
    """Exception raised when PDF rendering fails"""
    pass

