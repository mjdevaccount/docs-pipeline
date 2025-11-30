# Prompt Pipeline Quick Start

## What Is This?

A SOLID-based AI agent system that transforms rough draft documents into polished, professional documentation ready for PDF generation.

## Quick Example

**Input (rough_draft.md):**
```markdown
# Cache Manager Enhancement

## Problem
The current market data caching is inefficient...
```

**Output (polished.md):**
- ✅ Proper structure and sections
- ✅ Expanded content with technical depth
- ✅ Technical accuracy validated
- ✅ Professional style and consistency
- ✅ Ready for PDF generation

## Installation

```bash
cd tools/prompts
pip install -r requirements.txt

# Set your API key
export OPENAI_API_KEY="your-key-here"
# OR
export ANTHROPIC_API_KEY="your-key-here"
```

## Basic Usage

```bash
# Transform a rough draft
python -m tools.prompts.cli \
    examples/rough_draft_example.md \
    output/polished.md \
    --config pipelines/architecture-proposal.yaml \
    --verbose

# Then generate PDF
python tools/pdf/md2pdf.py \
    output/polished.md \
    --profile reporting-manager \
    --generate-cover \
    --generate-toc
```

## How It Works

```
Rough Draft
    ↓
[Structure Analyzer] → "Missing sections: X, Y, Z"
    ↓
[Content Enhancer] → Expands thin sections, adds detail
    ↓
[Technical Reviewer] → "Add diagram here, clarify this"
    ↓
[Style Polisher] → Ensures consistency, professional tone
    ↓
Polished Document → Ready for PDF
```

## Agent Flow

1. **Structure Analyzer** (analytical, temp=0.3)
   - Identifies missing sections
   - Finds content gaps
   - Detects inconsistencies
   - Returns JSON analysis

2. **Content Enhancer** (creative, temp=0.7)
   - Expands thin sections
   - Adds technical depth
   - Clarifies ambiguities
   - Returns enhanced markdown

3. **Technical Reviewer** (analytical, temp=0.3)
   - Validates architecture patterns
   - Checks technical accuracy
   - Suggests diagrams
   - Returns JSON review

4. **Style Polisher** (balanced, temp=0.5)
   - Ensures consistency
   - Improves clarity
   - Professional formatting
   - Returns final markdown

## Configuration

Edit `pipelines/architecture-proposal.yaml`:

```yaml
pipeline_name: "Architecture Proposal Refinement"
document_type: "architecture"

default_model: "gpt-4"  # or "claude-3-sonnet-20240229"
default_temperature: 0.7

agents:
  - name: "structure_analyzer"
    enabled: true
    temperature: 0.3
  # ... more agents

preserve_history: true  # Save .history.txt
generate_diff: true     # Save .diff.txt
```

## Output Files

After running, you get:

- `polished.md` - Final document
- `polished.history.txt` - Processing log
- `polished.diff.txt` - Changes made

## Tips

1. **Start with frontmatter** in your rough draft:
```yaml
---
title: Your Title
author: Your Name
organization: Your Company
date: November 2025
---
```

2. **Include key sections** even if brief:
   - Current System Overview
   - Problem Definition
   - Proposed Solution
   - Architecture Vision

3. **Use mock executor for testing**:
```bash
python -m tools.prompts.cli \
    input.md output.md \
    -c pipelines/architecture-proposal.yaml \
    --executor mock
```

4. **Disable agents** in config if not needed:
```yaml
agents:
  - name: "technical_reviewer"
    enabled: false  # Skip this agent
```

## Integration with PDF Pipeline

Complete workflow:

```bash
# Step 1: Refine rough draft
python -m tools.prompts.cli \
    rough_draft.md \
    polished.md \
    -c tools/prompts/pipelines/architecture-proposal.yaml

# Step 2: Generate PDF
python tools/pdf/md2pdf.py \
    polished.md \
    --profile reporting-manager \
    --generate-cover \
    --generate-toc

# Result: Professional PDF in C:\documentpipeline\
```

## Troubleshooting

**"ModuleNotFoundError: No module named 'openai'"**
```bash
pip install -r tools/prompts/requirements.txt
```

**"LLMExecutionError: OpenAI API error"**
- Check your API key is set: `echo $OPENAI_API_KEY`
- Verify you have API credits
- Try with `--executor mock` to test without API

**"PromptNotFoundError"**
- Ensure you're running from repo root: `cd C:\Work`
- Check prompt exists: `python -m tools.prompts.cli --list-prompts`

## Next Steps

1. Try the example:
```bash
python -m tools.prompts.cli \
    tools/prompts/examples/rough_draft_example.md \
    output/test.md \
    -c tools/prompts/pipelines/architecture-proposal.yaml \
    --executor mock \
    --verbose
```

2. Create your own rough draft

3. Run the pipeline with real LLM

4. Generate PDF

5. Iterate and refine!

## Learn More

- `README.md` - Full documentation
- `ARCHITECTURE.md` - Design details
- `examples/` - Example documents
- `library/` - Prompt templates

