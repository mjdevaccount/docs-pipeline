"""
Agent Orchestrator
==================
Orchestrates multiple agents in sequence to process documents.
"""
import time
from pathlib import Path
from typing import List, Optional
from .core.interfaces import IAgentOrchestrator, IDocumentAgent
from .core.models import (
    DocumentContext,
    PromptConfig,
    PipelineResult,
    AgentResult
)
from .core.exceptions import ValidationError

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    SUCCESS = f"{Fore.GREEN}✓{Style.RESET_ALL}"
    FAIL = f"{Fore.RED}✗{Style.RESET_ALL}"
    INFO = f"{Fore.CYAN}ℹ{Style.RESET_ALL}"
except ImportError:
    SUCCESS = "✓"
    FAIL = "✗"
    INFO = "ℹ"


class AgentOrchestrator(IAgentOrchestrator):
    """
    Orchestrates multiple document processing agents in sequence.
    """
    
    def __init__(self, verbose: bool = True):
        self._agents: List[IDocumentAgent] = []
        self._verbose = verbose
    
    def add_agent(self, agent: IDocumentAgent) -> None:
        """Add an agent to the pipeline"""
        self._agents.append(agent)
        if self._verbose:
            print(f"{INFO} Added agent: {agent.name}")
    
    async def run_pipeline(
        self,
        input_file: Path,
        output_file: Path,
        config: PromptConfig
    ) -> bool:
        """
        Run the complete agent pipeline.
        
        Args:
            input_file: Path to input markdown file (rough draft)
            output_file: Path to output markdown file (structured)
            config: Pipeline configuration
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            # Load input document
            if not input_file.exists():
                raise ValidationError(f"Input file not found: {input_file}")
            
            content = input_file.read_text(encoding='utf-8')
            
            # Extract metadata from frontmatter if present
            metadata = self._extract_frontmatter(content)
            
            # Validate requirements
            if config.require_frontmatter and not metadata:
                raise ValidationError("Document requires frontmatter but none found")
            
            # Initialize document context
            context = DocumentContext(
                content=content,
                metadata=metadata,
                source_file=input_file
            )
            
            if self._verbose:
                print(f"\n{INFO} Starting pipeline: {config.pipeline_name}")
                print(f"{INFO} Input: {input_file}")
                print(f"{INFO} Agents: {len(self._agents)}")
                print()
            
            # Run each agent in sequence
            agent_results: List[AgentResult] = []
            
            for i, agent in enumerate(self._agents, 1):
                if self._verbose:
                    print(f"[{i}/{len(self._agents)}] Running {agent.name}...")
                
                try:
                    result = await agent.process(context)
                    agent_results.append(result)
                    
                    if result.success:
                        # Update context with result
                        context.content = result.content
                        context.metadata.update(result.metadata)
                        
                        if self._verbose:
                            print(f"    {SUCCESS} {result.summary()}")
                            for change in result.changes_made:
                                print(f"        • {change}")
                            for warning in result.warnings:
                                print(f"        ⚠ {warning}")
                    else:
                        if self._verbose:
                            print(f"    {FAIL} {result.summary()}")
                        # Continue with next agent even if one fails
                    
                    print()
                    
                except Exception as e:
                    if self._verbose:
                        print(f"    {FAIL} Agent failed: {str(e)}")
                    # Continue with next agent
                    print()
            
            # Write output
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(context.content, encoding='utf-8')
            
            # Write processing history if configured
            if config.preserve_history:
                history_file = output_file.with_suffix('.history.txt')
                history_content = "\n".join(context.history)
                history_file.write_text(history_content, encoding='utf-8')
            
            # Generate diff if configured
            if config.generate_diff:
                diff_file = output_file.with_suffix('.diff.txt')
                original = input_file.read_text(encoding='utf-8')
                final = context.content
                diff_content = self._generate_diff(original, final)
                diff_file.write_text(diff_content, encoding='utf-8')
            
            duration = time.time() - start_time
            
            if self._verbose:
                print(f"{SUCCESS} Pipeline complete!")
                print(f"{INFO} Output: {output_file}")
                print(f"{INFO} Duration: {duration:.1f}s")
                print(f"{INFO} Total changes: {sum(len(r.changes_made) for r in agent_results)}")
            
            return True
            
        except Exception as e:
            if self._verbose:
                print(f"\n{FAIL} Pipeline failed: {str(e)}")
            return False
    
    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from markdown"""
        import re
        
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return {}
        
        try:
            import yaml
            return yaml.safe_load(frontmatter_match.group(1)) or {}
        except:
            return {}
    
    def _generate_diff(self, original: str, final: str) -> str:
        """Generate a simple diff between original and final content"""
        import difflib
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            final.splitlines(keepends=True),
            fromfile='original',
            tofile='final',
            lineterm=''
        )
        
        return ''.join(diff)

