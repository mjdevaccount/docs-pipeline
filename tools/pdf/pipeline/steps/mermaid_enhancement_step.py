"""
Mermaid 11 Enhancement Pipeline Step

Injects Mermaid 11 with CSS variable theming support.
Replaces old Mermaid initialization with new theme: 'base' configuration.
"""
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError


class MermaidEnhancementStep(PipelineStep):
    """
    Enhance HTML with Mermaid 11 CSS variable theming.
    
    - Removes old Mermaid script tag (unpkg with old theme)
    - Injects new Mermaid 11 script with theme: 'base' configuration
    - Enables dark-pro.css (and other profiles) to control diagram colors
    """
    
    def get_name(self) -> str:
        return "Mermaid Enhancement"
    
    def validate(self, context: PipelineContext) -> None:
        """Ensure HTML content is available"""
        if not context.html_content:
            raise PipelineError("No HTML content to enhance")
    
    def execute(self, context: PipelineContext) -> bool:
        """
        Transform Mermaid script in HTML.
        OLD: <script src="https://unpkg.com/mermaid/dist/mermaid.min.js"></script>
             <script>mermaid.initialize({startOnLoad:true,theme:'dark'})</script>
        
        NEW: <script type="module">import mermaid from '...'; mermaid.initialize({...})</script>
        """
        try:
            # Get profile for potential theming preferences
            profile_name = context.get_config('profile', 'dark-pro')
            verbose = context.verbose
            
            # Step 1: Remove old Mermaid script tag (unpkg)
            old_script_pattern = r'<script[^>]*src=["\']?https://unpkg\.org/mermaid[^>]*></script>'
            context.html_content = re.sub(old_script_pattern, '', context.html_content, flags=re.IGNORECASE)
            
            # Step 2: Remove old inline Mermaid initialization
            old_init_pattern = r'<script>\s*mermaid\.initialize\({[^}]*}\)\s*</script>'
            context.html_content = re.sub(old_init_pattern, '', context.html_content, flags=re.IGNORECASE)
            
            # Step 3: Check if new Mermaid script already exists (avoid double injection)
            if 'mermaid@11' in context.html_content:
                self.log(f"Mermaid 11 already present", context)
                return True
            
            # Step 4: Inject new Mermaid 11 script with CSS variable support
            mermaid_script = self._get_mermaid_11_script(profile_name)
            
            # Find </body> tag and inject before it
            if '</body>' in context.html_content:
                context.html_content = context.html_content.replace(
                    '</body>',
                    f'{mermaid_script}\n</body>'
                )
            else:
                # No </body> tag, append at end
                context.html_content += f'\n{mermaid_script}'
            
            self.log(
                f"Enhanced Mermaid for {profile_name} profile (CSS variable theming)",
                context
            )
            return True
            
        except PipelineError:
            raise
        except Exception as e:
            raise PipelineError(f"Mermaid enhancement failed: {e}")
    
    @staticmethod
    def _get_mermaid_11_script(profile_name: str = 'dark-pro') -> str:
        """
        Generate Mermaid 11 initialization script with CSS variable support.
        
        Uses theme: 'base' to tell Mermaid to read CSS custom properties from :root
        """
        script = '''    <script type="module">
        // Import Mermaid 11 as ES module
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        
        // Initialize with CSS-variable based theming
        mermaid.initialize({
            // Theme configuration
            startOnLoad: true,              // Auto-render .mermaid divs
            theme: 'base',                  // KEY: Use CSS custom properties
            themeVariables: {},             // Leave empty - CSS provides all colors
            
            // Security
            securityLevel: 'strict',        // Recommended for PDFs
            
            // Diagram-specific settings
            flowchart: {
                useMaxWidth: true,          // Responsive width
                padding: 20,                // Node padding
                htmlLabels: true,           // Better label rendering
                nodeSpacing: 50,            // Space between nodes
                rankSpacing: 50             // Space between ranks
            },
            sequence: {
                useMaxWidth: true,
                mirrorActors: true,         // Mirror actors on both sides
                actorMargin: 50
            },
            gantt: {
                useMaxWidth: true,
                fontSize: 12
            },
            class: {
                arrowMarkerAbsolute: true   // Better arrow rendering
            },
            state: {
                dividerMargin: 3,
                sizeUnit: 5
            },
            pie: {
                useMaxWidth: true,
                textPosition: 0.75
            },
            requirement: {
                useMaxWidth: true
            },
            git: {
                useMaxWidth: true
            }
        });
        
        // Trigger content loaded for Playwright (handles async HTML injection)
        mermaid.contentLoaded();
        
        // Optional: Debug logging for troubleshooting
        if (window.location.search.includes('debug')) {
            console.log('[Mermaid Config]', mermaid.config);
            const root = getComputedStyle(document.documentElement);
            console.log('[CSS Variables]', {
                primaryColor: root.getPropertyValue('--mermaid-primaryColor'),
                textColor: root.getPropertyValue('--mermaid-textColor'),
                lineColor: root.getPropertyValue('--mermaid-lineColor')
            });
        }
    </script>'''
        return script

