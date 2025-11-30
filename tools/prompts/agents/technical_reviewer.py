"""
Technical Reviewer Agent
=========================
Reviews document for technical accuracy and completeness.
"""
import json
from typing import Optional
from .base import BaseDocumentAgent
from ..core.interfaces import IPromptExecutor, IPromptLibrary
from ..core.models import DocumentContext, AgentResult


class TechnicalReviewerAgent(BaseDocumentAgent):
    """
    Agent that reviews technical content for accuracy, completeness,
    and best practices. Returns JSON review with recommendations.
    """
    
    def __init__(
        self,
        prompt_library: IPromptLibrary,
        prompt_executor: IPromptExecutor,
        model: Optional[str] = None,
        temperature: float = 0.3  # Lower temperature for review tasks
    ):
        super().__init__(
            prompt_library=prompt_library,
            prompt_executor=prompt_executor,
            prompt_category="architecture",
            prompt_name="review",
            model=model,
            temperature=temperature
        )
    
    @property
    def name(self) -> str:
        return "Technical Reviewer"
    
    @property
    def description(self) -> str:
        return "Reviews technical accuracy, architecture patterns, and completeness"
    
    def prepare_context(self, context: DocumentContext) -> dict:
        """Prepare context for technical review"""
        return {
            "document_content": context.content
        }
    
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        """Parse JSON review from LLM response"""
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            
            review = json.loads(json_str)
            
            # Extract changes and warnings
            changes_made = []
            warnings = []
            
            if review.get("architecture_issues"):
                critical = [i for i in review['architecture_issues'] if i.get('severity') == 'critical']
                high = [i for i in review['architecture_issues'] if i.get('severity') == 'high']
                
                if critical:
                    warnings.append(f"{len(critical)} critical architecture issues found")
                if high:
                    warnings.append(f"{len(high)} high-severity architecture issues found")
                
                changes_made.append(f"Identified {len(review['architecture_issues'])} architecture issues")
            
            if review.get("missing_diagrams"):
                changes_made.append(f"Recommended {len(review['missing_diagrams'])} diagrams")
            
            if review.get("technical_corrections"):
                changes_made.append(f"Suggested {len(review['technical_corrections'])} technical corrections")
            
            # Store review in metadata for next agent
            metadata = {
                "technical_review": review,
                "technical_score": review.get("technical_score", 0)
            }
            
            return AgentResult(
                content=context.content,  # No content changes, just review
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
                warnings=[f"Failed to parse review JSON: {str(e)}"],
                metadata={"raw_response": response}
            )

