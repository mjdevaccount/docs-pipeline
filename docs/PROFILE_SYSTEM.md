# PDF Profile System

## Overview

The docs-pipeline now includes a powerful **Profile System** that allows you to generate dramatically different-looking PDFs from the same content. Instead of modifying your markdown or manually tweaking CSS, you can simply select a profile to instantly change the visual style of your entire document.

## What is a Profile?

A profile is a named collection of visual settings that controls:
- **Typography** (fonts, sizes, weights, spacing)
- **Color scheme** (headings, links, code blocks, callouts)
- **Layout** (margins, page size, spacing)
- **Visual treatment** (borders, shadows, backgrounds)

## Available Profiles

### 1. Tech Whitepaper (Default)
**Best for:** Technical specifications, engineering documentation, API docs

**Characteristics:**
- Clean, professional engineering documentation style
- Blue accents (#2b6cb0, #3182ce)
- Generous margins (2.5cm top/bottom, 2cm sides)
- Clear visual hierarchy with bordered headings
- Light gray code blocks with dark background for syntax
- Perfect for technical specs and detailed documentation

**Example:**
```bash
python tools/pdf/md2pdf.py input.md --profile tech-whitepaper
```

### 2. Dark Pro
**Best for:** On-screen presentations, modern product docs, demo materials

**Characteristics:**
- Modern dark theme for on-screen viewing
- Dark background (#0f172a) with light text
- High contrast with neon blue accents (#3b82f6, #60a5fa)
- Dramatic presentation with subtle glows and shadows
- Code blocks pop with very dark backgrounds
- Diagrams highlighted with drop shadows
- Excellent for "look at this PDF on screen" scenarios

**Example:**
```bash
python tools/pdf/md2pdf.py input.md --profile dark-pro --renderer playwright
```

### 3. Minimalist
**Best for:** Architecture docs, RFCs, executive summaries

**Characteristics:**
- Clean, spacious design with maximum whitespace
- Thin typography (font-weight: 300)
- Subtle, muted colors
- No borders, no boxes - just clean text
- Very generous margins (3.5cm top/bottom, 3cm sides)
- Tables with no borders, just spacing
- Perfect for architecture diagrams and high-level content

**Example:**
```bash
python tools/pdf/md2pdf.py input.md --profile minimalist
```

### 4. Enterprise Blue
**Best for:** Business documents, corporate reports, client deliverables

**Characteristics:**
- Corporate-friendly, conservative styling
- Blue and gray color scheme (#003d7a, #0066cc)
- Structured layout with professional header bars
- Tables with corporate blue headers and hover effects
- Framed images with subtle shadows
- Perfect for documents that need to match corporate branding

**Example:**
```bash
python tools/pdf/md2pdf.py input.md --profile enterprise-blue
```

## Usage

### CLI

```bash
# Generate with a specific profile
python tools/pdf/md2pdf.py input.md --profile dark-pro

# Specify output location
python tools/pdf/md2pdf.py input.md --output reports/spec.pdf --profile minimalist

# Combine with renderer selection
python tools/pdf/md2pdf.py input.md --profile enterprise-blue --renderer playwright
```

### Pipeline YAML

```yaml
workspaces:
  my-docs:
    documents:
      # Technical specification
      - input: docs/api-spec.md
        output: output/api-spec.pdf
        format: pdf
        renderer: playwright
        profile: tech-whitepaper
      
      # Architecture overview
      - input: docs/architecture.md
        output: output/architecture.pdf
        format: pdf
        renderer: playwright
        profile: minimalist
      
      # Executive summary
      - input: docs/executive-summary.md
        output: output/executive-summary.pdf
        format: pdf
        renderer: playwright
        profile: enterprise-blue
```

### Web UI

1. Upload your markdown file
2. Select your preferred **Profile** from the dropdown:
   - Tech Whitepaper (Default)
   - Dark Pro
   - Minimalist
   - Enterprise Blue
3. Select your **Renderer** (Playwright recommended)
4. Click "Generate PDF"

## Profile Showcase: Same Content, Different Styles

Want to see the dramatic differences? Run the demo pipeline:

```bash
python -m tools.docs_pipeline.cli --config docs-pipeline-profiles-demo.yaml
```

This will generate the same document in all 4 profiles:
- `architecture-overview-tech.pdf` (Tech Whitepaper)
- `architecture-overview-dark.pdf` (Dark Pro)
- `architecture-overview-minimalist.pdf` (Minimalist)
- `architecture-overview-enterprise.pdf` (Enterprise Blue)

Compare them side-by-side to see how profiles transform the same content!

## Profile Selection Guidelines

### Choose **Tech Whitepaper** for:
✅ Technical specifications  
✅ API documentation  
✅ Engineering design docs  
✅ Developer guides  
✅ Internal technical notes  

### Choose **Dark Pro** for:
✅ Presentation decks (viewed on screen)  
✅ Modern product documentation  
✅ Demo materials  
✅ Portfolio pieces  
✅ Marketing/sales technical content  

### Choose **Minimalist** for:
✅ Architecture Decision Records (ADRs)  
✅ RFC-style documents  
✅ Executive summaries  
✅ High-level overviews  
✅ Clean, diagram-focused content  

### Choose **Enterprise Blue** for:
✅ Client deliverables  
✅ Business reports  
✅ Corporate documentation  
✅ Proposals and RFPs  
✅ Anything that needs to look "corporate-professional"  

## Technical Details

### How Profiles Work

1. **Profile Definition** (`tools/pdf/profiles.py`):
   - Each profile maps a name to a CSS file
   - Profiles can also specify logos, theme configs, etc.

2. **CSS Files** (`tools/pdf/styles/`):
   - Each profile has a dedicated CSS file
   - CSS files define complete styling (typography, colors, layout)
   - Compatible with both WeasyPrint and Playwright renderers

3. **Profile Resolution**:
   - CLI: `--profile` argument → profile name
   - Pipeline: `profile:` key in YAML → profile name
   - Web: dropdown selection → profile name
   - All paths converge on `markdown_to_pdf(..., profile=name)`

4. **CSS Injection**:
   - Profile name → CSS file path lookup
   - CSS loaded and injected into HTML before PDF rendering
   - Explicit `--css` argument overrides profile CSS

### Creating Custom Profiles

1. Create a new CSS file in `tools/pdf/styles/`:
   ```bash
   # Example: tools/pdf/styles/my-custom-profile.css
   ```

2. Add profile to `tools/pdf/profiles.py`:
   ```python
   PROFILES: Dict[str, DocumentProfile] = {
       "my-custom": DocumentProfile(
           name="my-custom",
           logo=None,
           css=_rel_from_repo_root("tools", "pdf", "styles", "my-custom-profile.css"),
           theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
           reference_docx=None,
       ),
       # ... other profiles
   }
   ```

3. Use your custom profile:
   ```bash
   python tools/pdf/md2pdf.py input.md --profile my-custom
   ```

### CSS Compatibility

Profiles are designed to work with both renderers:
- **WeasyPrint**: Supports standard CSS, some paged media features
- **Playwright**: Full modern CSS support, better rendering fidelity

For best results, use **Playwright** renderer with all profiles.

## Examples

### Generate Same Doc with Multiple Profiles

```bash
# Tech Whitepaper style
python tools/pdf/md2pdf.py spec.md --output spec-tech.pdf --profile tech-whitepaper

# Dark Pro style
python tools/pdf/md2pdf.py spec.md --output spec-dark.pdf --profile dark-pro

# Minimalist style
python tools/pdf/md2pdf.py spec.md --output spec-minimal.pdf --profile minimalist

# Enterprise Blue style
python tools/pdf/md2pdf.py spec.md --output spec-enterprise.pdf --profile enterprise-blue
```

### Pipeline with Mixed Profiles

```yaml
workspaces:
  product-docs:
    documents:
      # API docs in tech style
      - input: docs/api.md
        output: dist/api-reference.pdf
        profile: tech-whitepaper
      
      # Product overview in minimalist style
      - input: docs/overview.md
        output: dist/product-overview.pdf
        profile: minimalist
      
      # Sales deck in dark pro
      - input: docs/pitch.md
        output: dist/pitch-deck.pdf
        profile: dark-pro
```

## Troubleshooting

### Profile Not Found
```
[WARN] Profile 'xyz' not found, using defaults
```
**Solution:** Check profile name spelling. Valid profiles: `tech-whitepaper`, `dark-pro`, `minimalist`, `enterprise-blue`

### CSS Not Loading
```
[WARN] CSS file not found: ...
```
**Solution:** Ensure CSS file exists in `tools/pdf/styles/`. Run from project root.

### Dark Profile Not Dark in Print
**Issue:** Dark backgrounds may not print well  
**Solution:** Dark Pro is optimized for on-screen viewing. For print, use Tech Whitepaper or Enterprise Blue.

## Summary

The profile system gives you **4 distinct visual styles** without changing your content:

1. **Tech Whitepaper** → Professional engineering docs
2. **Dark Pro** → Modern on-screen presentations
3. **Minimalist** → Clean architecture docs
4. **Enterprise Blue** → Corporate business documents

Simply select the profile that matches your use case, and let the system handle the styling!

