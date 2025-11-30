"""
Prompt Library Implementation
==============================
Loads and manages prompt templates from the library directory.
"""
from pathlib import Path
from typing import List, Optional
from .core.interfaces import IPromptLibrary
from .core.exceptions import PromptNotFoundError


class FileSystemPromptLibrary(IPromptLibrary):
    """
    Prompt library that loads templates from the filesystem.
    """
    
    def __init__(self, library_root: Optional[Path] = None):
        """
        Initialize the prompt library.
        
        Args:
            library_root: Root directory for prompt templates.
                         Defaults to tools/prompts/library/
        """
        if library_root is None:
            # Default to library/ subdirectory
            self._library_root = Path(__file__).parent / "library"
        else:
            self._library_root = Path(library_root)
        
        if not self._library_root.exists():
            raise PromptNotFoundError(f"Prompt library not found: {self._library_root}")
    
    def load_prompt(self, category: str, name: str) -> str:
        """
        Load a prompt template by category and name.
        
        Args:
            category: Prompt category (e.g., 'architecture', 'technical')
            name: Prompt name (e.g., 'analyze', 'enhance')
            
        Returns:
            Prompt template as string
            
        Raises:
            PromptNotFoundError: If prompt file doesn't exist
        """
        prompt_path = self._library_root / category / f"{name}.md"
        
        if not prompt_path.exists():
            raise PromptNotFoundError(
                f"Prompt not found: {category}/{name}.md\n"
                f"Expected path: {prompt_path}"
            )
        
        return prompt_path.read_text(encoding='utf-8')
    
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """
        List available prompts, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of prompt identifiers in format "category/name"
        """
        prompts = []
        
        if category:
            # List prompts in specific category
            category_path = self._library_root / category
            if category_path.exists() and category_path.is_dir():
                for prompt_file in category_path.glob("*.md"):
                    prompts.append(f"{category}/{prompt_file.stem}")
        else:
            # List all prompts
            for category_dir in self._library_root.iterdir():
                if category_dir.is_dir():
                    for prompt_file in category_dir.glob("*.md"):
                        prompts.append(f"{category_dir.name}/{prompt_file.stem}")
        
        return sorted(prompts)

