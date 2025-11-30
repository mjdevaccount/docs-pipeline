#!/usr/bin/env python3
"""
Structurizr CLI Helper Script
=============================

Python wrapper for Structurizr CLI Docker commands with enhanced features:
- Configuration file support
- Batch operations
- Progress tracking
- Error handling
- Watch mode for live updates
- Validation before export

Usage:
    python structurizr.py export --workspace docs/Architecture.dsl --format mermaid --output docs/
    python structurizr.py validate --workspace docs/Architecture.dsl
    python structurizr.py serve --workspace docs/Architecture.dsl
    python structurizr.py --config structurizr-config.json
    python structurizr.py export --workspace docs/Architecture.dsl --watch
"""

import argparse
import json
import subprocess
import sys
import os
import threading
import time
from pathlib import Path

# Optional: Watch mode support
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create stub class for type checking
    class FileSystemEventHandler:
        pass
    Observer = None

# Try to import colorama for colored output
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = Fore.GREEN + "[OK]" + Style.RESET_ALL
    WARN = Fore.YELLOW + "[WARN]" + Style.RESET_ALL
    ERR = Fore.RED + "[ERROR]" + Style.RESET_ALL
    INFO = Fore.CYAN + "[INFO]" + Style.RESET_ALL
except ImportError:
    OK = "[OK]"
    WARN = "[WARN]"
    ERR = "[ERROR]"
    INFO = "[INFO]"

# Version
__version__ = "2.0.0"

# Default configuration
DEFAULT_DOCKER_IMAGE = "structurizr/cli:latest"
DEFAULT_LITE_IMAGE = "structurizr/lite:latest"
DEFAULT_SERVE_PORT = 8080


def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"{OK} Docker found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{ERR} Docker is not installed or not in PATH")
        print("Please install Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
    
    try:
        subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            check=True
        )
        print(f"{OK} Docker is running")
    except subprocess.CalledProcessError:
        print(f"{ERR} Docker is not running")
        print("Please start Docker Desktop")
        return False
    
    return True


def check_structurizr_image(image=DEFAULT_DOCKER_IMAGE):
    """Check if Structurizr CLI image is available"""
    try:
        result = subprocess.run(
            ["docker", "images", image.split(":")[0]],
            capture_output=True,
            text=True,
            check=True
        )
        if image.split(":")[0] in result.stdout:
            print(f"{OK} Structurizr CLI image found")
            return True
        else:
            print(f"{WARN} Structurizr CLI image not found")
            return False
    except subprocess.CalledProcessError:
        return False


