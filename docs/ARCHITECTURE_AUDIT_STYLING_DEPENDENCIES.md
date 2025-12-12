# 📋 Architecture Audit: Styling & Dependency Management

**Date**: December 12, 2025, 5:16 PM CST  
**Scope**: CSS/theme management, color systems, Python dependencies  
**Status**: Complete audit with recommendations

---

## 🔍 Current State

### CSS/Theme Files (MANUALLY MANAGED)

**Location**: `tools/pdf/styles/`

| File | Size | Purpose | Issues |
|------|------|---------|--------|
| `dark-pro.css` | 27.5 KB | Dark theme (primary) | 80+ CSS variables, manually maintained |
| `enterprise-blue.css` | 17.5 KB | Corporate theme | Duplicate color definitions |
| `tech-whitepaper.css` | 20.1 KB | Technical style | Separate color palette |
| `minimalist.css` | 17.4 KB | Minimal style | Another color system |
| `playwright.css` | 14.2 KB | Playwright branding | Yet another color palette |
| `layout.css` | 2.0 KB | Layout utilities | Thin but separate |
| **Total** | **98.7 KB** | **5 themes** | ❌ **5 separate color systems** |

### Color Duplication

```
dark-pro.css:
  --color-primary: #60a5fa
  --mermaid-primaryColor: #0f172a
  (80+ variables)

enterprise-blue.css:
  Same colors, different names
  No shared system

tech-whitepaper.css:
  Another palette
  No consistency

minimalist.css:
  Another palette
  Manual maintenance

playwright.css:
  Another palette
  Another system
```

### Theme Selection (Manual)

**File**: `tools/pdf/config/profiles.py`

```python
PROFILES = {
    "tech-whitepaper": DocumentProfile(
        css=".../styles/tech-whitepaper.css",  # Hardcoded path
        # Each profile manually linked
    ),
    "dark-pro": DocumentProfile(
        css=".../styles/dark-pro.css",  # Manual
    ),
    # 5 more profiles...
}
```

**Problem**: Profiles hardcoded, no configuration system, colors not centralized.

### Markdown → HTML → PDF Flow

```
Markdown (source)
    ↓
Pandoc (converts to HTML)
    ↓
CSS injected (one of 5 themes)
    ↓
Mermaid 11 (reads CSS variables)
    ↓
Playwright (renders to PDF)
    ↓
PDF with colors
```

**Problem**: Colors split across Markdown CSS + Mermaid-specific CSS variables.

---

## 🐍 Python Dependencies Audit

### Current Versions

```
Root Requirements (requirements.txt):
  pyyaml>=6.0              ✅ Current
  click>=8.1.0             ✅ Current
  flask>=3.0.0             ✅ Current
  werkzeug>=3.0.0          ✅ Current

PDF Requirements (requirements-pdf.txt):
  playwright>=1.45.0       ✅ Updated (was >=1.40.0)
  PyPDF2>=4.0.0            ✅ Updated (was >=3.0.0)
  pyyaml>=6.0              ✅ Current
  colorama>=0.4.6          ✅ Current
  tqdm>=4.65.0             ✅ Current
  pytest>=8.0.0            ✅ Updated (was >=7.4.0)
  pytest-cov>=5.0.0        ✅ Updated (was >=4.1.0)
  pytest-xdist>=3.5.0      ✅ Updated (was >=3.3.0)
  pytest-watch>=4.2.0      ✅ Current
```

### What's Missing?

```
❌ No color management library
   (Using manual CSS variables)

❌ No design token system
   (Duplicated across 5 CSS files)

❌ No theme generation tool
   (Hardcoded profiles)

❌ No CSS preprocessing
   (No SCSS/Less for variables/mixins)

❌ No schema validation for colors/themes
   (Manual maintenance = errors)

❌ No version pinning for Pandoc
   (System dependency, unmanaged)
```

### What Should Be Added?

