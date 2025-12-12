# Glossary Usage Guide

## Overview

The docs-pipeline glossary system provides professional term management and automatic highlighting for your documentation. This guide shows you how to:

- Create and validate glossary files
- Integrate glossaries with document conversion
- Generate glossary indexes
- Manage terminology across projects

---

## Quick Start

### 1. Using an Existing Glossary

```bash
# Convert document with glossary term highlighting
python -m tools.pdf.cli.main document.md output.pdf --glossary glossaries/technical.yaml
```

Output:
```
[OK] Created: output.pdf
[INFO] Glossary Processing Report
       Total Terms: 40
       Terms Found: 23
       Total Occurrences: 156
       Highlighted: 156
```

### 2. Generate a Glossary Index

```bash
# Create a printable glossary reference page
make glossary-index
```

This generates markdown files in `glossaries/indexes/`:
- `technical_index.md` - Alphabetized technical terms
- `business_index.md` - Business and organizational terms

### 3. Validate Your Glossary

```bash
# Check for issues and consistency
make glossary-validate

# Or individual glossary
python -m tools.pdf.cli.glossary_commands validate glossaries/technical.yaml
```

---

## Glossary File Format

Glossaries are YAML files with a simple structure:

```yaml
terms:
  - term: "API"
    definition: "Application Programming Interface - a set of protocols..."
    category: "Technical"
    synonyms: ["Application Program Interface", "Web Service"]
    see_also: ["REST", "SDK", "HTTP"]
    example: "The GitHub API allows developers to interact with repositories."
```

### Required Fields

- **term**: The term being defined (e.g., "API")
- **definition**: Clear, concise explanation of the term

### Optional Fields

- **category**: Group terms by category (e.g., "Technical", "Business")
- **synonyms**: Alternative names or abbreviations
- **see_also**: Related terms in the glossary
- **example**: Concrete usage example

---

## Creating a Custom Glossary

### Step 1: Create Glossary File

```bash
# Create a new glossary
touch glossaries/my-project.yaml
```

### Step 2: Add Terms

```yaml
# glossaries/my-project.yaml
terms:
  - term: "Cache Metrics"
    definition: "Statistics about cache performance including hit ratio and time saved."
    category: "Performance"
    synonyms: ["Cache Statistics", "Performance Metrics"]
    see_also: ["Cache", "Performance", "Optimization"]
    example: "Cache metrics showed a 75% hit ratio, saving 2.5 seconds per build."
  
  - term: "Incremental Build"
    definition: "A build process that only re-compiles files that have changed."
    category: "Build"
    synonyms: ["Incremental Compilation"]
    see_also: ["Cache", "Build", "Performance"]
    example: "Incremental builds reduced compilation time from 5 minutes to 30 seconds."
```

### Step 3: Validate

```bash
python -m tools.pdf.cli.glossary_commands validate glossaries/my-project.yaml
```

Expected output:
```
[OK] Glossary is valid: 2 terms
[INFO] Glossary Report
       Total Terms: 2
       Categories: 2
         - Performance: 1
         - Build: 1
```

---

## CLI Commands

### Validate Glossary

```bash
# Check for issues
python -m tools.pdf.cli.glossary_commands validate glossary.yaml

# With verbose output
python -m tools.pdf.cli.glossary_commands validate glossary.yaml --verbose
```

