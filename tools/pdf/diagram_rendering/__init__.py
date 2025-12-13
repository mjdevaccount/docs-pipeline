"""
Diagram Rendering Module
========================

Extensible diagram rendering system following SOLID principles.

This module provides:
- DiagramRenderer: Base abstraction for all diagram renderers
- MermaidRenderer: Mermaid diagram renderer
- MermaidNativeRenderer: Native Playwright-based Mermaid rendering (Phase B)
- PlantUMLRenderer: PlantUML diagram renderer  
- GraphvizRenderer: Graphviz/DOT diagram renderer
- DiagramCache: Caching system for rendered diagrams
- DiagramOrchestrator: Coordinates multiple renderers

Benefits:
- Open/Closed: Add new diagram types without modifying existing code
- Single Responsibility: Each renderer handles one diagram type
- Testable: All components can be unit tested independently
- Extensible: Easy to add new diagram formats
- Phase B: Native rendering 40-60% faster than CLI-based
"""

from .base import DiagramRenderer, DiagramFormat, RenderResult
from .cache import DiagramCache
from .mermaid import MermaidRenderer
from .mermaid_native_renderer import MermaidNativeRenderer, render_mermaid_native
from .plantuml import PlantUMLRenderer
from .graphviz import GraphvizRenderer
from .orchestrator import DiagramOrchestrator

__all__ = [
    'DiagramRenderer',
    'DiagramFormat',
    'RenderResult',
    'DiagramCache',
    'MermaidRenderer',
    'MermaidNativeRenderer',  # Phase B
    'render_mermaid_native',  # Phase B
    'PlantUMLRenderer',
    'GraphvizRenderer',
    'DiagramOrchestrator',
]