| Library | Purpose | Status | Notes |
|---------|---------|--------|-------|
| **Pydantic** | Data validation | Already have v2+ | Add Color types for validation |
| **colorspacious** or **colormath** | Color space conversions | ❌ Missing | For color harmonies, accessibility |
| **Jinja2** | Template-based CSS generation | ⚠️ Maybe | Generate themes from tokens |
| **python-sass** or **libsass** | CSS preprocessing | ❌ Missing | Variables, mixins, nesting |
| **tomli** / **tomllib** | TOML config parsing | ✅ Python 3.11+ | For design token TOML files |

---

## 🎨 What Should Be Outsourced

### ❌ Currently Manual (Should Automate)

#### 1. **Color System Management**

**Current State**:
```css
/* dark-pro.css */
--mermaid-primaryColor: #0f172a;
--mermaid-primaryTextColor: #f3f4f6;
--mermaid-primaryBorderColor: #60a5fa;
-- ... 77 more variables ...

/* enterprise-blue.css */
-- Same colors, different values, different names --
```

**Should Be**:
```yaml
# design-tokens.yml (Single source of truth)
themes:
  dark-pro:
    colors:
      primary: "#0f172a"
      primaryText: "#f3f4f6"
      primaryBorder: "#60a5fa"
  
  enterprise-blue:
    colors:
      primary: "#1e3a5f"
      primaryText: "#ffffff"
      primaryBorder: "#2563eb"
```

**Why**: One source of truth, auto-generate CSS, validate colors.

#### 2. **CSS Generation from Tokens**

**Current State**: Manual CSS files (98.7 KB)  
**Should Be**: Generate from tokens.yml

```python
# tools/pdf/config/theme_generator.py
from pathlib import Path
import yaml

def generate_css_from_tokens(tokens_file: str, output_dir: str):
    """Generate all theme CSS files from single tokens file."""
    with open(tokens_file) as f:
        tokens = yaml.safe_load(f)
    
    for theme_name, theme_tokens in tokens['themes'].items():
        css = generate_css_variables(theme_tokens)
        (Path(output_dir) / f"{theme_name}.css").write_text(css)
```

**Benefits**:
- Single source of truth
- Automatic consistency
- Easy theme creation
- Reduces maintenance

#### 3. **Color Validation & Accessibility**

**Current State**: Manual (no validation)  
**Should Be**: Automatic

```python
# Validate colors are valid hex/rgb/hsl
from pydantic import BaseModel, Field
from pydantic_extra_types.color import Color

class ThemeColors(BaseModel):
    primary: Color  # Auto-validates hex/rgb/hsl
    text: Color
    border: Color
    
    # Validate contrast ratios
    @field_validator('text')
    def check_contrast(cls, v, info):
        primary = info.data.get('primary')
        if not has_sufficient_contrast(primary, v):
            raise ValueError(f"Contrast insufficient: {primary} on {v}")
        return v
```

#### 4. **Theme Profile Configuration**

**Current State**: Hardcoded in Python  
**Should Be**: Data-driven TOML/YAML

```toml
# profiles.toml (Replaces profiles.py)
[tech-whitepaper]
name = "Technical Whitepaper"
css = "tech-whitepaper.css"
theme_tokens = "tech-whitepaper"
logo = null

[dark-pro]
name = "Dark Pro"
css = "dark-pro.css"
theme_tokens = "dark-pro"
logo = null
```

**Why**: Non-code configuration, easier to update.

---

## 🏗️ Recommended Architecture

### New Structure

```
tools/pdf/
├── config/
│   ├── profiles.toml          ← NEW: Profile definitions
│   ├── design-tokens.yml      ← NEW: Single token source
│   ├── profiles.py            ← Keep for backward compat
│   └── theme_generator.py     ← NEW: Auto-generates CSS
│
├── styles/
│   ├── _base.css              ← NEW: Shared base styles
│   ├── _variables.css         ← GENERATED: From tokens
│   ├── dark-pro.css           ← Keep (or auto-generate)
│   ├── enterprise-blue.css    ← Keep (or auto-generate)
│   └── ... (others)
│
└── pipeline/
    └── steps/
        ├── theme_validation_step.py  ← NEW: Validate tokens
        └── mermaid_enhancement_step.py
```

### Design Tokens File (Single Source)

