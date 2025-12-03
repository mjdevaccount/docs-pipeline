"""
Pipeline orchestration for document processing.
Implements Pipeline + Template Method patterns.

This module provides a flexible pipeline architecture for processing
documents through multiple stages (preprocessing, conversion, rendering).
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PipelineContext:
    """
    Shared context object passed through pipeline steps.
    Each step reads from and writes to this context.
    
    Attributes:
        input_file: Path to input Markdown file
        output_file: Path to output file (PDF, DOCX, or HTML)
        work_dir: Temporary working directory for intermediate files
        raw_content: Original Markdown content
        preprocessed_markdown: Markdown after preprocessing steps
        html_content: HTML after Pandoc conversion
        metadata: Document metadata dictionary
        svg_files: List of rendered diagram files
        temp_files: List of temporary files to clean up
        config: Step configuration dictionary
        verbose: Enable verbose logging
        step_results: Results from each step (step_name -> success/failure)
    """
    # Input/Output paths
    input_file: Path
    output_file: Path
    work_dir: Path
    
    # Content at various stages
    raw_content: Optional[str] = None
    preprocessed_markdown: Optional[str] = None
    html_content: Optional[str] = None
    html_file: Optional[Path] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    metadata_obj: Any = None  # DocumentMetadata instance
    
    # Artifacts generated during processing
    svg_files: List[Path] = field(default_factory=list)
    temp_files: List[Path] = field(default_factory=list)
    
    # Configuration passed through
    config: Dict[str, Any] = field(default_factory=dict)
    
    # State tracking
    verbose: bool = False
    step_results: Dict[str, bool] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Convert string paths to Path objects"""
        if isinstance(self.input_file, str):
            self.input_file = Path(self.input_file)
        if isinstance(self.output_file, str):
            self.output_file = Path(self.output_file)
        if isinstance(self.work_dir, str):
            self.work_dir = Path(self.work_dir)
        self.start_time = datetime.now()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default"""
        return self.config.get(key, default)
    
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds since pipeline started"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0


class PipelineStep(ABC):
    """
    Abstract base class for pipeline steps.
    Each step operates on PipelineContext and returns success/failure.
    
    Subclasses must implement:
    - execute(context): Perform the step's work
    - get_name(): Return human-readable step name
    
    Example:
        class MyStep(PipelineStep):
            def get_name(self) -> str:
                return "My Custom Step"
            
            def execute(self, context: PipelineContext) -> bool:
                # Do work here
                context.preprocessed_markdown = process(context.raw_content)
                return True
    """
    
    @abstractmethod
    def execute(self, context: PipelineContext) -> bool:
        """
        Execute this pipeline step.
        
        Args:
            context: Shared pipeline context
        
        Returns:
            True if step succeeded, False otherwise
        
        Raises:
            PipelineError: If step fails critically
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get human-readable step name for logging"""
        pass
    
    def log(self, message: str, context: PipelineContext) -> None:
        """Log a message if verbose mode enabled"""
        if context.verbose:
            print(f"    [{self.get_name()}] {message}")
    
    def validate(self, context: PipelineContext) -> None:
        """
        Validate preconditions for this step.
        Override in subclasses for step-specific validation.
        
        Args:
            context: Pipeline context
        
        Raises:
            PipelineError: If preconditions not met
        """
        pass
    
    def cleanup(self, context: PipelineContext) -> None:
        """
        Clean up after step execution (optional).
        Called after execute(), regardless of success/failure.
        """
        pass


class Pipeline:
    """
    Pipeline orchestrator that executes steps sequentially.
    
    Features:
    - Sequential step execution with error handling
    - Step insertion/removal at runtime
    - Progress tracking and logging
    - Cleanup on failure
    
    Example:
        pipeline = Pipeline([
            MetadataExtractionStep(),
            GlossaryExpansionStep(),
            DiagramRenderingStep(),
            PandocConversionStep(),
            PdfRenderingStep()
        ])
        
        context = PipelineContext(
            input_file='doc.md',
            output_file='doc.pdf',
            work_dir=temp_dir
        )
        
        success = pipeline.execute(context)
    """
    
    def __init__(self, steps: Optional[List[PipelineStep]] = None, name: str = "Document"):
        """
        Initialize pipeline with steps.
        
        Args:
            steps: List of pipeline steps to execute in order
            name: Human-readable pipeline name for logging
        """
        self.steps = steps or []
        self.name = name
        self._on_step_complete: Optional[Callable[[str, bool], None]] = None
    
    def execute(self, context: PipelineContext) -> bool:
        """
        Execute all pipeline steps in sequence.
        
        Args:
            context: Pipeline context
        
        Returns:
            True if all steps succeeded, False if any failed
        """
        total_steps = len(self.steps)
        
        if context.verbose:
            print(f"\n{'='*60}")
            print(f"{self.name} Pipeline - {total_steps} steps")
            print(f"{'='*60}")
        
        for idx, step in enumerate(self.steps, 1):
            step_name = step.get_name()
            
            if context.verbose:
                print(f"\n  [{idx}/{total_steps}] {step_name}...")
            
            try:
                # Validate preconditions
                step.validate(context)
                
                # Execute step
                success = step.execute(context)
                
                # Record result
                context.step_results[step_name] = success
                
                # Cleanup
                step.cleanup(context)
                
                # Callback
                if self._on_step_complete:
                    self._on_step_complete(step_name, success)
                
                if not success:
                    print(f"  [ERROR] Step '{step_name}' failed")
                    return False
                    
            except PipelineError as e:
                print(f"  [ERROR] Step '{step_name}': {e}")
                context.step_results[step_name] = False
                step.cleanup(context)
                return False
                
            except Exception as e:
                print(f"  [ERROR] Step '{step_name}' raised unexpected exception: {e}")
                context.step_results[step_name] = False
                step.cleanup(context)
                return False
        
        if context.verbose:
            elapsed = context.elapsed_time()
            print(f"\n{'='*60}")
            print(f"Pipeline completed in {elapsed:.2f}s")
            print(f"{'='*60}")
        
        return True
    
    def add_step(self, step: PipelineStep) -> 'Pipeline':
        """Add a step to the end of the pipeline. Returns self for chaining."""
        self.steps.append(step)
        return self
    
    def insert_step(self, index: int, step: PipelineStep) -> 'Pipeline':
        """Insert a step at specific position. Returns self for chaining."""
        self.steps.insert(index, step)
        return self
    
    def remove_step(self, step_name: str) -> 'Pipeline':
        """Remove a step by name. Returns self for chaining."""
        self.steps = [s for s in self.steps if s.get_name() != step_name]
        return self
    
    def replace_step(self, step_name: str, new_step: PipelineStep) -> 'Pipeline':
        """Replace a step by name. Returns self for chaining."""
        for i, step in enumerate(self.steps):
            if step.get_name() == step_name:
                self.steps[i] = new_step
                break
        return self
    
    def get_step(self, step_name: str) -> Optional[PipelineStep]:
        """Get a step by name"""
        for step in self.steps:
            if step.get_name() == step_name:
                return step
        return None
    
    def on_step_complete(self, callback: Callable[[str, bool], None]) -> None:
        """Set callback for step completion events"""
        self._on_step_complete = callback
    
    def __len__(self) -> int:
        return len(self.steps)
    
    def __iter__(self):
        return iter(self.steps)


class PipelineError(Exception):
    """Exception raised when pipeline execution fails"""
    
    def __init__(self, message: str, step_name: str = None, cause: Exception = None):
        super().__init__(message)
        self.step_name = step_name
        self.cause = cause

