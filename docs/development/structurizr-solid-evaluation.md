# SOLID Principles Evaluation - Structurizr Tools

## Executive Summary

This document evaluates the `structurizr-tools` codebase against SOLID principles and provides a refactoring plan to improve maintainability and extensibility.

**Current State**: Single-file procedural script (773 lines) with mixed responsibilities.

**Target State**: Modular architecture with clear separation of concerns and dependency injection.

---

## Current Architecture Analysis

### structurizr.py (773 lines)

#### SRP Violations ❌
- **Multiple Responsibilities**:
  - Docker command execution
  - Configuration file management
  - Workspace validation
  - Export operations
  - Watch mode implementation
  - Batch processing
  - Progress tracking
  - Path normalization
  - CLI argument parsing
  - Dependency checking

#### OCP Violations ❌
- Hard-coded Docker command construction
- Fixed export format handling
- Cannot extend functionality without modifying core
- No plugin system for new export formats

#### LSP Violations ⚠️
- No inheritance hierarchy (procedural code)
- Not applicable in current structure

#### ISP Violations ❌
- Functions with many optional parameters
- `run_docker_command` has 7 parameters
- `batch_export` mixes multiple concerns

#### DIP Violations ❌
- Direct Docker subprocess calls
- No abstraction for container execution
- Hard dependency on Docker CLI
- Direct file system operations

---

## Refactoring Strategy

### Proposed Module Structure

```
structurizr_tools/
├── core/
│   ├── __init__.py
│   ├── interfaces.py          # Abstract interfaces
│   ├── exceptions.py         # Custom exceptions
│   └── types.py              # Type definitions
├── docker/
│   ├── __init__.py
│   ├── executor.py           # Docker command execution
│   ├── container_manager.py  # Container lifecycle
│   └── path_normalizer.py    # Path normalization
├── workspace/
│   ├── __init__.py
│   ├── validator.py          # Workspace validation
│   ├── exporter.py           # Export operations
│   └── watcher.py            # Watch mode
├── config/
│   ├── __init__.py
│   ├── loader.py             # Config loading
│   ├── validator.py          # Config validation
│   └── template_generator.py # Config templates
└── cli/
    ├── __init__.py
    ├── commands.py            # CLI commands
    └── parsers.py             # Argument parsing
```

---

## Implementation Plan

### Phase 1: Core Interfaces

```python
# structurizr_tools/core/interfaces.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional

class IContainerExecutor(ABC):
    """Abstract interface for container execution"""
    
    @abstractmethod
    def execute(self, command: str, args: List[str], 
                workspace_dir: Path, **options) -> bool:
        """Execute command in container"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if container runtime is available"""
        pass

class IWorkspaceValidator(ABC):
    """Abstract interface for workspace validation"""
    
    @abstractmethod
    def validate(self, workspace_path: Path) -> bool:
        """Validate workspace file"""
        pass

class IWorkspaceExporter(ABC):
    """Abstract interface for workspace export"""
    
    @abstractmethod
    def export(self, workspace_path: Path, format: str, 
              output_dir: Path, **options) -> bool:
        """Export workspace to format"""
        pass
    
    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """Check if format is supported"""
        pass

class IConfigLoader(ABC):
    """Abstract interface for configuration loading"""
    
    @abstractmethod
    def load(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file"""
        pass
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration"""
        pass

class IFileWatcher(ABC):
    """Abstract interface for file watching"""
    
    @abstractmethod
    def watch(self, file_path: Path, callback: callable) -> None:
        """Watch file for changes"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop watching"""
        pass
```

### Phase 2: Docker Module

