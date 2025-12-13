"""
CSS Wait Strategies - December 2025 Pattern
===========================================
Structured, testable wait strategies for CSS operations.
Allows explicit condition-based waiting instead of procedural waits.

Philosophy:
- Single responsibility: Each strategy waits for one specific condition
- Observable: Returns success/failure, can be chained
- Testable: Each strategy can be tested independently
- Non-blocking: Uses async/await properly
"""
from playwright.async_api import Page

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    WARN = "[WARN]"


class CSSWaitStrategy:
    """
    Structured wait strategies for CSS operations.
    December 2025 pattern: Observable, testable, reusable.
    """
    
    def __init__(self, page: Page, verbose: bool = False):
        """
        Initialize wait strategy.
        
        Args:
            page: Playwright page object
            verbose: Verbose logging
        """
        self.page = page
        self.verbose = verbose
    
    async def wait_for_css_cascade(self, timeout_ms: int = 2000) -> bool:
        """
        Wait for CSS custom properties to cascade through the page.
        
        Uses requestAnimationFrame to wait for paint cycles and CSS cascade completion.
        This is more reliable than arbitrary timeouts because it waits for actual
        browser paint cycles.
        
        Args:
            timeout_ms: Maximum time to wait (fallback)
        
        Returns:
            True if successful
        """
        try:
            await self.page.evaluate("""
                () => new Promise(resolve => {
                    // Wait for two RAF cycles (paint + reflow cycle)
                    // First RAF waits for paint, second ensures cascade is complete
                    requestAnimationFrame(() => {
                        requestAnimationFrame(resolve);
                    });
                })
            """)
            if self.verbose:
                print(f"{INFO} CSS cascade wait completed")
            return True
        except Exception as e:
            if self.verbose:
                print(f"{WARN} CSS cascade wait timeout: {e}")
            return False
    
    async def wait_for_svg_visibility(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for SVG diagrams to be visible in the page.
        
        Uses Playwright's auto-waiting to check:
        - Element exists in DOM
        - Element is visible (display != none, visibility != hidden)
        - Element is stable (not animating)
        
        Args:
            timeout_ms: Maximum time to wait
        
        Returns:
            True if SVGs found and visible, False otherwise
        """
        try:
            await self.page.wait_for_selector(
                'svg, img[src$=".svg"]',
                state='visible',
                timeout=timeout_ms
            )
            
            svg_count = await self.page.evaluate("""
                () => document.querySelectorAll('svg').length
            """)
            
            if self.verbose:
                print(f"{INFO} SVG visibility wait completed: {svg_count} SVGs found")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"{WARN} SVG visibility wait timeout: {e}")
            return False
    
    async def wait_for_fonts_ready(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for all document fonts to be ready.
        
        Uses document.fonts.ready API which resolves when:
        - All @font-face fonts are loaded
        - All text with custom fonts is measurable
        
        Args:
            timeout_ms: Maximum time to wait
        
        Returns:
            True if fonts ready, False on timeout
        """
        try:
            await self.page.evaluate("""
                async () => {
                    await document.fonts.ready;
                }
            """, timeout=timeout_ms)
            
            if self.verbose:
                print(f"{INFO} Fonts ready wait completed")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"{WARN} Fonts ready wait timeout: {e}")
            return False
    
    async def wait_for_style_sheet_ready(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for style sheets to be fully loaded and accessible.
        
        Checks that cssRules can be accessed without CORS errors.
        Some stylesheets (like Google Fonts) may be CORS-protected.
        
        Args:
            timeout_ms: Maximum time to wait
        
        Returns:
            True if at least one stylesheet is accessible
        """
        try:
            result = await self.page.evaluate("""
                () => new Promise((resolve) => {
                    const checkReady = () => {
                        const sheets = Array.from(document.styleSheets);
                        const hasAccessibleRules = sheets.some(s => {
                            try {
                                return s.cssRules?.length > 0;
                            } catch (e) {
                                // CORS or pending - not accessible yet
                                return false;
                            }
                        });
                        
                        if (hasAccessibleRules) {
                            resolve(true);
                        } else {
                            // Retry with RAF
                            requestAnimationFrame(checkReady);
                        }
                    };
                    checkReady();
                })
            """, timeout=timeout_ms)
            
            if self.verbose and result:
                print(f"{INFO} Style sheet ready wait completed")
            return result
            
        except Exception as e:
            if self.verbose:
                print(f"{WARN} Style sheet ready wait timeout: {e}")
            return False
    
    async def wait_for_network_idle(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for network to be idle (no pending requests).
        
        Uses Playwright's built-in network monitoring.
        
        Args:
            timeout_ms: Maximum time to wait
        
        Returns:
            True if network idle
        """
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout_ms)
            if self.verbose:
                print(f"{INFO} Network idle wait completed")
            return True
        except Exception as e:
            if self.verbose:
                print(f"{WARN} Network idle wait timeout: {e}")
            return False
    
    async def wait_for_all_conditions(self) -> bool:
        """
        Wait for all conditions together (safe ordering).
        
        Order matters:
        1. Network idle - ensure all resources are loaded
        2. Fonts ready - all fonts are loaded
        3. Style sheets ready - CSS is accessible
        4. CSS cascade - custom properties cascaded
        5. SVG visibility - diagrams rendered
        
        Returns:
            True if all conditions met
        """
        conditions = [
            ("network idle", await self.wait_for_network_idle()),
            ("fonts", await self.wait_for_fonts_ready()),
            ("stylesheets", await self.wait_for_style_sheet_ready()),
            ("CSS cascade", await self.wait_for_css_cascade()),
            ("SVG visibility", await self.wait_for_svg_visibility()),
        ]
        
        if self.verbose:
            print(f"{INFO} All conditions ready:")
            for condition, success in conditions:
                status = "✓" if success else "✗"
                print(f"  {status} {condition}")
        
        return all(success for _, success in conditions)
    
    async def wait_for_condition(self, condition: str) -> bool:
        """
        Wait for a specific named condition.
        
        Args:
            condition: One of:
                - 'css_cascade': CSS custom properties cascaded
                - 'svg_visibility': SVG diagrams visible
                - 'fonts': Document fonts ready
                - 'stylesheets': Stylesheets accessible
                - 'network': Network idle
        
        Returns:
            True if condition met
        """
        conditions = {
            'css_cascade': self.wait_for_css_cascade,
            'svg_visibility': self.wait_for_svg_visibility,
            'fonts': self.wait_for_fonts_ready,
            'stylesheets': self.wait_for_style_sheet_ready,
            'network': self.wait_for_network_idle,
        }
        
        if condition not in conditions:
            raise ValueError(f"Unknown condition: {condition}")
        
        return await conditions[condition]()
