"""
Structure Analyzer Agent
=========================
Analyzes document structure and identifies gaps and inconsistencies.
"""
import json
from typing import Optional
from .base import BaseDocumentAgent
from ..core.interfaces import IPromptExecutor, IPromptLibrary
from ..core.models import DocumentContext, AgentResult


class StructureAnalyzerAgent(BaseDocumentAgent):
    """
    Agent that analyzes document structure and provides recommendations.
    Returns JSON analysis that can be used by subsequent agents.
    """
    
    def __init__(
        self,
        prompt_library: IPromptLibrary,
        prompt_executor: IPromptExecutor,
        model: Optional[str] = None,
        temperature: float = 0.3  # Lower temperature for analytical tasks
    ):
        super().__init__(
            prompt_library=prompt_library,
            prompt_executor=prompt_executor,
            prompt_category="architecture",
            prompt_name="analyze",
            model=model,
            temperature=temperature
        )
    
    @property
    def name(self) -> str:
        return "Structure Analyzer"
    
    @property
    def description(self) -> str:
        return "Analyzes document structure, identifies gaps, and provides recommendations"
    
    def prepare_context(self, context: DocumentContext) -> dict:
        """Prepare context for the analysis prompt"""
        return {
            "document_content": context.content,
            "metadata": context.metadata
        }
    
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        """Parse JSON analysis from LLM response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(json_str)
            
            # Extract changes and warnings
            changes_made = []
            warnings = []
            
            if analysis.get("missing_sections"):
                changes_made.append(f"Identified {len(analysis['missing_sections'])} missing sections")
            
            if analysis.get("content_gaps"):
                high_severity = [g for g in analysis['content_gaps'] if g.get('severity') == 'high']
                if high_severity:
                    warnings.append(f"{len(high_severity)} high-severity content gaps found")
                changes_made.append(f"Found {len(analysis['content_gaps'])} content gaps")
            
            if analysis.get("consistency_issues"):
                changes_made.append(f"Found {len(analysis['consistency_issues'])} consistency issues")
            
            # Store analysis in metadata for next agent
            metadata = {
                "analysis": analysis,
                "structure_score": analysis.get("structure_score", 0)
            }
            
            return AgentResult(
                content=context.content,  # No content changes, just analysis
                success=True,
                agent_name=self.name,
                changes_made=changes_made,
                warnings=warnings,
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            return AgentResult(
                content=context.content,
                success=False,
                agent_name=self.name,
                changes_made=[],
                warnings=[f"Failed to parse analysis JSON: {str(e)}"],
                metadata={"raw_response": response}
            )