```yaml
# tools/pdf/config/design-tokens.yml
---
version: "1.0"
description: "Central design token system for all themes"

# Global tokens (used across all themes)
global:
  fonts:
    body: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI'"
    mono: "JetBrains Mono, 'SF Mono', Menlo, monospace"
  
  spacing:
    xs: "4px"
    sm: "8px"
    md: "16px"
    lg: "24px"
    xl: "32px"
  
  radius:
    sm: "4px"
    md: "8px"
    lg: "12px"

# Theme-specific tokens
themes:
  dark-pro:
    metadata:
      name: "Dark Pro"
      description: "Modern dark theme for on-screen viewing"
    
    colors:
      # Primary palette
      primary:
        background: "#0f172a"
        surface: "#1e293b"
        border: "#60a5fa"
        text: "#f3f4f6"
      
      # Status colors
      success: "#10b981"
      warning: "#f59e0b"
      error: "#ef4444"
      info: "#06b6d4"
      
      # Mermaid specific
      mermaid:
        primaryColor: "#0f172a"
        primaryTextColor: "#f3f4f6"
        primaryBorderColor: "#60a5fa"
        # ... 60+ more
  
  enterprise-blue:
    metadata:
      name: "Enterprise Blue"
      description: "Corporate-friendly, conservative styling"
    
    colors:
      primary:
        background: "#ffffff"
        surface: "#f8f9fa"
        border: "#2563eb"
        text: "#1e293b"
      # ...
```

### Python Theme Manager

```python
# tools/pdf/config/theme_manager.py
from typing import Dict, Any
from pathlib import Path
import yaml
from pydantic import BaseModel, field_validator
from pydantic_extra_types.color import Color

class ThemeColorSet(BaseModel):
    """Validates a color set for a theme."""
    primary_bg: Color
    primary_text: Color
    primary_border: Color
    success: Color
    warning: Color
    error: Color
    info: Color
    
    @field_validator('primary_text', 'primary_border')
    def validate_contrast(cls, v, info):
        """Ensure sufficient contrast with background."""
        bg = info.data.get('primary_bg')
        if bg and not has_sufficient_contrast(bg, v):
            raise ValueError(f"Low contrast: {bg} on {v}")
        return v

class ThemeManager:
    """Manage themes and generate CSS from tokens."""
    
    def __init__(self, tokens_file: str):
        self.tokens_file = Path(tokens_file)
        self.tokens = self._load_tokens()
    
    def _load_tokens(self) -> Dict[str, Any]:
        """Load and validate design tokens."""
        with open(self.tokens_file) as f:
            tokens = yaml.safe_load(f)
        
        # Validate each theme
        for theme_name, theme_data in tokens.get('themes', {}).items():
            colors = theme_data.get('colors', {}).get('primary', {})
            ThemeColorSet(
                primary_bg=colors.get('background'),
                primary_text=colors.get('text'),
                primary_border=colors.get('border'),
                success=theme_data['colors'].get('success'),
                warning=theme_data['colors'].get('warning'),
                error=theme_data['colors'].get('error'),
                info=theme_data['colors'].get('info'),
            )
        
        return tokens
    
    def generate_css(self, theme_name: str) -> str:
        """Generate CSS for a theme."""
        theme = self.tokens['themes'].get(theme_name, {})
        if not theme:
            raise ValueError(f"Theme not found: {theme_name}")
        
        css_lines = [':root {']
        
        # Global tokens
        for token_name, token_value in self.tokens.get('global', {}).items():
            css_lines.append(f"  --{token_name}: {token_value};")
        
        # Theme-specific tokens
        colors = theme.get('colors', {})
        for color_category, color_values in colors.items():
            for color_name, color_value in color_values.items():
                var_name = f"--{color_category}-{color_name}".replace('_', '-')
                css_lines.append(f"  {var_name}: {color_value};")
        
        css_lines.append('}')
        return '\n'.join(css_lines)
    
    def generate_all_css(self, output_dir: str):
        """Generate CSS files for all themes."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for theme_name in self.tokens.get('themes', {}).keys():
            css = self.generate_css(theme_name)
            (output_path / f"{theme_name}.css").write_text(css)
            print(f"Generated: {theme_name}.css")
```

