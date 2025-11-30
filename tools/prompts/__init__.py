"""AI-powered document refinement with multi-agent system."""

__version__ = "1.0.0"

# Expose main orchestrator for programmatic use
try:
    from .orchestrator import AgentOrchestrator
    # Alias for backward compatibility
    DocumentOrchestrator = AgentOrchestrator
    __all__ = ["AgentOrchestrator", "DocumentOrchestrator"]
except ImportError:
    __all__ = []
