"""
Factory for creating PDF renderer instances.
Implements Strategy pattern for runtime renderer selection.
"""
from typing import Optional, List, Type
from .base import PdfRenderer
from .config import RendererType


class RendererFactory:
    """
    Factory for creating PDF renderers based on type or auto-detection.
    
    Usage:
        # Explicit renderer selection
        factory = RendererFactory()
        renderer = factory.get_renderer(RendererType.PLAYWRIGHT)
        
        # Auto-select available renderer
        renderer = factory.get_available_renderer()
    """
    
    # Registry of available renderers (lazy loaded to avoid import errors)
    _RENDERERS = {}
    _initialized = False
    
    @classmethod
    def _init_renderers(cls):
        """Lazy initialization of renderer registry"""
        if cls._initialized:
            return
        
        # Import renderers only when needed
        try:
            from .playwright_wrapper import PlaywrightRenderer
            cls._RENDERERS[RendererType.PLAYWRIGHT] = PlaywrightRenderer
        except ImportError:
            pass
        
        cls._initialized = True
    
    @classmethod
    def get_renderer(cls, renderer_type: RendererType) -> PdfRenderer:
        """
        Get renderer by type.
        
        Args:
            renderer_type: Type of renderer to create
        
        Returns:
            Renderer instance
        
        Raises:
            ValueError: If renderer type not found
            ImportError: If renderer not available
        """
        cls._init_renderers()
        
        if renderer_type not in cls._RENDERERS:
            raise ValueError(f"Unknown renderer type: {renderer_type}")
        
        renderer_class = cls._RENDERERS[renderer_type]
        
        try:
            renderer = renderer_class()
            
            if not renderer.is_available():
                raise ImportError(f"{renderer.get_name()} is not available on this system")
            
            return renderer
            
        except ImportError as e:
            raise ImportError(f"Failed to create {renderer_type.value} renderer: {e}")
    
    @classmethod
    def get_available_renderer(cls, verbose: bool = False) -> Optional[PdfRenderer]:
        """
        Get available renderer (Playwright).
        
        Args:
            verbose: Print availability status
        
        Returns:
            Playwright renderer, or None if not available
        """
        cls._init_renderers()
        
        try:
            renderer = cls.get_renderer(RendererType.PLAYWRIGHT)
            if verbose:
                print(f"[OK] Using {renderer.get_name()} renderer")
            return renderer
        except (ImportError, ValueError):
            if verbose:
                print(f"[ERROR] Playwright renderer not available")
            return None
    
    @classmethod
    def list_available_renderers(cls) -> List[str]:
        """
        List all available renderers on this system.
        
        Returns:
            List of available renderer names
        """
        cls._init_renderers()
        
        available = []
        for renderer_type, renderer_class in cls._RENDERERS.items():
            try:
                renderer = renderer_class()
                if renderer.is_available():
                    available.append(renderer.get_name())
            except:
                pass
        return available
    
    @classmethod
    def register_renderer(cls, renderer_type: RendererType, renderer_class: Type[PdfRenderer]):
        """
        Register a custom renderer (for extensibility).
        
        Args:
            renderer_type: Enum type for the renderer
            renderer_class: Renderer class (must inherit from PdfRenderer)
        
        Example:
            class MyRenderer(PdfRenderer):
                # Implementation
                pass
            
            RendererFactory.register_renderer(RendererType.CUSTOM, MyRenderer)
        """
        cls._init_renderers()
        
        if not issubclass(renderer_class, PdfRenderer):
            raise TypeError(f"{renderer_class} must inherit from PdfRenderer")
        
        cls._RENDERERS[renderer_type] = renderer_class
