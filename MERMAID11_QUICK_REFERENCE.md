# Mermaid 11 Integration - Quick Reference Card

## 🎯 The One-Line Fix

```html
<!-- Change this: -->
<script src="https://unpkg.com/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true,theme:'dark'})</script>

<!-- To this: -->
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({startOnLoad:true, theme:'base', themeVariables:{}, securityLevel:'strict'});
  mermaid.contentLoaded();
</script>
```

---

## 📊 Mermaid 11 CSS Variables (Already in dark-pro.css)

| Variable | Value | Purpose |
|----------|-------|----------|
| `--mermaid-primaryColor` | `#0f172a` | Node background |
| `--mermaid-primaryTextColor` | `#f3f4f6` | Node text (bright) |
| `--mermaid-primaryBorderColor` | `#60a5fa` | Node border |
| `--mermaid-lineColor` | `#60a5fa` | Connection lines |
| `--mermaid-textColor` | `#f3f4f6` | Global text |
| `--mermaid-noteBkgColor` | `#1e3a4c` | Note background |
| `--mermaid-mainBkg` | `#0f172a` | Diagram bg |
| ... | ... | (80+ total variables) |

---

## ✅ Verification Checklist

### In Browser Console:
```javascript
// Check theme is 'base'
console.log(mermaid.config.theme); // Should be: 'base'

// Check CSS variables loaded
let root = getComputedStyle(document.documentElement);
console.log(root.getPropertyValue('--mermaid-primaryColor')); // Should be: #0f172a
console.log(root.getPropertyValue('--mermaid-textColor')); // Should be: #f3f4f6
```

### In PDF:
```
✅ Node backgrounds: Very dark (#0f172a)
✅ Node text: Bright and readable (#f3f4f6)
✅ Connection lines: Blue (#60a5fa)
✅ NOT washed-out gray/blue Mermaid defaults
```

---

## 🔧 CSS Requirements (Already Implemented)

```css
/* dark-pro.css must have: */
:root {
    --mermaid-primaryColor: #0f172a;
    --mermaid-primaryTextColor: #f3f4f6;
    --mermaid-lineColor: #60a5fa;
    /* ... 80+ variables ... */
}

/* SVG text fallback: */
svg text {
    fill: var(--color-text-primary) !important;
}

/* Print preservation: */
svg {
    print-color-adjust: exact !important;
}
```

**Status**: ✅ Already done in dark-pro.css

---

## 🎬 Playwright PDF Options

```python
await page.pdf({
    'path': str(pdf_file),
    'printBackground': True,      # ← Required for colors
    'preferCSSPageSize': True,     # ← Required for CSS @page
    'pdf_version': '2.0'           # ← Modern PDF
})
```

---

## 📄 File Reference

| File | Action | Status |
|------|--------|--------|
| `tools/pdf/styles/dark-pro.css` | Already has mermaid variables | ✅ DONE |
| Your HTML template | Update Mermaid script | ⏳ YOUR ACTION |
| `playwright_renderer.py` | Check PDF options | ⏳ VERIFY |
| `mermaid_themes.py` | Optional: delete | 🗑️ CAN DELETE |

---

## 🚀 Timeline

**5 min**: Update HTML template  
**2 min**: Test with sample diagram  
**Total**: ~7 minutes to fix

---

## ❄️ Troubleshooting (If colors still wrong)

| Issue | Check |
|-------|-------|
| CSS variables not loading | Is dark-pro.css linked in `<head>`? |
| Mermaid not reading CSS | Is `theme: 'base'` set? |
| Text still washed out | Is `printBackground: True` in PDF options? |
| Old colors still showing | Clear browser cache, reload |

---

## 🔗 Related Documentation

- **MERMAID_DARK_PRO_INTEGRATION.md** - Full explanation
- **IMPLEMENTATION_CHECKLIST_MERMAID11.md** - Step-by-step guide
- **HTML_TEMPLATE_MERMAID11.html** - Working template
- **MERMAID11_INTEGRATION_SUMMARY.md** - Executive summary

---

## 📝 Key Concepts

**What's `theme: 'base'`?**
- Tells Mermaid to use CSS custom properties instead of built-in theme
- Enables dark-pro.css to control diagram colors
- Required for CSS variable theming

**Why `themeVariables: {}` empty?**
- If you pass colors here, they override CSS
- CSS should be single source of truth
- Leave empty to let CSS drive colors

**Why ES module import?**
- Modern, tree-shakeable approach
- Mermaid 11+ native support
- Better performance than script tag

---

## 🎈 Result

**Before**:
- ❌ Washed-out diagram colors
- ❌ Default gray/blue theme
- ❌ Poor contrast

**After**:
- ✅ Perfect dark-pro colors
- ✅ Bright, readable text
- ✅ Consistent with document

---

**Time to implement**: 5-10 minutes  
**Complexity**: LOW  
**Impact**: HIGH  
**Status**: READY TO DEPLOY
