"""
Style Polisher Agent
====================
Polishes document for consistency, clarity, and professional presentation.
"""
import re
from typing import Optional
from .base import BaseDocumentAgent
from ..core.interfaces import IPromptExecutor, IPromptLibrary
from ..core.models import DocumentContext, AgentResult


class StylePolisherAgent(BaseDocumentAgent):
    """
    Agent that polishes document style, ensuring consistency,
    clarity, and professional presentation.
    """
    
    def __init__(
        self,
        prompt_library: IPromptLibrary,
        prompt_executor: IPromptExecutor,
        model: Optional[str] = None,
        temperature: float = 0.5  # Moderate temperature for style tasks
    ):
        super().__init__(
            prompt_library=prompt_library,
            prompt_executor=prompt_executor,
            prompt_category="architecture",
            prompt_name="polish",
            model=model,
            temperature=temperature
        )
    
    @property
    def name(self) -> str:
        return "Style Polisher"
    
    @property
    def description(self) -> str:
        return "Polishes document for consistency, clarity, and professional presentation"
    
    def prepare_context(self, context: DocumentContext) -> dict:
        """Prepare context for style polishing"""
        return {
            "document_content": context.content
        }
    
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        """Parse polished document from LLM response"""
        # Clean up response
        polished_content = response.strip()
        
        # Remove markdown code block markers if present
        if polished_content.startswith("```markdown"):
            polished_content = polished_content[len("```markdown"):].strip()
        elif polished_content.startswith("```"):
            polished_content = polished_content[3:].strip()
        
        if polished_content.endswith("```"):
            polished_content = polished_content[:-3].strip()
        
        # Detect changes
        changes_made = []
        
        # Check for formatting improvements
        if polished_content.count('`') != context.content.count('`'):
            changes_made.append("Improved code formatting")
        
        if polished_content.count('**') != context.content.count('**'):
            changes_made.append("Enhanced emphasis formatting")
        
        # Check for structural improvements
        original_headings = re.findall(r'^(#+)\s+(.+)$', context.content, re.MULTILINE)
        polished_headings = re.findall(r'^(#+)\s+(.+)$', polished_content, re.MULTILINE)
        
        if len(polished_headings) != len(original_headings):
            changes_made.append("Adjusted heading structure")
        
        # Check for consistency improvements
        original_words = len(context.content.split())
        polished_words = len(polished_content.split())
        word_diff = abs(polished_words - original_words)
        
        if word_diff > original_words * 0.05:  # More than 5% change
            if polished_words < original_words:
                changes_made.append(f"Reduced verbosity ({word_diff} words)")
            else:
                changes_made.append(f"Expanded clarity ({word_diff} words)")
        
        if not changes_made:
            changes_made = ["Polished formatting and style"]
        
        return AgentResult(
            content=polished_content,
            success=True,
            agent_name=self.name,
            changes_made=changes_made,
            warnings=[],
            metadata={}
        )