This checks:
- Empty definitions
- Broken cross-references (terms in `see_also` that don't exist)
- Duplicate terms

### Generate Index

```bash
# Create glossary index
python -m tools.pdf.cli.glossary_commands index glossary.yaml --output glossary-index.md

# View index
cat glossary-index.md
```

Generates:
- Table of contents
- Terms organized by category
- Definitions with examples
- Cross-references

### Highlight Terms

```bash
# Highlight terms in document
python -m tools.pdf.cli.glossary_commands highlight document.md glossary.yaml --output highlighted.md

# Case-sensitive matching
python -m tools.pdf.cli.glossary_commands highlight document.md glossary.yaml --case-sensitive

# Allow partial word matches
python -m tools.pdf.cli.glossary_commands highlight document.md glossary.yaml --partial-words
```

Outputs markdown with term references:
```markdown
An [API]{glossary:API} is a set of protocols...
```

### Generate Report

```bash
# Show glossary statistics
python -m tools.pdf.cli.glossary_commands report glossary.yaml

# Detailed report
python -m tools.pdf.cli.glossary_commands report glossary.yaml --verbose
```

Shows:
- Total terms and categories
- Term counts per category
- Validation issues
- Usage statistics

### Search Glossary

```bash
# Find terms matching a query
python -m tools.pdf.cli.glossary_commands search glossary.yaml API

# Search in definitions and synonyms
python -m tools.pdf.cli.glossary_commands search glossary.yaml "performance"
```

Finds matching:
- Term names
- Definitions
- Synonyms

---

## Makefile Targets

Quick commands for common glossary operations:

```bash
# Validate all glossaries
make glossary-validate

# Generate all indexes
make glossary-index

# Generate report
make glossary-report

# Full check
make glossary-check  # = validate + report
```

---

## Integration with Document Conversion

### Single Document

```bash
# Convert with glossary highlighting
python -m tools.pdf.cli.main document.md output.pdf --glossary glossaries/technical.yaml
```

### Batch Processing

```bash
# Use glossary for all documents
make batch-build INPUT_DIR=docs/ GLOSSARY=glossaries/technical.yaml
```

### Config File

```json
{
  "glossary": "glossaries/technical.yaml",
  "files": [
    {"input": "doc1.md", "output": "doc1.pdf"},
    {"input": "doc2.md", "output": "doc2.pdf", "glossary": "glossaries/business.yaml"}
  ]
}
```

---

## Best Practices

### 1. Organize by Domain

```
glossaries/
  ├── technical.yaml       # API, architecture, code terms
  ├── business.yaml        # Management, organizational terms
  ├── compliance.yaml       # Legal, regulatory terms
  └── indexes/             # Generated glossary pages
```

### 2. Use Consistent Formatting

- **Definitions**: 1-3 sentences, clear and concise
- **Examples**: Real usage, not contrived scenarios
- **Categories**: Use consistent category names across glossaries
- **Synonyms**: Include abbreviations (API vs Application Program Interface)

### 3. Maintain Cross-References

```yaml
# Good: Related terms that exist in glossary
see_also: ["REST", "SDK", "HTTP"]

# Bad: References to undefined terms
see_also: ["Random Term", "Undefined Concept"]
```

### 4. Keep Glossaries Fresh

```bash
# Regular validation
cron job: daily glossary validation

# Check before release
make glossary-check

# Update with new terminology
git commit -m "docs: add new technical glossary terms"
```

### 5. Document Evolution

Track glossary changes:
```
# v1.0 - Initial technical glossary
# v1.1 - Added 10 new terms
# v1.2 - Fixed broken cross-references
```

---

## Examples

### Example 1: Validate Technical Glossary

```bash
$ python -m tools.pdf.cli.glossary_commands validate glossaries/technical.yaml

[OK] Glossary is valid: 40 terms
[INFO] Glossary Report
       Total Terms: 40
       Categories: 6
         - Technical: 25
         - DevOps: 7
         - Testing: 5
         - Security: 3
```

### Example 2: Highlight Terms in Document

```bash
$ python -m tools.pdf.cli.glossary_commands highlight technical-guide.md glossaries/technical.yaml --output highlighted.md

[OK] Highlighted document: highlighted.md
[INFO] Glossary Processing Report
       Total Terms: 40
       Terms Found: 18
       Total Occurrences: 47
       Highlighted: 47
```

### Example 3: Generate Complete Index

```bash
$ python -m tools.pdf.cli.glossary_commands index glossaries/technical.yaml --output glossary-index.md

[OK] Generated glossary index: glossary-index.md
[INFO] Glossary Report
       Total Terms: 40
       Categories: 6
```

### Example 4: Batch Process with Glossary

```bash
$ python -m tools.pdf.cli.main --batch docs/*.md --glossary glossaries/technical.yaml --threads 4

[INFO] Processing 10 files with 4 threads...
[OK] Generated: docs/architecture.pdf
[OK] Generated: docs/api-guide.pdf
[OK] Generated: docs/deployment.pdf
...
[OK] Generated: docs/troubleshooting.pdf
```

---

## Troubleshooting

### Issue: Glossary File Not Found

```
[ERROR] Glossary file not found: glossary.yaml
```

**Solution**: Verify file path and extension (`.yaml` or `.json`)

```bash
ls -la glossaries/technical.yaml
```

### Issue: Invalid YAML Format

```
[ERROR] Failed to load glossary: mapping values are not allowed here
```

**Solution**: Check YAML syntax (indentation, quotes, colons)

```bash
python -c "import yaml; yaml.safe_load(open('glossary.yaml'))"
```

### Issue: Broken Cross-References

```
[WARNING] Term 'API' references undefined term 'UNDEFINED'
```

**Solution**: Check `see_also` values match existing terms

```bash
python -m tools.pdf.cli.glossary_commands validate glossary.yaml --verbose
```

### Issue: Terms Not Highlighted

Terms might not be highlighted if they:
- Are inside code blocks (intentional, not a bug)
- Don't match exactly (case sensitivity)
- Are only partial matches and `--partial-words` not used

**Solution**: Check matching rules

```bash
python -m tools.pdf.cli.glossary_commands search glossary.yaml "term name"
```

---

## Advanced Usage

### Combining Multiple Glossaries

```bash
# Highlight with technical terms
python -m tools.pdf.cli.main document.md output.pdf --glossary glossaries/technical.yaml

# Post-process for business terms (use intermediate file)
python -m tools.pdf.cli.glossary_commands highlight output-highlighted.md glossaries/business.yaml
```

### Custom Glossary Generation

```python
from tools.pdf.core.glossary_processor import GlossaryProcessor

processor = GlossaryProcessor('glossary.yaml')

# Generate markdown index
index = processor.generate_index()
print(index)

# Highlight document content
with open('document.md') as f:
    content = f.read()
    highlighted = processor.highlight_terms(content)

# Access statistics
if processor.stats:
    print(f"Found {processor.stats.terms_found} terms")
    print(f"Hit {processor.stats.occurrences} occurrences")
```

---

## Summary

The glossary system provides:

✅ Professional terminology management  
✅ Automatic term highlighting  
✅ Cross-reference validation  
✅ Index generation  
✅ Batch processing support  
✅ Multiple format support (YAML/JSON)  
✅ CLI and programmatic interfaces  

**Start using glossaries today:**

```bash
# 1. Validate existing glossaries
make glossary-validate

# 2. Generate indexes
make glossary-index

# 3. Use in document conversion
python -m tools.pdf.cli.main doc.md output.pdf --glossary glossaries/technical.yaml
```

---

**See also:**
- `PRIORITY_4_IMPLEMENTATION_COMPLETE.md` - Technical details
- `glossaries/technical.yaml` - Example technical terms
- `glossaries/business.yaml` - Example business terms
