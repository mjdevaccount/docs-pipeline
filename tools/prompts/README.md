# Prompt-Driven Document Pipeline

A SOLID-based system for transforming rough draft documents into polished, professional documentation using AI agents.

## Architecture

```
Rough Draft (MD)
    ↓
[Structure Analyzer] → Identifies gaps, inconsistencies
    ↓
[Content Enhancer] → Expands, clarifies, adds detail
    ↓
[Technical Reviewer] → Validates accuracy, suggests diagrams
    ↓
[Style Polisher] → Ensures consistency, professional tone
    ↓
Structured Document (MD)
    ↓
[md2pdf Pipeline] → PDF/DOCX
```

## SOLID Design

- **Single Responsibility**: Each agent has one job
- **Open/Closed**: Easy to add new agents without modifying existing code
- **Liskov Substitution**: All agents implement `IDocumentAgent`
- **Interface Segregation**: Clean interfaces for library, executor, orchestrator
- **Dependency Inversion**: Agents depend on abstractions, not concrete implementations

## Directory Structure

```
tools/prompts/
├── core/                      # Core interfaces and models
│   ├── interfaces.py          # IPromptExecutor, IDocumentAgent, etc.
│   ├── models.py              # DocumentContext, AgentResult, etc.
│   └── exceptions.py          # Custom exceptions
├── agents/                    # Agent implementations
│   ├── base.py                # BaseDocumentAgent
│   ├── structure_analyzer.py  # Analyzes structure
│   ├── content_enhancer.py    # Enhances content
│   ├── technical_reviewer.py  # Reviews technical accuracy
│   └── style_polisher.py      # Polishes style
├── library/                   # Prompt templates
│   ├── architecture/          # Architecture proposal prompts
│   │   ├── analyze.md
│   │   ├── enhance.md
│   │   ├── review.md
│   │   └── polish.md
│   ├── technical/             # Technical doc prompts (future)
│   └── business/              # Business case prompts (future)
├── pipelines/                 # Pipeline configurations
│   └── architecture-proposal.yaml
├── library.py                 # FileSystemPromptLibrary
├── executor.py                # OpenAI/Anthropic executors
├── orchestrator.py            # AgentOrchestrator
└── cli.py                     # Command-line interface
```

## Usage

### Basic Usage

```bash
# Transform a rough draft into a polished document
cd tools/prompts
python -m cli \
    input_draft.md \
    output_polished.md \
    --config pipelines/architecture-proposal.yaml \
    --verbose
```

### With OpenAI (default)

```bash
cd tools/prompts
export OPENAI_API_KEY="your-api-key"
python -m cli rough_draft.md polished.md -c pipelines/architecture-proposal.yaml
```

### With Anthropic Claude

```bash
cd tools/prompts
export ANTHROPIC_API_KEY="your-api-key"
python -m cli rough_draft.md polished.md -c pipelines/architecture-proposal.yaml --executor anthropic
```

### List Available Prompts

```bash
cd tools/prompts
python -m cli --list-prompts
```

## Pipeline Configuration

Example `architecture-proposal.yaml`:

```yaml
pipeline_name: "Architecture Proposal Refinement"
document_type: "architecture"

default_model: "gpt-4"
default_temperature: 0.7

agents:
  - name: "structure_analyzer"
    enabled: true
    temperature: 0.3
    
  - name: "content_enhancer"
    enabled: true
    temperature: 0.7
    
  - name: "technical_reviewer"
    enabled: true
    temperature: 0.3
    
  - name: "style_polisher"
    enabled: true
    temperature: 0.5

preserve_history: true
generate_diff: true
require_frontmatter: true
```

## Agent Flow

### 1. Structure Analyzer
- **Input**: Rough draft markdown
- **Output**: JSON analysis with gaps, issues, recommendations
- **Temperature**: 0.3 (analytical)

### 2. Content Enhancer
- **Input**: Rough draft + analysis
- **Output**: Enhanced markdown with expanded content
- **Temperature**: 0.7 (creative)

### 3. Technical Reviewer
- **Input**: Enhanced markdown
- **Output**: JSON review with technical issues, diagram suggestions
- **Temperature**: 0.3 (analytical)

### 4. Style Polisher
- **Input**: Enhanced markdown
- **Output**: Polished, publication-ready markdown
- **Temperature**: 0.5 (balanced)

## Output Files

After running the pipeline, you'll get:

- `output.md` - Polished document
- `output.history.txt` - Processing history (if `preserve_history: true`)
- `output.diff.txt` - Changes made (if `generate_diff: true`)

## Integration with PDF Pipeline

```bash
# Step 1: Transform rough draft to polished document
cd tools/prompts
python -m cli \
    rough_draft.md \
    polished.md \
    -c pipelines/architecture-proposal.yaml

# Step 2: Generate PDF
cd ../pdf
python md2pdf.py \
    ../polished.md \
    --profile reporting-manager \
    --generate-cover \
    --generate-toc
```

## Adding New Agents

1. Create agent class inheriting from `BaseDocumentAgent`
2. Implement `prepare_context()` and `parse_result()`
3. Add prompt template to `library/`
4. Register in `cli.py` agent map
5. Add to pipeline configuration

Example:

```python
class DiagramGeneratorAgent(BaseDocumentAgent):
    @property
    def name(self) -> str:
        return "Diagram Generator"
    
    def prepare_context(self, context: DocumentContext) -> dict:
        return {"document_content": context.content}
    
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        # Parse Mermaid diagrams from response
        # Insert into document
        return AgentResult(...)
```

## Testing

```bash
# Use mock executor for testing without API calls
cd tools/prompts
python -m cli \
    test_input.md \
    test_output.md \
    -c pipelines/architecture-proposal.yaml \
    --executor mock \
    --verbose
```

## Dependencies

```bash
pip install openai anthropic pyyaml colorama
```

## Future Enhancements

- [ ] Diagram generation agent (Mermaid from descriptions)
- [ ] Cross-reference validator
- [ ] Glossary generator
- [ ] Multi-document consistency checker
- [ ] Template-based document generator
- [ ] Interactive mode with human-in-the-loop
- [ ] Batch processing for multiple documents
- [ ] Web UI for non-technical users

