"""Structurizr DSL to diagram export tool."""

__version__ = "1.0.0"

# Expose main functions
try:
    from .structurizr_tools.workspace.exporter import WorkspaceExporter
    # Alias for backward compatibility
    StructurizrExporter = WorkspaceExporter
    __all__ = ["WorkspaceExporter", "StructurizrExporter"]
except ImportError:
    __all__ = []

