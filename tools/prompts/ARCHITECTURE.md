# Prompt Pipeline Architecture

## Overview

The Prompt Pipeline is a SOLID-based system for transforming rough draft documents into polished, professional documentation using AI agents. It follows enterprise software design principles and integrates seamlessly with the existing PDF generation pipeline.

## Design Principles

### SOLID Compliance

**Single Responsibility Principle (SRP)**
- Each agent has one specific job (analyze, enhance, review, polish)
- Prompt library only handles template loading
- Executor only handles LLM communication
- Orchestrator only coordinates agent sequence

**Open/Closed Principle (OCP)**
- Easy to add new agents without modifying existing code
- New prompt templates can be added without code changes
- New LLM providers can be added by implementing `IPromptExecutor`

**Liskov Substitution Principle (LSP)**
- All agents implement `IDocumentAgent` and are interchangeable
- All executors implement `IPromptExecutor` and are interchangeable
- Orchestrator works with any agent that follows the interface

**Interface Segregation Principle (ISP)**
- Clean, focused interfaces: `IPromptLibrary`, `IDocumentAgent`, `IPromptExecutor`, `IAgentOrchestrator`
- No client is forced to depend on methods it doesn't use

**Dependency Inversion Principle (DIP)**
- Agents depend on `IPromptExecutor` abstraction, not concrete implementations
- Orchestrator depends on `IDocumentAgent` abstraction
- High-level modules don't depend on low-level modules

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer                            │
│  (cli.py - User interface, argument parsing)            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Orchestration Layer                      │
│  (orchestrator.py - Agent coordination, flow control)   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                           │
│  (agents/* - Document processing logic)                 │
│  • StructureAnalyzerAgent                               │
│  • ContentEnhancerAgent                                 │
│  • TechnicalReviewerAgent                               │
│  • StylePolisherAgent                                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                           │
│  • PromptLibrary (template loading)                     │
│  • PromptExecutor (LLM communication)                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Core Layer                             │
│  (core/* - Interfaces, models, exceptions)              │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

```
Input: rough_draft.md
    ↓
[Load Document] → DocumentContext
    ↓
[Structure Analyzer]
    ├─ Load prompt: library/architecture/analyze.md
    ├─ Execute via IPromptExecutor
    ├─ Parse JSON response
    └─ Return AgentResult (analysis metadata)
    ↓
[Content Enhancer]
    ├─ Load prompt: library/architecture/enhance.md
    ├─ Inject analysis from previous agent
    ├─ Execute via IPromptExecutor
    ├─ Parse enhanced markdown
    └─ Return AgentResult (updated content)
    ↓
[Technical Reviewer]
    ├─ Load prompt: library/architecture/review.md
    ├─ Execute via IPromptExecutor
    ├─ Parse JSON response
    └─ Return AgentResult (review metadata)
    ↓
[Style Polisher]
    ├─ Load prompt: library/architecture/polish.md
    ├─ Execute via IPromptExecutor
    ├─ Parse polished markdown
    └─ Return AgentResult (final content)
    ↓
[Save Document] → polished.md
[Save History] → polished.history.txt
[Save Diff] → polished.diff.txt
```

## Key Components

### DocumentContext
Carries state through the pipeline:
- `content`: Current document content
- `metadata`: Accumulated metadata from agents
- `history`: Audit trail of transformations
- `source_file`: Original input file

### AgentResult
Returned by each agent:
- `content`: Processed content
- `success`: Whether processing succeeded
- `changes_made`: List of changes for logging
- `warnings`: Any issues encountered
- `metadata`: Additional data for next agent

### PromptConfig
Defines pipeline behavior:
- `pipeline_name`: Descriptive name
- `document_type`: Category (architecture, technical, business)
- `agents`: List of agents to run
- `default_model`: LLM model to use
- `preserve_history`: Save processing history
- `generate_diff`: Generate diff file

## Agent Communication

Agents communicate through `DocumentContext`:

```python
# Agent 1: Structure Analyzer
result1 = await analyzer.process(context)
context.content = result1.content  # Usually unchanged
context.metadata["analysis"] = result1.metadata["analysis"]

# Agent 2: Content Enhancer
# Can access analysis from Agent 1
analysis = context.metadata.get("analysis", {})
result2 = await enhancer.process(context)
context.content = result2.content  # Updated content

# Agent 3: Technical Reviewer
# Works with enhanced content from Agent 2
result3 = await reviewer.process(context)
context.metadata["technical_review"] = result3.metadata["technical_review"]

# Agent 4: Style Polisher
# Final polish on enhanced content
result4 = await polisher.process(context)
context.content = result4.content  # Final content
```

## Extensibility

### Adding a New Agent

1. **Create agent class**:
```python
class DiagramGeneratorAgent(BaseDocumentAgent):
    def prepare_context(self, context: DocumentContext) -> dict:
        return {"document_content": context.content}
    
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        # Extract Mermaid diagrams from response
        # Insert into document
        return AgentResult(...)
```

2. **Create prompt template**:
```
library/architecture/generate_diagrams.md
```

3. **Register in CLI**:
```python
agent_map = {
    ...
    "diagram_generator": DiagramGeneratorAgent
}
```

4. **Add to pipeline config**:
```yaml
agents:
  - name: "diagram_generator"
    enabled: true
    temperature: 0.7
```

### Adding a New LLM Provider

Implement `IPromptExecutor`:

```python
class CustomLLMExecutor(IPromptExecutor):
    async def execute(self, prompt, context, model, temperature):
        # Call your LLM API
        # Return response string
        pass
```

Register in CLI:
```python
if executor_type == "custom":
    prompt_executor = CustomLLMExecutor()
```

### Adding a New Document Type

1. Create new prompt category:
```
library/technical/
├── analyze.md
├── enhance.md
└── polish.md
```

2. Create pipeline config:
```yaml
# pipelines/technical-doc.yaml
pipeline_name: "Technical Documentation"
document_type: "technical"
agents: [...]
```

## Error Handling

- **PromptNotFoundError**: Prompt template doesn't exist
- **AgentExecutionError**: Agent processing failed
- **LLMExecutionError**: LLM API call failed
- **ValidationError**: Document validation failed
- **ConfigurationError**: Invalid configuration

All exceptions inherit from `PromptPipelineError` for easy catching.

## Testing Strategy

### Unit Tests
- Test each agent in isolation with mock executor
- Test prompt library loading
- Test configuration parsing

### Integration Tests
- Test full pipeline with mock executor
- Verify agent communication via DocumentContext
- Validate output files

### End-to-End Tests
- Test with real LLM APIs (in CI with API keys)
- Validate final document quality

## Performance Considerations

- **Async execution**: All agents use async/await for efficient I/O
- **Streaming**: Future enhancement for real-time feedback
- **Caching**: Could cache LLM responses for repeated runs
- **Parallel execution**: Future enhancement for independent agents

## Integration with PDF Pipeline

```bash
# Complete workflow
python -m tools.prompts.cli \
    rough_draft.md \
    polished.md \
    -c tools/prompts/pipelines/architecture-proposal.yaml

python tools/pdf/md2pdf.py \
    polished.md \
    --profile project-docs \
    --generate-cover \
    --generate-toc
```

## Future Enhancements

1. **Interactive Mode**: Human-in-the-loop for reviewing agent suggestions
2. **Batch Processing**: Process multiple documents in parallel
3. **Web UI**: Non-technical users can upload drafts and get polished docs
4. **Template Generator**: AI generates document templates from descriptions
5. **Multi-document Consistency**: Ensure terminology consistency across docs
6. **Diagram Generation**: Auto-generate Mermaid diagrams from descriptions
7. **Citation Manager**: Auto-add references and citations
8. **Version Control Integration**: Track document evolution in Git