---

## 📊 What's Currently OK

✅ **Python Dependencies**: Recently updated (Playwright 1.45.0, PyPDF2 4.0.0, pytest 8.0.0)  
✅ **Mermaid Integration**: Working well (version 11, CSS variables)  
✅ **Playwright**: Current version, good rendering  
✅ **YAML parsing**: pyyaml adequate  
✅ **CLI**: Click is solid  
✅ **Web**: Flask 3.0 is current  

---

## 🚨 What's Missing/Outdated

❌ **System Dependency Management**
- Pandoc: System package (unversioned)
  - Recommendation: Document ≥3.1.0 requirement
  - Consider: Docker images to lock versions

❌ **Color/Theme System**
- Manual CSS files (5 copies of color definitions)
- No schema validation
- No accessibility checks
- No single source of truth

❌ **Design Token Standard**
- Not following industry patterns
- No separation of concerns
- No automation

❌ **CSS Preprocessing**
- No SCSS/Less
- No variable system beyond CSS custom properties
- Manual duplication across files

---

## 💡 Recommendations

### Phase 1 (Immediate - 2-3 hours)

1. **Create `design-tokens.yml`**
   - Central color definitions
   - All theme colors in one file
   - Document structure

2. **Add theme validation with Pydantic**
   ```python
   pip install pydantic-extra-types  # For Color validation
   ```
   - Validate colors are valid
   - Check contrast ratios
   - Warn on accessibility issues

3. **Create `ThemeManager` class**
   - Loads tokens.yml
   - Validates themes
   - Can generate CSS

### Phase 2 (Short-term - 4-6 hours)

4. **Add CSS generation**
   - Auto-generate CSS from tokens.yml
   - Replace manual CSS files
   - Add to pipeline as validation step

5. **Convert profiles.py to profiles.toml**
   - Data-driven configuration
   - Easier to maintain
   - Support dynamic profile loading

6. **Add accessibility validation**
   - Color contrast checking
   - WCAG AA/AAA compliance
   - Warnings during build

### Phase 3 (Medium-term - 8-12 hours)

7. **CSS preprocessing**
   - Add SCSS support (optional)
   - Or stick with CSS but better structure

8. **Theme editor/builder**
   - Web UI to create themes
   - Live preview
   - Export tokens.yml

9. **Design token documentation**
   - Auto-generate design token reference
   - Show color swatches
   - Link to usage

---

## 🎯 Expected Benefits

✅ **Single source of truth** for all colors and themes  
✅ **Automatic consistency** across all 5 themes  
✅ **Validation** (colors, contrast, accessibility)  
✅ **Easy to add themes** (edit YAML, not CSS)  
✅ **Reduced file size** (elimination of duplication)  
✅ **Version control** friendly (data-driven)  
✅ **CI/CD integration** (automatic validation)  
✅ **Non-developers** can update colors (YAML)  

---

## 📋 Summary

| Aspect | Current | Issue | Solution |
|--------|---------|-------|----------|
| **Color Management** | Manual CSS (5 files) | Duplication, errors | Design tokens YAML |
| **Validation** | None | Accessibility risks | Pydantic validators |
| **CSS Generation** | Hardcoded | Maintenance burden | Auto-generate from tokens |
| **Profile Config** | Python code | Hard to update | TOML configuration |
| **Contrast Checking** | Manual | Accessibility issues | Automated checking |
| **Theme Creation** | Difficult | Requires CSS knowledge | YAML-based |
| **Documentation** | Scattered | Hard to maintain | Auto-generated from tokens |

---

## ✅ Action Items

- [ ] Audit current theme usage (which themes used most?)
- [ ] Create design-tokens.yml with all colors
- [ ] Add Pydantic Color validation
- [ ] Create ThemeManager class
- [ ] Generate CSS from tokens as test
- [ ] Add validation step to pipeline
- [ ] Document design token structure
- [ ] Plan Phase 2 CSS generation replacement

---

**Next Step**: Create design-tokens.yml with current colors extracted from CSS files.
