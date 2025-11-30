"""
Content Enhancer Agent
======================
Enhances and expands document content based on analysis.
"""
import re
from typing import Optional
from .base import BaseDocumentAgent
from ..core.interfaces import IPromptExecutor, IPromptLibrary
from ..core.models import DocumentContext, AgentResult


class ContentEnhancerAgent(BaseDocumentAgent):
    """
    Agent that enhances document content by expanding thin sections,
    clarifying ambiguities, and improving structure.
    """
    
    def __init__(
        self,
        prompt_library: IPromptLibrary,
        prompt_executor: IPromptExecutor,
        model: Optional[str] = None,
        temperature: float = 0.7
    ):
        super().__init__(
            prompt_library=prompt_library,
            prompt_executor=prompt_executor,
            prompt_category="architecture",
            prompt_name="enhance",
            model=model,
            temperature=temperature
        )
    
    @property
    def name(self) -> str:
        return "Content Enhancer"
    
    @property
    def description(self) -> str:
        return "Enhances and expands document content for completeness and clarity"
    
    def prepare_context(self, context: DocumentContext) -> dict:
        """Prepare context including previous analysis"""
        import json
        
        # Get analysis from previous agent (if available)
        analysis = context.metadata.get("analysis", {})
        
        return {
            "document_content": context.content,
            "analysis": json.dumps(analysis, indent=2) if analysis else "{}"
        }
    
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        """Parse enhanced document from LLM response"""
        # Clean up response (remove any markdown formatting around the document)
        enhanced_content = response.strip()
        
        # Remove markdown code block markers if present
        if enhanced_content.startswith("```markdown"):
            enhanced_content = enhanced_content[len("```markdown"):].strip()
        elif enhanced_content.startswith("```"):
            enhanced_content = enhanced_content[3:].strip()
        
        if enhanced_content.endswith("```"):
            enhanced_content = enhanced_content[:-3].strip()
        
        # Detect changes
        changes_made = []
        original_lines = context.content.count('\n')
        enhanced_lines = enhanced_content.count('\n')
        line_diff = enhanced_lines - original_lines
        
        if line_diff > 0:
            changes_made.append(f"Added {line_diff} lines of content")
        
        # Check for new sections
        original_headings = len(re.findall(r'^#+\s+', context.content, re.MULTILINE))
        enhanced_headings = len(re.findall(r'^#+\s+', enhanced_content, re.MULTILINE))
        if enhanced_headings > original_headings:
            changes_made.append(f"Added {enhanced_headings - original_headings} new sections")
        
        # Check for formatting improvements
        if enhanced_content.count('**') > context.content.count('**'):
            changes_made.append("Enhanced formatting with emphasis")
        
        if enhanced_content.count('```') > context.content.count('```'):
            changes_made.append("Added code blocks")
        
        return AgentResult(
            content=enhanced_content,
            success=True,
            agent_name=self.name,
            changes_made=changes_made if changes_made else ["Enhanced content"],
            warnings=[],
            metadata={}
        )

