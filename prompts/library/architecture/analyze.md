# Structure Analyzer Prompt - Architecture Proposals

You are an expert technical architect reviewing a draft architecture proposal. Your task is to analyze the document structure and identify gaps, inconsistencies, and areas for improvement.

## Input Document
```markdown
{document_content}
```

## Your Task

Analyze the document and provide:

1. **Structure Assessment**
   - Does it have proper frontmatter (title, author, date, organization)?
   - Are all essential sections present?
   - Is the section hierarchy logical?

2. **Content Gaps**
   - Missing technical details
   - Undefined terms or concepts
   - Incomplete diagrams or missing visual aids
   - Missing context or background

3. **Consistency Issues**
   - Inconsistent terminology
   - Conflicting statements
   - Unclear or ambiguous language

4. **Required Sections for Architecture Proposals**
   - Executive Summary / Purpose
   - Current System Overview
   - Problem Definition
   - Proposed Solution
   - Architecture Vision
   - Implementation Phases
   - Technical Specifications
   - Benefits / Value Proposition
   - Risks and Mitigation
   - Success Metrics

## Output Format

Provide your analysis as a structured JSON object:

```json
{{
  "structure_score": 0-100,
  "missing_sections": ["section1", "section2"],
  "content_gaps": [
    {{"section": "...", "issue": "...", "severity": "high|medium|low"}}
  ],
  "consistency_issues": [
    {{"issue": "...", "locations": ["...", "..."], "suggestion": "..."}}
  ],
  "recommendations": [
    {{"priority": "high|medium|low", "action": "...", "rationale": "..."}}
  ]
}}
```

Focus on actionable feedback that will help create a professional, complete architecture proposal.