```python
# structurizr_tools/docker/executor.py
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from structurizr_tools.core.interfaces import IContainerExecutor
from structurizr_tools.core.exceptions import DockerError
from structurizr_tools.docker.path_normalizer import PathNormalizer

class DockerExecutor(IContainerExecutor):
    """Docker-based container executor"""
    
    def __init__(self, image: str = "structurizr/cli:latest"):
        """
        Initialize Docker executor
        
        Args:
            image: Docker image to use
        """
        self._image = image
        self._normalizer = PathNormalizer()
    
    def is_available(self) -> bool:
        """Check if Docker is available"""
        try:
            subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def execute(self, command: str, args: List[str],
                workspace_dir: Path, **options) -> bool:
        """
        Execute command in Docker container
        
        Args:
            command: Command to execute
            args: Command arguments
            workspace_dir: Workspace directory to mount
            **options: Additional options
        
        Returns:
            True if successful
        """
        if not self.is_available():
            raise DockerError("Docker is not available")
        
        docker_cmd = self._build_docker_command(
            command, args, workspace_dir, **options
        )
        
        try:
            result = subprocess.run(
                docker_cmd,
                check=True,
                capture_output=options.get('capture_output', False),
                text=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            raise DockerError(f"Docker command failed: {e.stderr}") from e
    
    def _build_docker_command(self, command: str, args: List[str],
                              workspace_dir: Path, **options) -> List[str]:
        """Build Docker command"""
        workspace_normalized = self._normalizer.normalize(workspace_dir)
        
        docker_cmd = ["docker", "run", "--rm"]
        docker_cmd.extend(["-v", f"{workspace_normalized}:/workspace"])
        docker_cmd.extend(["-w", "/workspace"])
        docker_cmd.append(self._image)
        docker_cmd.append(command)
        docker_cmd.extend(args)
        
        return docker_cmd
```

### Phase 3: Workspace Module

```python
# structurizr_tools/workspace/exporter.py
from pathlib import Path
from typing import List, Dict, Any
from structurizr_tools.core.interfaces import IWorkspaceExporter, IContainerExecutor
from structurizr_tools.core.exceptions import ExportError

class WorkspaceExporter(IWorkspaceExporter):
    """Workspace exporter using container executor"""
    
    SUPPORTED_FORMATS = [
        'mermaid', 'plantuml', 'png', 'svg', 
        'html', 'json', 'ilograph', 'websequencediagrams', 'graphviz'
    ]
    
    def __init__(self, executor: IContainerExecutor):
        """
        Initialize workspace exporter
        
        Args:
            executor: Container executor for running commands
        """
        self._executor = executor
    
    def supports_format(self, format: str) -> bool:
        """Check if format is supported"""
        return format.lower() in self.SUPPORTED_FORMATS
    
    def export(self, workspace_path: Path, format: str,
              output_dir: Path, **options) -> bool:
        """
        Export workspace to format
        
        Args:
            workspace_path: Path to workspace file
            format: Export format
            output_dir: Output directory
            **options: Additional options
        
        Returns:
            True if successful
        """
        if not self.supports_format(format):
            raise ExportError(f"Unsupported format: {format}")
        
        workspace_dir = workspace_path.parent
        workspace_name = workspace_path.name
        
        args = [
            '--workspace', workspace_name,
            '--format', format,
            '--output', str(output_dir.relative_to(workspace_dir))
        ]
        
        return self._executor.execute(
            'export',
            args,
            workspace_dir=workspace_dir,
            **options
        )
```

### Phase 4: Configuration Module

```python
# structurizr_tools/config/loader.py
import json
from pathlib import Path
from typing import Dict, Any
from structurizr_tools.core.interfaces import IConfigLoader
from structurizr_tools.core.exceptions import ConfigurationError

class JsonConfigLoader(IConfigLoader):
    """JSON configuration loader"""
    
    def load(self, config_path: Path) -> Dict[str, Any]:
        """
        Load configuration from JSON file
        
        Args:
            config_path: Path to config file
        
        Returns:
            Configuration dictionary
        
        Raises:
            ConfigurationError: If loading fails
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Config file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config: {e}") from e
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration
        
        Args:
            config: Configuration dictionary
        
        Returns:
            True if valid
        
        Raises:
            ConfigurationError: If validation fails
        """
        if 'workspace' not in config:
            raise ConfigurationError("Missing required field: workspace")
        
        workspace_path = Path(config['workspace'])
        if not workspace_path.exists():
            raise ConfigurationError(f"Workspace file not found: {workspace_path}")
        
        if 'formats' in config:
            valid_formats = WorkspaceExporter.SUPPORTED_FORMATS
            for fmt in config['formats']:
                if fmt not in valid_formats:
                    raise ConfigurationError(
                        f"Unknown format: {fmt} (valid: {', '.join(valid_formats)})"
                    )
        
        return True
```