def pull_image(image=DEFAULT_DOCKER_IMAGE):
    """Pull Structurizr CLI Docker image"""
    print(f"{INFO} Pulling Structurizr CLI image...")
    try:
        subprocess.run(
            ["docker", "pull", image],
            check=True
        )
        print(f"{OK} Image pulled successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"{ERR} Failed to pull image")
        return False


def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{ERR} Config file not found: {config_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"{ERR} Invalid JSON in config file: {e}")
        return None


def validate_config(config):
    """Validate configuration file structure"""
    required_fields = ['workspace']
    optional_fields = ['formats', 'output_dir', 'docker_image', 'options', 'serve']
    
    errors = []
    warnings = []
    
    # Check required fields
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Check workspace file exists
    if 'workspace' in config:
        if not os.path.exists(config['workspace']):
            errors.append(f"Workspace file not found: {config['workspace']}")
    
    # Validate formats
    if 'formats' in config:
        valid_formats = ['mermaid', 'plantuml', 'png', 'svg', 'html', 'json', 'ilograph', 'websequencediagrams', 'graphviz']
        for fmt in config['formats']:
            if fmt not in valid_formats:
                warnings.append(f"Unknown format: {fmt} (valid: {', '.join(valid_formats)})")
    
    # Print results
    if errors:
        print(f"{ERR} Config validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print(f"{WARN} Config validation warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    return True


def generate_config_template(output_file='structurizr-config.json'):
    """Generate a template configuration file"""
    template = {
        "version": "1.0",
        "workspace": "docs/architecture/workspace.dsl",
        "formats": ["mermaid", "plantuml", "svg"],
        "output_dir": "docs/diagrams",
        "docker_image": "structurizr/cli:latest",
        "options": {
            "validate_before_export": True,
            "cleanup_old_exports": False,
            "parallel_export": False
        },
        "serve": {
            "port": 8080,
            "auto_open": False
        }
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        print(f"{OK} Generated config template: {output_file}")
        return True
    except IOError as e:
        print(f"{ERR} Failed to write config: {e}")
        return False


def normalize_path_for_docker(path):
    """Convert Windows path to Docker-compatible format"""
    path = os.path.abspath(path)
    if sys.platform == 'win32':
        # Convert Windows path to Unix-style for Docker
        path = path.replace('\\', '/')
        # Handle Windows drive letters (C:\ -> /c/)
        if ':' in path:
            drive, rest = path.split(':', 1)
            path = f'/{drive.lower()}{rest}'
    return path


def extract_workspace_from_args(args):
    """Extract workspace file path from command arguments"""
    for i, arg in enumerate(args):
        if arg == '--workspace' and i + 1 < len(args):
            return args[i + 1]
    return None


def show_progress(stop_event, message="Processing"):
    """Show animated progress indicator"""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        print(f'\r{INFO} {message} {spinner[idx % len(spinner)]}', end='', flush=True)
        idx += 1
        time.sleep(0.1)
    print('\r' + ' ' * 80 + '\r', end='', flush=True)


def run_docker_command(command, args, workspace_dir=None, docker_image=None, serve=False, show_progress_indicator=True, verbose=False, dry_run=False):
    """Run Structurizr CLI command via Docker"""
    
    # Extract workspace file path from args if provided
    workspace_file = extract_workspace_from_args(args)
    
    # Determine workspace directory
    if workspace_file:
        # Use parent directory of workspace file
        workspace_file_abs = os.path.abspath(workspace_file)
        workspace_dir_from_file = os.path.dirname(workspace_file_abs)
        if workspace_dir is None:
            workspace_dir = workspace_dir_from_file if workspace_dir_from_file else os.getcwd()
        
        # Update args to use relative path inside container
        workspace_basename = os.path.basename(workspace_file)
        for i, arg in enumerate(args):
            if arg == '--workspace':
                if serve:
                    # Lite uses environment variable, not path in args
                    pass
                else:
                    # CLI uses relative path from workspace mount
                    args[i + 1] = workspace_basename
    elif workspace_dir is None:
        workspace_dir = os.getcwd()
    
    # Create output directory if it doesn't exist (for export command)
    if command == 'export':
        for i, arg in enumerate(args):
            if arg == '--output' and i + 1 < len(args):
                output_path = args[i + 1]
                # If relative, make it relative to workspace_dir
                if not os.path.isabs(output_path):
                    full_output_path = os.path.join(workspace_dir, output_path)
                else:
                    full_output_path = output_path
                
                try:
                    os.makedirs(full_output_path, exist_ok=True)
                    if verbose:
                        print(f"{INFO} Output directory: {full_output_path}")
                except OSError as e:
                    print(f"{ERR} Failed to create output directory: {e}")
                    return False
                break
    
    # Normalize path for Docker (handle Windows paths)
    workspace_dir_normalized = normalize_path_for_docker(workspace_dir)
    
    if docker_image is None:
        docker_image = DEFAULT_LITE_IMAGE if serve else DEFAULT_DOCKER_IMAGE
    
    # Ensure docker_image has version tag
    if docker_image and ':' not in docker_image:
        docker_image = f"{docker_image}:latest"
        if verbose:
            print(f"{WARN} No version tag specified, using {docker_image}")
    
    # Build Docker command
    docker_cmd = ["docker", "run", "--rm"]
    
    if serve:
        docker_cmd.extend(["-it", "-p", f"{DEFAULT_SERVE_PORT}:8080"])
        
        # Structurizr Lite expects workspace at /usr/local/structurizr
        docker_cmd.extend(["-v", f"{workspace_dir_normalized}:/usr/local/structurizr"])
        
        # Set workspace filename via environment variable if provided
        if workspace_file:
            workspace_name = os.path.basename(workspace_file)
            # Remove extension for Lite
            workspace_name = workspace_name.replace('.dsl', '').replace('.json', '')
            docker_cmd.extend(["-e", f"STRUCTURIZR_WORKSPACE_FILENAME={workspace_name}"])
        
        docker_cmd.append(docker_image)
        # Lite doesn't use CLI args - it's a web server
        # Remove --workspace from args if present
        filtered_args = []
        skip_next = False
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            if arg == '--workspace':
                skip_next = True
                continue
            filtered_args.append(arg)
        args = filtered_args
    else:
        # Structurizr CLI expects workspace at /workspace
        docker_cmd.extend(["-v", f"{workspace_dir_normalized}:/workspace"])
        docker_cmd.extend(["-w", "/workspace"])
        docker_cmd.append(docker_image)
        docker_cmd.append(command)
    
    docker_cmd.extend(args)
    
    # Verbose output
    if verbose:
        print(f"{INFO} Docker command: {' '.join(docker_cmd)}")
        print(f"{INFO} Workspace dir: {workspace_dir_normalized}")
        print(f"{INFO} Arguments: {args}")
    
    # Dry run mode
    if dry_run:
        print(f"{INFO} DRY RUN - Would execute:")
        print(f"  Command: {' '.join(docker_cmd)}")
        print(f"  Workspace: {workspace_dir_normalized}")
        return True
    
    # Execute
    try:
        if serve or not show_progress_indicator:
            # Interactive or no progress needed
            subprocess.run(docker_cmd, check=True)
        else:
            # Show progress for non-interactive commands
            stop_event = threading.Event()
            progress_thread = threading.Thread(
                target=show_progress,
                args=(stop_event, f"Running {command}")
            )
            progress_thread.start()
            
            try:
                result = subprocess.run(
                    docker_cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
                stop_event.set()
                progress_thread.join()
                
                if result.stdout:
                    print(result.stdout)
                
                return True
            except subprocess.CalledProcessError as e:
                stop_event.set()
                progress_thread.join()
                print(f"{ERR} Command failed with exit code {e.returncode}")
                if e.stderr:
                    print(e.stderr)
                if e.stdout:
                    print(e.stdout)
                return False
        
        return True
    except KeyboardInterrupt:
        if show_progress_indicator and not serve:
            stop_event.set()
            progress_thread.join()
        print(f"\n{WARN} Interrupted by user")
        return False


def validate_workspace(workspace_path, verbose=False):
    """Validate workspace before export"""
    if not workspace_path:
        print(f"{ERR} No workspace file specified")
        return False
    
    if not os.path.exists(workspace_path):
        print(f"{ERR} Workspace file not found: {workspace_path}")
        # Helpful suggestion
        workspace_dir = os.path.dirname(workspace_path) or '.'
        if os.path.exists(workspace_dir):
            try:
                similar_files = [f for f in os.listdir(workspace_dir) if f.endswith(('.dsl', '.json'))]
                if similar_files:
                    print(f"{INFO} Did you mean one of these?")
                    for f in similar_files[:5]:
                        print(f"    {os.path.join(workspace_dir, f)}")
            except OSError:
                pass
        return False
    
    print(f"{INFO} Validating workspace...")
    cmd_args = ['--workspace', workspace_path]
    
    if run_docker_command('validate', cmd_args, show_progress_indicator=False, verbose=verbose):
        print(f"{OK} Workspace is valid")
        return True
    else:
        print(f"{ERR} Workspace validation failed")
        return False


def batch_export(config, verbose=False, dry_run=False):
    """Export to multiple formats with error recovery"""
    workspace = config.get('workspace')
    formats = config.get('formats', ['mermaid'])
    output_dir = config.get('output_dir', 'docs/diagrams')
    validate_before = config.get('options', {}).get('validate_before_export', True)
    parallel = config.get('options', {}).get('parallel_export', False)
    
    if not workspace:
        print(f"{ERR} No workspace specified in config")
        return False
    
    if not os.path.exists(workspace):
        print(f"{ERR} Workspace file not found: {workspace}")
        return False
    
    # Validate if requested
    if validate_before and not dry_run:
        if not validate_workspace(workspace, verbose=verbose):
            return False
    
    def export_format(fmt):
        """Export a single format"""
        print(f"{INFO} Exporting to {fmt}...")
        cmd_args = ['--workspace', workspace, '--format', fmt, '--output', output_dir]
        return (fmt, run_docker_command('export', cmd_args, verbose=verbose, dry_run=dry_run))
    
    results = {}
    
    if parallel and len(formats) > 1 and not dry_run:
        print(f"{INFO} Exporting {len(formats)} formats in parallel...")
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(formats))) as executor:
            future_to_format = {executor.submit(export_format, fmt): fmt for fmt in formats}
            for future in concurrent.futures.as_completed(future_to_format):
                fmt, success = future.result()
                results[fmt] = success
                if not success:
                    print(f"{WARN} Failed to export {fmt}")
    else:
        # Sequential export
        for fmt in formats:
            fmt, success = export_format(fmt)
            results[fmt] = success
            if not success:
                print(f"{WARN} Failed to export {fmt}, continuing with other formats...")
    
    # Enhanced summary with file information
    print(f"\n{INFO} Export Summary:")
    for fmt, success in results.items():
        status = OK if success else ERR
        
        if success and not dry_run:
            # Find exported files for this format
            output_dir_abs = os.path.abspath(output_dir)
            ext_map = {
                'mermaid': '.mmd',
                'plantuml': '.puml',
                'svg': '.svg',
                'png': '.png',
                'html': '.html',
                'json': '.json'
            }
            ext = ext_map.get(fmt, f'.{fmt}')
            
            try:
                files = list(Path(output_dir_abs).glob(f'*{ext}'))
                if files:
                    total_size = sum(f.stat().st_size for f in files)
                    size_str = f"{total_size:,} bytes"
                    if total_size > 1024:
                        size_str += f" ({total_size / 1024:.1f} KB)"
                    print(f"  {status} {fmt} - {len(files)} file(s), {size_str}")
                else:
                    print(f"  {status} {fmt}")
            except Exception:
                print(f"  {status} {fmt}")
        else:
            print(f"  {status} {fmt}")
    
    return all(results.values())


class WorkspaceHandler(FileSystemEventHandler):
    """File system event handler for watch mode"""
    def __init__(self, workspace_path, formats, output_dir):
        self.workspace_path = workspace_path
        self.formats = formats
        self.output_dir = output_dir
        self.last_modified = 0
    
    def on_modified(self, event):
        if event.src_path.endswith(('.dsl', '.json')) and os.path.abspath(event.src_path) == os.path.abspath(self.workspace_path):
            # Debounce: wait 1 second before re-exporting
            current_time = time.time()
            if current_time - self.last_modified > 1:
                self.last_modified = current_time
                print(f"\n{INFO} Workspace changed, re-exporting...")
                
                for fmt in self.formats:
                    cmd_args = ['--workspace', self.workspace_path, '--format', fmt, '--output', self.output_dir]
                    run_docker_command('export', cmd_args, show_progress_indicator=False)


def watch_workspace(workspace_path, formats, output_dir):
    """Watch workspace for changes and auto-export"""
    if not WATCHDOG_AVAILABLE:
        print(f"{ERR} Watch mode requires 'watchdog' package")
        print(f"{INFO} Install with: pip install watchdog")
        return False
    
    workspace_dir = os.path.dirname(os.path.abspath(workspace_path))
    
    event_handler = WorkspaceHandler(workspace_path, formats, output_dir)
    observer = Observer()
    observer.schedule(event_handler, workspace_dir, recursive=False)
    observer.start()
    
    print(f"{INFO} Watching {workspace_dir} for changes... (Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print(f"\n{OK} Stopped watching")
    
    observer.join()
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Structurizr CLI Helper Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export to Mermaid
  python structurizr.py export --workspace docs/Architecture.dsl --format mermaid --output docs/
  
  # Validate DSL
  python structurizr.py validate --workspace docs/Architecture.dsl
  
  # Start interactive server
  python structurizr.py serve --workspace docs/Architecture.dsl
  
  # Use config file
  python structurizr.py --config structurizr-config.json
  
  # Watch mode (auto-export on changes)
  python structurizr.py export --workspace docs/Architecture.dsl --format mermaid --output docs/ --watch
  
  # Generate config template
  python structurizr.py init
  
  # Dry run (see what would happen)
  python structurizr.py export --workspace docs/Architecture.dsl --format mermaid --output docs/ --dry-run
  
  # Verbose mode
  python structurizr.py export --workspace docs/Architecture.dsl --format mermaid --output docs/ --verbose
  
  # Check dependencies
  python structurizr.py --check
        """
    )
    
    parser.add_argument('command', nargs='?', choices=['export', 'validate', 'serve', 'check', 'init'],
                       help='Structurizr CLI command')
    parser.add_argument('--workspace', help='DSL workspace file')
    parser.add_argument('--format', help='Export format (mermaid, plantuml, png, svg, html, json)')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--config', help='Configuration file (JSON)')
    parser.add_argument('--check', action='store_true', help='Check dependencies and exit')
    parser.add_argument('--watch', action='store_true', help='Watch workspace for changes and auto-export')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation before export')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output for debugging')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    # Allow remaining arguments to pass through
    args, unknown_args = parser.parse_known_args()
    
    # Handle init command
    if args.command == 'init':
        output_file = args.config or 'structurizr-config.json'
        if os.path.exists(output_file):
            overwrite = input(f"{WARN} {output_file} already exists. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                sys.exit(0)
        if generate_config_template(output_file):
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Handle check command
    if args.check or (not args.command and not args.config):
        if check_docker():
            check_structurizr_image()
            if not check_structurizr_image():
                pull = input(f"{WARN} Pull Structurizr CLI image now? (y/n): ")
                if pull.lower() == 'y':
                    pull_image()
        sys.exit(0)
    
    # Load config if provided
    config = None
    if args.config:
        config = load_config(args.config)
        if config is None:
            sys.exit(1)
        if not validate_config(config):
            sys.exit(1)
    
    # Merge config with command-line args
    workspace = args.workspace or (config.get('workspace') if config else None)
    format_type = args.format or (config.get('formats', [None])[0] if config else None)
    output = args.output or (config.get('output_dir') if config else None)
    docker_image = config.get('docker_image') if config else None
    
    # Handle serve command
    if args.command == 'serve':
        if not check_docker():
            sys.exit(1)
        
        if not check_structurizr_image(DEFAULT_LITE_IMAGE):
            if not pull_image(DEFAULT_LITE_IMAGE):
                sys.exit(1)
        
        serve_args = unknown_args
        if workspace:
            serve_args = ['--workspace', workspace] + serve_args
        
        if args.dry_run:
            print(f"{WARN} Serve command not compatible with dry-run")
            sys.exit(1)
        
        print(f"{INFO} Starting Structurizr Lite server...")
        print(f"{INFO} Access at http://localhost:{DEFAULT_SERVE_PORT}")
        run_docker_command('serve', serve_args, serve=True, docker_image=DEFAULT_LITE_IMAGE, verbose=args.verbose)
        sys.exit(0)
    
    # Handle validate command
    if args.command == 'validate':
        if not check_docker():
            sys.exit(1)
        
        if not check_structurizr_image(docker_image or DEFAULT_DOCKER_IMAGE):
            if not pull_image(docker_image or DEFAULT_DOCKER_IMAGE):
                sys.exit(1)
        
        if not workspace:
            print(f"{ERR} --workspace is required for validate command")
            sys.exit(1)
        
        success = validate_workspace(workspace, verbose=args.verbose)
        sys.exit(0 if success else 1)
    
    # Handle export command
    if args.command == 'export':
        if not args.dry_run and not check_docker():
            sys.exit(1)
        
        if not args.dry_run:
            if not check_structurizr_image(docker_image or DEFAULT_DOCKER_IMAGE):
                if not pull_image(docker_image or DEFAULT_DOCKER_IMAGE):
                    sys.exit(1)
        
        if not workspace:
            print(f"{ERR} --workspace is required for export command")
            sys.exit(1)
        
        # Validate before export (unless disabled or dry run)
        if not args.no_validate and not args.dry_run:
            if not validate_workspace(workspace, verbose=args.verbose):
                sys.exit(1)
        
        # Handle watch mode
        if args.watch:
            if args.dry_run:
                print(f"{WARN} Watch mode not compatible with dry-run")
                sys.exit(1)
            formats = [format_type] if format_type else ['mermaid']
            output_dir = output or 'docs/diagrams'
            watch_workspace(workspace, formats, output_dir)
            sys.exit(0)
        
        # Build arguments
        cmd_args = unknown_args.copy()
        
        if workspace:
            cmd_args.extend(['--workspace', workspace])
        if format_type:
            cmd_args.extend(['--format', format_type])
        if output:
            # Make output path relative to workspace directory
            output_abs = os.path.abspath(output)
            workspace_abs = os.path.dirname(os.path.abspath(workspace))
            
            try:
                output_rel = os.path.relpath(output_abs, workspace_abs)
                cmd_args.extend(['--output', output_rel])
            except ValueError:
                # Different drive on Windows - use absolute path normalized
                print(f"{WARN} Output directory on different drive, using absolute path")
                cmd_args.extend(['--output', output])
        else:
            # Default to current directory
            cmd_args.extend(['--output', '.'])
        
        success = run_docker_command(
            'export',
            cmd_args,
            docker_image=docker_image,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
    
    # If no command but config provided, process config
    if config and not args.command:
        if not args.dry_run and not check_docker():
            sys.exit(1)
        
        if not args.dry_run:
            if not check_structurizr_image():
                if not pull_image():
                    sys.exit(1)
        
        # Use batch export function
        success = batch_export(config, verbose=args.verbose, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()

