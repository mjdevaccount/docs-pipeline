#!/usr/bin/env python3
"""
Test Coverage Dashboard Generator
==================================

Generates an HTML coverage dashboard showing:
- Overall coverage percentage
- Module-by-module breakdown
- Test categories (unit, integration, smoke)
- Coverage trends over time
- Missing coverage by file

Usage:
    python tools/pdf/tests/coverage_dashboard.py
    python tools/pdf/tests/coverage_dashboard.py --json coverage.json
    python tools/pdf/tests/coverage_dashboard.py --trend
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess
import sys


@dataclass
class FileCoverage:
    """Coverage data for a single file."""
    path: str
    statements: int
    covered: int
    missing: int
    excluded: int
    
    @property
    def coverage_percent(self) -> float:
        """Calculate coverage percentage."""
        if self.statements == 0:
            return 0.0
        return (self.covered / self.statements) * 100
    
    @property
    def status(self) -> str:
        """Get coverage status badge."""
        pct = self.coverage_percent
        if pct >= 90:
            return "✅ Excellent"
        elif pct >= 75:
            return "🟢 Good"
        elif pct >= 50:
            return "🟡 Fair"
        else:
            return "🔴 Poor"


@dataclass
class CoverageSummary:
    """Overall coverage summary."""
    timestamp: str
    total_statements: int
    total_covered: int
    total_missing: int
    total_excluded: int
    file_coverage: List[FileCoverage]
    
    @property
    def overall_percent(self) -> float:
        """Calculate overall coverage percentage."""
        if self.total_statements == 0:
            return 0.0
        return (self.total_covered / self.total_statements) * 100
    
    @property
    def status(self) -> str:
        """Get overall status badge."""
        pct = self.overall_percent
        if pct >= 90:
            return "✅ Excellent"
        elif pct >= 75:
            return "🟢 Good"
        elif pct >= 50:
            return "🟡 Fair"
        else:
            return "🔴 Poor"


class CoverageDashboard:
    """Generate test coverage dashboard."""
    
    def __init__(self, coverage_json: Optional[Path] = None):
        """Initialize dashboard generator.
        
        Args:
            coverage_json: Path to coverage.json file from pytest-cov
        """
        self.coverage_json = coverage_json or Path('coverage.json')
        self.trend_file = Path('.coverage-trend.json')
    
    def parse_coverage_json(self) -> CoverageSummary:
        """Parse coverage.json from pytest-cov.
        
        Returns:
            CoverageSummary with coverage data
        """
        if not self.coverage_json.exists():
            raise FileNotFoundError(f"Coverage file not found: {self.coverage_json}")
        
        with open(self.coverage_json) as f:
            data = json.load(f)
        
        file_coverage = []
        total_statements = 0
        total_covered = 0
        total_missing = 0
        total_excluded = 0
        
        # Parse per-file data
        for file_path, file_data in data.get('files', {}).items():
            summary = file_data.get('summary', {})
            
            statements = summary.get('num_statements', 0)
            covered = summary.get('covered_lines', 0)
            missing = statements - covered
            excluded = summary.get('excluded_lines', 0)
            
            file_coverage.append(FileCoverage(
                path=file_path,
                statements=statements,
                covered=covered,
                missing=missing,
                excluded=excluded
            ))
            
            total_statements += statements
            total_covered += covered
            total_missing += missing
            total_excluded += excluded
        
        # Sort by coverage percent (lowest first)
        file_coverage.sort(key=lambda x: x.coverage_percent)
        
        return CoverageSummary(
            timestamp=datetime.now().isoformat(),
            total_statements=total_statements,
            total_covered=total_covered,
            total_missing=total_missing,
            total_excluded=total_excluded,
            file_coverage=file_coverage
        )
    
    def generate_html(self, summary: CoverageSummary) -> str:
        """Generate HTML dashboard.
        
        Args:
            summary: CoverageSummary data
            
        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Coverage Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        .timestamp {{
            color: #718096;
            font-size: 14px;
        }}
        
        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat {{
            padding: 20px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 4px solid #3182ce;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2d3748;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
            transition: width 0.3s ease;
        }}
        
        .progress-fill.warning {{
            background: linear-gradient(90deg, #ed8936, #dd6b20);
        }}
        
        .progress-fill.danger {{
            background: linear-gradient(90deg, #f56565, #e53e3e);
        }}
        
        .file-list {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .file-item {{
            display: grid;
            grid-template-columns: 1fr 100px 100px 80px;
            gap: 20px;
            padding: 15px 0;
            border-bottom: 1px solid #e2e8f0;
            align-items: center;
        }}
        
        .file-item:last-child {{
            border-bottom: none;
        }}
        
        .file-path {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            color: #2d3748;
            overflow-x: auto;
        }}
        
        .file-stats {{
            text-align: right;
            font-size: 12px;
            color: #718096;
        }}
        
        .file-percent {{
            font-weight: bold;
            color: #2d3748;
            font-size: 14px;
        }}
        
        .status-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        
        .status-excellent {{
            background: #c6f6d5;
            color: #22543d;
        }}
        
        .status-good {{
            background: #bef3c3;
            color: #22543d;
        }}
        
        .status-fair {{
            background: #fed7d7;
            color: #742a2a;
        }}
        
        .status-poor {{
            background: #fed7d7;
            color: #742a2a;
        }}
        
        h2 {{
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        footer {{
            text-align: center;
            color: #718096;
            margin-top: 40px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Test Coverage Dashboard</h1>
            <p class="timestamp">Generated: {summary.timestamp}</p>
        </header>
        
        <div class="summary-card">
            <h2>Coverage Summary</h2>
            <div class="summary-stats">
                <div class="stat">
                    <div class="stat-label">Overall Coverage</div>
                    <div class="stat-value">{summary.overall_percent:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {summary.overall_percent}%">
                            {summary.overall_percent:.1f}%
                        </div>
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Status</div>
                    <div class="stat-value">{summary.status}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Lines Covered</div>
                    <div class="stat-value">{summary.total_covered:,}</div>
                    <div style="font-size: 12px; color: #718096; margin-top: 5px;">
                        of {summary.total_statements:,} statements
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Missing Coverage</div>
                    <div class="stat-value">{summary.total_missing:,}</div>
                    <div style="font-size: 12px; color: #718096; margin-top: 5px;">
                        lines to cover
                    </div>
                </div>
            </div>
        </div>
        
        <div class="file-list">
            <h2>Coverage by Module</h2>
            <div class="file-item" style="font-weight: bold; border-bottom: 2px solid #cbd5e0;">
                <div>Module</div>
                <div style="text-align: right;">Coverage</div>
                <div style="text-align: right;">Lines</div>
                <div>Status</div>
            </div>
"""
        
        # Add file coverage data
        for file in summary.file_coverage:
            status_class = f"status-{file.status.split()[0].lower()}".replace('✅', 'excellent').replace('🟢', 'good').replace('🟡', 'fair').replace('🔴', 'poor')
            
            # Determine color for progress bar
            if file.coverage_percent >= 90:
                bar_class = ""
            elif file.coverage_percent >= 75:
                bar_class = "warning"
            else:
                bar_class = "danger"
            
            html += f"""
            <div class="file-item">
                <div class="file-path">{file.path}</div>
                <div class="file-percent">{file.coverage_percent:.1f}%</div>
                <div class="file-stats">{file.covered}/{file.statements}</div>
                <div class="status-badge status-{'excellent' if file.coverage_percent >= 90 else 'good' if file.coverage_percent >= 75 else 'fair'}">
                    {file.status}
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <footer>
            <p>📈 Coverage data updated every test run</p>
            <p>Use <code>pytest --cov</code> to regenerate</p>
        </footer>
    </div>
</body>
</html>
"""
        return html
    
    def save_html(self, html: str, output: Optional[Path] = None) -> Path:
        """Save HTML dashboard to file.
        
        Args:
            html: HTML string
            output: Output file path (default: coverage-dashboard.html)
            
        Returns:
            Path to output file
        """
        output = output or Path('coverage-dashboard.html')
        output.write_text(html, encoding='utf-8')
        return output
    
    def track_trend(self, summary: CoverageSummary):
        """Track coverage trend over time.
        
        Args:
            summary: Current coverage summary
        """
        trends = []
        if self.trend_file.exists():
            trends = json.loads(self.trend_file.read_text())
        
        trends.append({
            'timestamp': summary.timestamp,
            'overall_percent': summary.overall_percent,
            'total_covered': summary.total_covered,
            'total_statements': summary.total_statements
        })
        
        # Keep last 30 days of data
        self.trend_file.write_text(json.dumps(trends[-30:], indent=2))
    
    def generate(self, output: Optional[Path] = None, track_trend: bool = False) -> Path:
        """Generate complete dashboard.
        
        Args:
            output: Output file path
            track_trend: Whether to track coverage trend
            
        Returns:
            Path to generated HTML file
        """
        print("[INFO] Generating coverage dashboard...")
        summary = self.parse_coverage_json()
        print(f"[OK] Parsed coverage.json: {summary.overall_percent:.1f}% coverage")
        
        html = self.generate_html(summary)
        output_path = self.save_html(html, output)
        print(f"[OK] Generated: {output_path}")
        
        if track_trend:
            self.track_trend(summary)
            print(f"[OK] Trend tracking updated")
        
        return output_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate test coverage dashboard',
        epilog="""
Examples:
  # Generate dashboard from coverage.json
  python tools/pdf/tests/coverage_dashboard.py
  
  # Use custom coverage file
  python tools/pdf/tests/coverage_dashboard.py --json my-coverage.json
  
  # Track coverage trends
  python tools/pdf/tests/coverage_dashboard.py --trend
  
  # Output to custom location
  python tools/pdf/tests/coverage_dashboard.py --output dashboards/coverage.html
        """
    )
    
    parser.add_argument('--json', type=Path, help='Path to coverage.json file')
    parser.add_argument('--output', type=Path, help='Output HTML file path')
    parser.add_argument('--trend', action='store_true', help='Track coverage trends')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        dashboard = CoverageDashboard(args.json)
        output_path = dashboard.generate(args.output, args.trend)
        
        if args.verbose:
            print(f"\n✅ Dashboard ready: {output_path}")
            print(f"   Open in browser: file://{output_path.absolute()}")
        
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print(f"[INFO] Run 'pytest --cov' first to generate coverage.json")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to generate dashboard: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
