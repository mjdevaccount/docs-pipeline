"""
Prompt Pipeline CLI
===================
Command-line interface for running prompt-driven document pipelines.
"""
import sys
from pathlib import Path

# Support standalone execution: add current directory to path for local imports
_script_file = Path(__file__).resolve()
_script_dir = _script_file.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import asyncio
import argparse
from typing import Optional

try:
    from .core.models import PromptConfig
    from .core.exceptions import PromptPipelineError
    from .library import FileSystemPromptLibrary
    from .executor import OpenAIPromptExecutor, AnthropicPromptExecutor, MockPromptExecutor
    from .orchestrator import AgentOrchestrator
    from .agents.structure_analyzer import StructureAnalyzerAgent
    from .agents.content_enhancer import ContentEnhancerAgent
    from .agents.technical_reviewer import TechnicalReviewerAgent
    from .agents.style_polisher import StylePolisherAgent
except ImportError:
    # Fallback for standalone execution
    from core.models import PromptConfig
    from core.exceptions import PromptPipelineError
    from library import FileSystemPromptLibrary
    from executor import OpenAIPromptExecutor, AnthropicPromptExecutor, MockPromptExecutor
    from orchestrator import AgentOrchestrator
    from agents.structure_analyzer import StructureAnalyzerAgent
    from agents.content_enhancer import ContentEnhancerAgent
    from agents.technical_reviewer import TechnicalReviewerAgent
    from agents.style_polisher import StylePolisherAgent


def create_agent_from_config(agent_config, prompt_library, prompt_executor):
    """Factory function to create agents from configuration"""
    agent_name = agent_config.name
    
    agent_map = {
        "structure_analyzer": StructureAnalyzerAgent,
        "content_enhancer": ContentEnhancerAgent,
        "technical_reviewer": TechnicalReviewerAgent,
        "style_polisher": StylePolisherAgent
    }
    
    agent_class = agent_map.get(agent_name)
    if not agent_class:
        raise PromptPipelineError(f"Unknown agent: {agent_name}")
    
    return agent_class(
        prompt_library=prompt_library,
        prompt_executor=prompt_executor,
        model=agent_config.model,
        temperature=agent_config.temperature
    )


async def run_pipeline_async(
    input_file: Path,
    output_file: Path,
    config_file: Path,
    executor_type: str = "openai",
    verbose: bool = True
) -> bool:
    """Run the prompt pipeline asynchronously"""
    try:
        # Load configuration
        config = PromptConfig.from_yaml(config_file)
        
        # Initialize prompt library
        prompt_library = FileSystemPromptLibrary()
        
        # Initialize prompt executor
        if executor_type == "openai":
            prompt_executor = OpenAIPromptExecutor()
        elif executor_type == "anthropic":
            prompt_executor = AnthropicPromptExecutor()
        elif executor_type == "mock":
            prompt_executor = MockPromptExecutor("Mock enhanced content")
        else:
            raise PromptPipelineError(f"Unknown executor type: {executor_type}")
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(verbose=verbose)
        
        # Create and add agents
        for agent_config in config.agents:
            if agent_config.enabled:
                agent = create_agent_from_config(
                    agent_config,
                    prompt_library,
                    prompt_executor
                )
                orchestrator.add_agent(agent)
        
        # Run pipeline
        success = await orchestrator.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            config=config
        )
        
        return success
        
    except PromptPipelineError as e:
        if verbose:
            print(f"\n✗ Pipeline error: {str(e)}")
        return False
    except Exception as e:
        if verbose:
            print(f"\n✗ Unexpected error: {str(e)}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Prompt-driven document pipeline for transforming rough drafts into polished documents"
    )
    
    parser.add_argument(
        "input",
        type=Path,
        help="Input markdown file (rough draft)"
    )
    
    parser.add_argument(
        "output",
        type=Path,
        help="Output markdown file (polished)"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=Path,
        required=True,
        help="Pipeline configuration file (YAML)"
    )
    
    parser.add_argument(
        "-e", "--executor",
        choices=["openai", "anthropic", "mock"],
        default="openai",
        help="LLM executor to use (default: openai)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available prompts and exit"
    )
    
    args = parser.parse_args()
    
    # List prompts if requested
    if args.list_prompts:
        library = FileSystemPromptLibrary()
        prompts = library.list_prompts()
        print("Available prompts:")
        for prompt in prompts:
            print(f"  - {prompt}")
        return 0
    
    # Validate inputs
    if not args.input.exists():
        print(f"✗ Input file not found: {args.input}")
        return 1
    
    if not args.config.exists():
        print(f"✗ Config file not found: {args.config}")
        return 1
    
    # Run pipeline
    success = asyncio.run(run_pipeline_async(
        input_file=args.input,
        output_file=args.output,
        config_file=args.config,
        executor_type=args.executor,
        verbose=args.verbose
    ))
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