### Phase 5: CLI Module

```python
# structurizr_tools/cli/commands.py
from pathlib import Path
from typing import Optional
from structurizr_tools.workspace.exporter import WorkspaceExporter
from structurizr_tools.workspace.validator import WorkspaceValidator
from structurizr_tools.docker.executor import DockerExecutor
from structurizr_tools.config.loader import JsonConfigLoader

class ExportCommand:
    """Export command handler"""
    
    def __init__(
        self,
        exporter: Optional[WorkspaceExporter] = None,
        validator: Optional[WorkspaceValidator] = None
    ):
        """
        Initialize export command
        
        Args:
            exporter: Workspace exporter (injected)
            validator: Workspace validator (injected)
        """
        executor = DockerExecutor()
        self._exporter = exporter or WorkspaceExporter(executor)
        self._validator = validator or WorkspaceValidator(executor)
    
    def execute(self, workspace: Path, format: str, 
               output: Path, validate: bool = True) -> bool:
        """
        Execute export command
        
        Args:
            workspace: Workspace file path
            format: Export format
            output: Output directory
            validate: Whether to validate before export
        
        Returns:
            True if successful
        """
        if validate:
            if not self._validator.validate(workspace):
                return False
        
        return self._exporter.export(workspace, format, output)

class BatchExportCommand:
    """Batch export command handler"""
    
    def __init__(
        self,
        exporter: Optional[WorkspaceExporter] = None,
        config_loader: Optional[JsonConfigLoader] = None
    ):
        """
        Initialize batch export command
        
        Args:
            exporter: Workspace exporter (injected)
            config_loader: Config loader (injected)
        """
        executor = DockerExecutor()
        self._exporter = exporter or WorkspaceExporter(executor)
        self._config_loader = config_loader or JsonConfigLoader()
    
    def execute(self, config_path: Path) -> bool:
        """
        Execute batch export from config
        
        Args:
            config_path: Path to config file
        
        Returns:
            True if all exports successful
        """
        config = self._config_loader.load(config_path)
        self._config_loader.validate(config)
        
        workspace = Path(config['workspace'])
        formats = config.get('formats', ['mermaid'])
        output_dir = Path(config.get('output_dir', 'docs/diagrams'))
        
        results = []
        for fmt in formats:
            success = self._exporter.export(workspace, fmt, output_dir)
            results.append((fmt, success))
        
        return all(success for _, success in results)
```

---

## Benefits

### Maintainability
- **Single Responsibility**: Each class has one clear purpose
- **Isolated Components**: Easier to debug and modify
- **Clear Dependencies**: Explicit dependency injection

### Testability
- **Mockable Interfaces**: Easy to mock for testing
- **Isolated Units**: Test each component independently
- **Dependency Injection**: Inject test doubles

### Extensibility
- **Interface-Based**: Add new implementations without modifying core
- **Plugin System**: Register new export formats
- **Open/Closed**: Extend without modification

---

## Migration Path

### Step 1: Create New Structure
- Create new module directories
- Move code to appropriate modules
- Create interfaces

### Step 2: Refactor Incrementally
- Start with Docker executor
- Then workspace operations
- Finally CLI commands

### Step 3: Maintain Compatibility
- Keep old CLI entry point
- Provide adapter if needed
- Gradual migration

---

## Success Metrics

- ✅ Code coverage > 80%
- ✅ Cyclomatic complexity < 10 per function
- ✅ No circular dependencies
- ✅ All SOLID principles satisfied
- ✅ Backward compatibility maintained

