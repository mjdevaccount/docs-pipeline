"""
PlantUML diagram renderer.
"""
from pathlib import Path
from typing import Optional
import subprocess
import tempfile

from .base import DiagramRenderer, DiagramFormat, RenderResult
from .cache import DiagramCache


class PlantUMLRenderer(DiagramRenderer):
    """
    Renderer for PlantUML diagrams.
    
    Requires:
    - Java Runtime Environment
    - plantuml.jar file
    
    Supports:
    - UML diagrams (class, sequence, use case, etc.)
    - SVG output (PNG support can be added)
    - Caching
    """
    
    def __init__(
        self,
        cache: Optional[DiagramCache] = None,
        plantuml_jar: Optional[Path] = None
    ):
        """
        Initialize PlantUML renderer.
        
        Args:
            cache: Optional DiagramCache
            plantuml_jar: Optional path to plantuml.jar file
                         If None, searches common locations
        """
        self.cache = cache
        self.plantuml_jar = plantuml_jar or self._find_plantuml_jar()
        
        if not self.plantuml_jar or not self.plantuml_jar.exists():
            # Don't raise error - PlantUML is optional
            # Just mark as unavailable
            self._available = False
        else:
            self._available = True
    
    def _find_plantuml_jar(self) -> Optional[Path]:
        """Find plantuml.jar in common locations."""
        search_paths = [
            Path(__file__).parent.parent / 'plantuml.jar',
            Path.home() / 'plantuml.jar',
            Path('C:/tools/plantuml.jar'),
            Path('/usr/local/share/plantuml.jar'),
            Path('/usr/share/plantuml/plantuml.jar'),
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def can_render(self, diagram_code: str, format_hint: Optional[str] = None) -> bool:
        """Check if this is a PlantUML diagram."""
        if not self._available:
            return False
        
        if format_hint:
            return format_hint.lower() == 'plantuml'
        
        # PlantUML diagrams typically start with @startuml
        return diagram_code.strip().startswith('@start')
    
    def validate(self, diagram_code: str) -> bool:
        """Validate PlantUML syntax."""
        # Basic validation - check for @startuml/@enduml
        code = diagram_code.strip()
        return code.startswith('@start') and '@end' in code
    
    def render(
        self,
        diagram_code: str,
        output_file: Path,
        format: DiagramFormat = DiagramFormat.SVG,
        **options
    ) -> RenderResult:
        """
        Render PlantUML diagram.
        
        Args:
            diagram_code: PlantUML source code
            output_file: Output file path
            format: Output format (currently only SVG)
            **options: Reserved for future options
            
        Returns:
            RenderResult with success status
        """
        if not self._available:
            return RenderResult(
                success=False,
                error_message="PlantUML not available: plantuml.jar not found"
            )
        
        if format != DiagramFormat.SVG:
            return RenderResult(
                success=False,
                error_message=f"PlantUML renderer only supports SVG (requested: {format.value})"
            )
        
        # Validate
        if not self.validate(diagram_code):
            return RenderResult(
                success=False,
                error_message="Invalid PlantUML syntax"
            )
        
        # Check cache
        if self.cache:
            if self.cache.get_and_copy(diagram_code, output_file, format):
                return RenderResult(
                    success=True,
                    output_file=output_file,
                    from_cache=True
                )
        
        # Create temp input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False, encoding='utf-8') as tmp:
            tmp.write(diagram_code)
            tmp_input = Path(tmp.name)
        
        try:
            # Render: java -jar plantuml.jar -tsvg input.puml -o output_dir
            work_dir = output_file.parent
            result = subprocess.run([
                'java', '-jar', str(self.plantuml_jar),
                '-tsvg',
                str(tmp_input),
                '-o', str(work_dir)
            ], capture_output=True, text=True, check=False, timeout=30)
            
            # PlantUML outputs to same name with .svg extension
            expected_output = work_dir / f"{tmp_input.stem}.svg"
            
            if result.returncode != 0:
                return RenderResult(
                    success=False,
                    error_message=f"PlantUML failed: {result.stderr}"
                )
            
            # Move to final output location
            if expected_output.exists():
                if expected_output != output_file:
                    expected_output.rename(output_file)
                
                # Save to cache
                if self.cache:
                    self.cache.save(diagram_code, output_file, format)
                
                return RenderResult(
                    success=True,
                    output_file=output_file,
                    from_cache=False
                )
            else:
                return RenderResult(
                    success=False,
                    error_message="PlantUML did not produce output file"
                )
                
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                error_message="PlantUML rendering timed out (30s)"
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error_message=f"PlantUML exception: {str(e)}"
            )
        finally:
            if tmp_input.exists():
                tmp_input.unlink()
    
    def get_supported_formats(self) -> list[DiagramFormat]:
        """PlantUML currently supports SVG only."""
        return [DiagramFormat.SVG]

