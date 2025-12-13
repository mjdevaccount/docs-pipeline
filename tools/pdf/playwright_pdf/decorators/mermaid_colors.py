"""
Mermaid Color Replacement Decorator
====================================
Replaces Mermaid classDef placeholder colors with CSS variables from loaded theme.

This must run AFTER CSS injection (inject_custom_css) so CSS variables are available.
"""
from playwright.async_api import Page

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"


async def apply_mermaid_colors(page: Page, verbose: bool = False) -> None:
    """
    Replace Mermaid classDef colors with CSS variables.
    
    This reads CSS variables from the loaded theme and applies them to all
    Mermaid classDef rules in SVG diagrams.
    
    The color replacement handles:
    - classDef config fill/stroke
    - classDef core fill/stroke
    - classDef stream fill/stroke
    - classDef storage fill/stroke
    - classDef output fill/stroke
    - classDef topic fill/stroke
    - classDef highlight fill/stroke
    
    Args:
        page: Playwright page object
        verbose: Verbose logging
    """
    # JavaScript to replace Mermaid classDef colors with CSS variables
    await page.evaluate("""
        () => {
            // Get CSS variable from root element
            const getVar = (varName) => {
                const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
                if (!value) return null;
                // Handle colors with or without #
                return value.startsWith('#') ? value : `#${value}`;
            };
            
            // Map of CSS variable names to placeholder values
            // These are the placeholders defined in the design tokens
            const colorMap = {
                // Config class
                '--mermaid-config-fill': '#164e63',      // Default fallback (dark cyan)
                '--mermaid-config-stroke': '#06b6d4',    // Default fallback (cyan)
                
                // Core class
                '--mermaid-core-fill': '#0f172a',        // Default fallback (very dark blue)
                '--mermaid-core-stroke': '#60a5fa',      // Default fallback (blue)
                
                // Stream class
                '--mermaid-stream-fill': '#1e293b',      // Default fallback (dark slate)
                '--mermaid-stream-stroke': '#60a5fa',    // Default fallback (blue)
                
                // Storage class
                '--mermaid-storage-fill': '#334155',     // Default fallback (medium slate)
                '--mermaid-storage-stroke': '#60a5fa',   // Default fallback (blue)
                
                // Output class
                '--mermaid-output-fill': '#1e293b',      // Default fallback (dark slate)
                '--mermaid-output-stroke': '#60a5fa',    // Default fallback (blue)
                
                // Topic class
                '--mermaid-topic-fill': '#334155',       // Default fallback (medium slate)
                '--mermaid-topic-stroke': '#60a5fa',     // Default fallback (blue)
                
                // Highlight class
                '--mermaid-highlight-fill': '#0f172a',   // Default fallback (very dark blue)
                '--mermaid-highlight-stroke': '#60a5fa', // Default fallback (blue)
            };
            
            // Build actual color map from CSS variables
            const actualColors = {};
            Object.entries(colorMap).forEach(([varName, fallback]) => {
                const value = getVar(varName);
                actualColors[varName] = value || fallback;
            });
            
            // Find all SVG diagrams (Mermaid renders as SVG)
            const svgs = document.querySelectorAll('svg');
            
            svgs.forEach(svg => {
                // Look for style elements or style attributes with classDef
                // Mermaid injects a <style> tag with classDef definitions
                let styleElement = svg.querySelector('style');
                
                if (styleElement && styleElement.textContent) {
                    let styleContent = styleElement.textContent;
                    let modified = false;
                    
                    // Replace color references in classDef statements
                    // Pattern: .classNameN { fill: #xxxxxx; stroke: #xxxxxx; }
                    // We look for the hex colors and replace with CSS variables
                    
                    // For each class, replace fill and stroke
                    const classes = ['config', 'core', 'stream', 'storage', 'output', 'topic', 'highlight'];
                    
                    classes.forEach(className => {
                        const fillVar = `--mermaid-${className}-fill`;
                        const strokeVar = `--mermaid-${className}-stroke`;
                        const fillColor = actualColors[fillVar];
                        const strokeColor = actualColors[strokeVar];
                        
                        if (fillColor && strokeColor) {
                            // Look for .classNameN or .className style rules
                            // Mermaid often generates class1, class2, etc. but we look for the specific class
                            const classRegex = new RegExp(`(\\.${className}\\d*)\\s*\\{([^}]*)\\}`, 'g');
                            
                            styleContent = styleContent.replace(classRegex, (match, selector, styles) => {
                                let newStyles = styles;
                                
                                // Replace fill color
                                // Handle: fill: #xxxxxx or fill:#xxxxxx
                                newStyles = newStyles.replace(/fill\s*:\s*#[0-9a-fA-F]{6}/gi, `fill: ${fillColor}`);
                                
                                // Replace stroke color
                                // Handle: stroke: #xxxxxx or stroke:#xxxxxx
                                newStyles = newStyles.replace(/stroke\s*:\s*#[0-9a-fA-F]{6}/gi, `stroke: ${strokeColor}`);
                                
                                if (newStyles !== styles) {
                                    modified = true;
                                }
                                
                                return `${selector} {${newStyles}}`;
                            });
                        }
                    });
                    
                    // Update the style element if modified
                    if (modified) {
                        styleElement.textContent = styleContent;
                    }
                }
            });
        }
    """)
    
    if verbose:
        print(f"{INFO} Applied Mermaid classDef colors from CSS variables")
