"""
Mermaid 11 Enhancement Pipeline Step

Injects Mermaid 11 with complete CSS variable theming support.
Replaces old Mermaid initialization with new theme: 'base' configuration.
Dynamically maps CSS variables to Mermaid themeVariables for full color control.
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
    - Enables dark-pro.css (and other profiles) to control ALL diagram colors
    - Dynamically reads CSS variables from :root at runtime
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
                f"Enhanced Mermaid for {profile_name} profile (CSS variable theming + diagram settings)",
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
        Generate Mermaid 11 initialization script with complete CSS variable support.
        
        Uses theme: 'base' to tell Mermaid to read CSS custom properties from :root.
        Dynamically maps all CSS variables to Mermaid themeVariables at runtime.
        """
        script = '''    <script type="module">
        // Import Mermaid 11 as ES module
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        
        /**
         * Read CSS custom properties from :root and map to Mermaid theme variables.
         * This enables dark-pro.css (and other profiles) to control ALL diagram colors.
         */
        const getCSSVariables = () => {
            const root = getComputedStyle(document.documentElement);
            const getVar = (name, fallback = '') => {
                const val = root.getPropertyValue(name).trim();
                return val || fallback;
            };
            
            return {
                // Primary colors
                primaryColor: getVar('--mermaid-primaryColor', '#0f172a'),
                primaryTextColor: getVar('--mermaid-primaryTextColor', '#f3f4f6'),
                primaryBorderColor: getVar('--mermaid-primaryBorderColor', '#60a5fa'),
                lineColor: getVar('--mermaid-lineColor', '#60a5fa'),
                secondBkgColor: getVar('--mermaid-secondBkgColor', '#1e293b'),
                tertiaryColor: getVar('--mermaid-tertiaryColor', '#334155'),
                
                // Text styling
                tertiaryTextColor: getVar('--mermaid-tertiaryTextColor', '#f3f4f6'),
                textColor: getVar('--mermaid-textColor', '#f3f4f6'),
                titleColor: getVar('--mermaid-titleColor', '#93c5fd'),
                labelTextColor: getVar('--mermaid-labelTextColor', '#f3f4f6'),
                
                // Borders
                borderColor: getVar('--mermaid-borderColor', '#60a5fa'),
                tertiaryBorderColor: getVar('--mermaid-tertiaryBorderColor', '#334155'),
                noteBkgColor: getVar('--mermaid-noteBkgColor', '#164e63'),
                noteBorderColor: getVar('--mermaid-noteBorderColor', '#06b6d4'),
                noteTextColor: getVar('--mermaid-noteTextColor', '#cffafe'),
                
                // Graph styling
                gridColor: getVar('--mermaid-gridColor', '#334155'),
                markerAccent: getVar('--mermaid-markerAccent', '#60a5fa'),
                
                // Flowchart specific
                flowchartBkgColor: getVar('--mermaid-flowchartBkgColor', '#1e293b'),
                flowchartBorderColor: getVar('--mermaid-flowchartBorderColor', '#60a5fa'),
                nodeTextColor: getVar('--mermaid-nodeTextColor', '#f3f4f6'),
                
                // Sequence diagram
                actorBkg: getVar('--mermaid-actorBkg', '#0f172a'),
                actorBorder: getVar('--mermaid-actorBorder', '#60a5fa'),
                actorTextColor: getVar('--mermaid-actorTextColor', '#f3f4f6'),
                actorLineColor: getVar('--mermaid-actorLineColor', '#60a5fa'),
                messageLabelBackground: getVar('--mermaid-messageLabelBackground', '#1e293b'),
                labelBoxBkgColor: getVar('--mermaid-labelBoxBkgColor', '#1e293b'),
                labelBoxBorderColor: getVar('--mermaid-labelBoxBorderColor', '#60a5fa'),
                
                // State diagram
                stateBkg: getVar('--mermaid-stateBkg', '#1e293b'),
                stateBorder: getVar('--mermaid-stateBorder', '#60a5fa'),
                stateTextColor: getVar('--mermaid-stateTextColor', '#f3f4f6'),
                transitionTextColor: getVar('--mermaid-transitionTextColor', '#d1d5db'),
                
                // Class diagram
                classifierBkgColor: getVar('--mermaid-classifierBkgColor', '#0f172a'),
                classifierBorder: getVar('--mermaid-classifierBorder', '#60a5fa'),
                classTextColor: getVar('--mermaid-classTextColor', '#f3f4f6'),
                
                // Entity relationship
                entityBkg: getVar('--mermaid-entityBkg', '#1e293b'),
                entityBorder: getVar('--mermaid-entityBorder', '#60a5fa'),
                entityTextColor: getVar('--mermaid-entityTextColor', '#f3f4f6'),
                relationshipTextColor: getVar('--mermaid-relationshipTextColor', '#d1d5db'),
                
                // Gantt chart
                taskBkg: getVar('--mermaid-taskBkg', '#60a5fa'),
                taskBorder: getVar('--mermaid-taskBorder', '#3b82f6'),
                taskTextColor: getVar('--mermaid-taskTextColor', '#0f172a'),
                doneTaskBkg: getVar('--mermaid-doneTaskBkg', '#10b981'),
                doneTaskBorder: getVar('--mermaid-doneTaskBorder', '#059669'),
                crit: getVar('--mermaid-crit', '#ef4444'),
                critBorder: getVar('--mermaid-critBorder', '#dc2626'),
                critTextColor: getVar('--mermaid-critTextColor', '#0f172a'),
                todayLineColor: getVar('--mermaid-todayLineColor', '#f59e0b'),
                sectionBkgColor: getVar('--mermaid-sectionBkgColor', '#1e293b'),
                sectionBkgColor2: getVar('--mermaid-sectionBkgColor2', '#334155'),
                
                // Pie chart
                pieStrokeColor: getVar('--mermaid-pieStrokeColor', '#fff'),
                
                // Git graph
                gitInv: getVar('--mermaid-gitInv', '#0f172a'),
                gitBkg: getVar('--mermaid-gitBkg', '#1e293b'),
                gitBorder: getVar('--mermaid-gitBorder', '#60a5fa'),
                gitLabel: getVar('--mermaid-gitLabel', '#f3f4f6'),
                commitTextColor: getVar('--mermaid-commitTextColor', '#0f172a'),
                branchTextColor: getVar('--mermaid-branchTextColor', '#f3f4f6'),
                tagTextColor: getVar('--mermaid-tagTextColor', '#f3f4f6')
            };
        };
        
        // Initialize with CSS-variable based theming
        mermaid.initialize({
            // Theme configuration - KEY: 'base' reads CSS custom properties
            startOnLoad: true,                  // Auto-render .mermaid divs
            theme: 'base',                      // Use CSS custom properties
            themeVariables: getCSSVariables(),  // Dynamically read CSS variables
            
            // Security
            securityLevel: 'strict',            // Recommended for PDFs
            
            // Diagram-specific settings for better rendering
            flowchart: {
                useMaxWidth: true,              // Responsive width
                htmlLabels: true,               // HTML labels (respects CSS)
                padding: 20,                    // Node padding
                nodeSpacing: 50,                // Space between nodes
                rankSpacing: 50,                // Space between ranks
                arrowMarkerAbsolute: true       // Better arrow rendering
            },
            
            sequence: {
                useMaxWidth: true,
                mirrorActors: true,             // Mirror actors on both sides
                actorMargin: 50,                // Actor spacing
                messageAlign: 'center'
            },
            
            gantt: {
                useMaxWidth: true,
                fontSize: 12,                   // Readable task text
                numberSectionStyles: 2          // Color alternating sections
            },
            
            class: {
                arrowMarkerAbsolute: true,      // Better arrow rendering
                htmlLabels: true
            },
            
            state: {
                dividerMargin: 3,
                sizeUnit: 5,
                htmlLabels: true
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
            },
            
            er: {
                useMaxWidth: true
            }
        });
        
        // Trigger content loaded for Playwright (handles async HTML injection)
        mermaid.contentLoaded();
        
        // Optional: Debug logging for troubleshooting
        if (window.location.search.includes('debug')) {
            console.log('[Mermaid Config] Theme variables loaded:', getCSSVariables());
            console.log('[Mermaid Initialized] Ready to render diagrams');
        }
    </script>'''
        return script
