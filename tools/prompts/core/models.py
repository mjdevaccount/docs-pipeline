"""
Prompt Pipeline Data Models
============================
Dataclasses for prompt pipeline configuration and results.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class DocumentContext:
    """Context for document processing"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)  # Track agent transformations
    source_file: Optional[Path] = None
    
    def add_history(self, agent_name: str, action: str) -> None:
        """Add an entry to the processing history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append(f"[{timestamp}] {agent_name}: {action}")


@dataclass
class AgentResult:
    """Result from an agent's processing"""
    content: str
    success: bool
    agent_name: str
    changes_made: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def summary(self) -> str:
        """Generate a summary of the agent's work"""
        status = "✓" if self.success else "✗"
        changes = f"{len(self.changes_made)} changes" if self.changes_made else "no changes"
        warnings = f", {len(self.warnings)} warnings" if self.warnings else ""
        return f"{status} {self.agent_name}: {changes}{warnings}"


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    name: str
    enabled: bool = True
    prompt_template: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptConfig:
    """Configuration for the entire prompt pipeline"""
    pipeline_name: str
    document_type: str  # 'architecture', 'technical', 'business'
    agents: List[AgentConfig] = field(default_factory=list)
    
    # LLM settings
    default_model: str = "gpt-4"
    default_temperature: float = 0.7
    
    # Output settings
    preserve_history: bool = True
    generate_diff: bool = True
    
    # Validation
    require_frontmatter: bool = True
    require_sections: List[str] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'PromptConfig':
        """Load configuration from YAML file"""
        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        agents = [AgentConfig(**agent) for agent in data.get('agents', [])]
        
        return cls(
            pipeline_name=data['pipeline_name'],
            document_type=data['document_type'],
            agents=agents,
            default_model=data.get('default_model', 'gpt-4'),
            default_temperature=data.get('default_temperature', 0.7),
            preserve_history=data.get('preserve_history', True),
            generate_diff=data.get('generate_diff', True),
            require_frontmatter=data.get('require_frontmatter', True),
            require_sections=data.get('require_sections', [])
        )


@dataclass
class PipelineResult:
    """Result from running the entire pipeline"""
    success: bool
    input_file: Path
    output_file: Path
    agent_results: List[AgentResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def summary(self) -> str:
        """Generate a summary of the pipeline run"""
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        agents = len(self.agent_results)
        total_changes = sum(len(r.changes_made) for r in self.agent_results)
        return f"{status}: {agents} agents, {total_changes} total changes, {self.duration_seconds:.1f}s"

