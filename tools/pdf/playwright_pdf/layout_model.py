"""
Layout Model - Domain Objects
==============================
Pure data structures representing the layout analysis.
No logic, no dependencies on Playwright or DOM.
"""
from dataclasses import dataclass, field
from typing import List, Literal, Optional

DiagramType = Literal["svg", "img"]


@dataclass
class HeadingInfo:
    """Information about a heading element"""
    id: str
    level: int  # 1, 2, 3, 4
    text: str
    y: float = 0.0  # top position in px (optional)
    height: float = 0.0  # full height incl margins/padding/borders


@dataclass
class DiagramBlock:
    """Represents a heading+diagram pair that needs analysis"""
    heading_id: str
    heading_text: str
    diagram_type: DiagramType
    diagram_selector: str  # CSS selector or stable path
    
    # Raw measurements
    heading_height: float
    elements_between_height: float
    diagram_height: float
    container_margins: float
    container_padding: float
    container_borders: float
    total_content_height: float
    available_height: float
    
    # Extra diagnostic info
    overflow_ratio: float
    header_height: float
    footer_height: float
    
    # Detailed breakdown (optional, for debugging)
    measurement_breakdown: Optional[dict] = None


@dataclass
class LayoutAnalysis:
    """Complete layout analysis result"""
    page_height: float
    available_height: float
    diagram_blocks: List[DiagramBlock] = field(default_factory=list)

