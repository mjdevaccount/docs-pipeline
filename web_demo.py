"""
docs-pipeline Web Demo
Simple Flask web interface for Markdown → PDF conversion
"""

from flask import Flask, request, send_file, render_template, jsonify
from pathlib import Path
import os
import sys
import tempfile
import traceback
from werkzeug.utils import secure_filename

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'pdf'))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Use Docker paths if /app exists, otherwise use local paths
BASE_DIR = Path('/app') if Path('/app').exists() else Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'
EXAMPLES_FOLDER = BASE_DIR / 'docs' / 'examples' / 'generated'
EXAMPLES_SOURCE_FOLDER = BASE_DIR / 'docs' / 'examples'

# Create directories
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
EXAMPLES_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'md', 'markdown', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve main demo page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for Docker"""
    return jsonify({'status': 'healthy', 'service': 'docs-pipeline-web'})


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and PDF generation"""
    
    # Check if file was uploaded
    if 'markdown' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['markdown']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload .md or .markdown file'}), 400
    
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        md_path = UPLOAD_FOLDER / filename
        
        # Save uploaded file
        file.save(md_path)
        
        # Generate output PDF path
        pdf_filename = f"{md_path.stem}.pdf"
        pdf_path = OUTPUT_FOLDER / pdf_filename
        
        # Import and run PDF conversion
        from tools.pdf.core import markdown_to_pdf
        
        # Get renderer and profile from request
        # Default to playwright for Docker compatibility
        renderer = request.form.get('renderer', 'playwright')
        if renderer not in ['playwright', 'weasyprint']:
            renderer = 'playwright'  # Fallback to safe default
        
        # Get profile selection (optional)
        profile = request.form.get('profile', None)
        if profile and profile not in ['tech-whitepaper', 'dark-pro', 'minimalist', 'enterprise-blue']:
            profile = None  # Invalid profile, ignore
        
        # Get metadata from form
        custom_metadata = {}
        if request.form.get('author'):
            custom_metadata['author'] = request.form.get('author')
        if request.form.get('organization'):
            custom_metadata['organization'] = request.form.get('organization')
        if request.form.get('version'):
            custom_metadata['version'] = request.form.get('version')
        if request.form.get('classification'):
            custom_metadata['classification'] = request.form.get('classification')
        
        # Get options
        generate_cover = request.form.get('generate_cover') == 'on'
        generate_toc = request.form.get('generate_toc') == 'on'
        watermark = request.form.get('watermark', None)
        
        # Handle logo upload
        logo_path = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                logo_filename = secure_filename(logo_file.filename)
                logo_path = UPLOAD_FOLDER / logo_filename
                logo_file.save(logo_path)
                logo_path = str(logo_path)
        
        # Convert markdown to PDF with all options
        markdown_to_pdf(
            str(md_path), 
            str(pdf_path), 
            renderer=renderer, 
            profile=profile,
            logo_path=logo_path,
            generate_cover=generate_cover,
            generate_toc=generate_toc,
            watermark=watermark,
            custom_metadata=custom_metadata
        )
        
        # Check if PDF was created
        if not pdf_path.exists():
            return jsonify({'error': 'PDF generation failed - file not created'}), 500
        
        return jsonify({
            'success': True,
            'filename': pdf_filename,
            'download_url': f'/download/{pdf_filename}'
        })
        
    except Exception as e:
        print(f"Error during PDF generation: {e}")
        traceback.print_exc()
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500


@app.route('/download/<path:filepath>')
def download_file(filepath):
    """Download generated PDF (supports subdirectories)"""
    try:
        # Handle both flat files and subdirectory paths
        # Split path and secure each component
        parts = filepath.split('/')
        file_path = OUTPUT_FOLDER
        for part in parts:
            file_path = file_path / secure_filename(part)
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_path.name,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _generate_friendly_name(filename):
    """Convert filename to friendly display name"""
    # Remove extension and convert to title case
    name = filename.replace('.md', '').replace('.markdown', '')
    # Replace hyphens and underscores with spaces
    name = name.replace('-', ' ').replace('_', ' ')
    # Title case
    return ' '.join(word.capitalize() for word in name.split())


def _extract_base_name(filename):
    """Extract base name from markdown filename for PDF matching"""
    # Remove .md or .markdown extension
    base = filename.replace('.md', '').replace('.markdown', '')
    # Common patterns: convert to short base names
    # e.g., "advanced-markdown-showcase" -> "showcase"
    #       "technical-white-paper" -> "whitepaper"
    #       "product-requirements-doc" -> "prd"
    base_lower = base.lower()
    
    # Try to match common patterns
    if 'showcase' in base_lower:
        return 'showcase'
    elif 'whitepaper' in base_lower or 'white-paper' in base_lower:
        return 'whitepaper'
    elif 'prd' in base_lower or 'product-requirements' in base_lower:
        return 'prd'
    elif 'technical-spec' in base_lower or 'tech-spec' in base_lower:
        return 'tech-spec'
    else:
        # Use the last meaningful word or first few words
        parts = base.split('-')
        if len(parts) > 2:
            # Take last 1-2 meaningful parts
            return '-'.join(parts[-2:]) if len(parts[-1]) > 3 else '-'.join(parts[-3:])
        return base


@app.route('/examples')
def list_examples():
    """Dynamically discover and list pre-generated example PDFs with profile variants"""
    
    result = []
    profiles = ['tech', 'dark', 'minimalist', 'enterprise']
    
    # Discover markdown files in examples folder (excluding README and subdirectories)
    if not EXAMPLES_SOURCE_FOLDER.exists():
        return jsonify([])
    
    # Find all markdown files in the examples directory (not in subdirectories)
    markdown_files = [
        f for f in EXAMPLES_SOURCE_FOLDER.iterdir()
        if f.is_file() and f.suffix.lower() in ['.md', '.markdown']
        and f.name.lower() != 'readme.md'
    ]
    
    # Sort for consistent ordering
    markdown_files.sort(key=lambda x: x.name.lower())
    
    for md_file in markdown_files:
        base_name = _extract_base_name(md_file.name)
        friendly_name = _generate_friendly_name(md_file.name)
        source_path = f"docs/examples/{md_file.name}"
        
        # Check for PDFs matching this markdown file
        available_files = []
        for profile in profiles:
            # Try different naming patterns
            possible_names = [
                f"{base_name}-{profile}.pdf",
                f"{md_file.stem}-{profile}.pdf",
            ]
            
            for pdf_name in possible_names:
                pdf_path = EXAMPLES_FOLDER / pdf_name
                if pdf_path.exists():
                    size_bytes = pdf_path.stat().st_size
                    size_mb = size_bytes / 1024 / 1024
                    available_files.append({
                        'profile': profile,
                        'filename': pdf_name,
                        'size': f"{size_mb:.1f} MB"
                    })
                    break  # Found a match, move to next profile
        
        # Also check for any PDF that starts with the base name (catch-all)
        if not available_files:
            for pdf_file in EXAMPLES_FOLDER.glob(f"{base_name}*.pdf"):
                # Extract profile from filename if possible
                pdf_stem = pdf_file.stem
                if '-' in pdf_stem:
                    parts = pdf_stem.split('-')
                    if len(parts) >= 2:
                        potential_profile = parts[-1]
                        if potential_profile in profiles:
                            size_bytes = pdf_file.stat().st_size
                            size_mb = size_bytes / 1024 / 1024
                            available_files.append({
                                'profile': potential_profile,
                                'filename': pdf_file.name,
                                'size': f"{size_mb:.1f} MB"
                            })
        
        # Sort available files by profile order
        profile_order = {p: i for i, p in enumerate(profiles)}
        available_files.sort(key=lambda x: profile_order.get(x['profile'], 999))
        
        if available_files:
            # Use first available file as primary
            result.append({
                'name': friendly_name,
                'description': f'Generated from {md_file.name}',
                'source': source_path,
                'file': available_files[0]['filename'],
                'size': available_files[0]['size'],
                'available': True,
                'profiles': available_files
            })
        else:
            # Show as unavailable but still list it
            result.append({
                'name': friendly_name,
                'description': f'Source file: {md_file.name} (PDF not yet generated)',
                'source': source_path,
                'file': f"{base_name}-tech.pdf",  # Expected filename
                'size': 'N/A',
                'available': False,
                'profiles': []
            })
    
    return jsonify(result)


@app.route('/example/<filename>')
def download_example(filename):
    """Download pre-generated example PDF"""
    try:
        file_path = EXAMPLES_FOLDER / secure_filename(filename)
        
        if not file_path.exists():
            return jsonify({'error': 'Example not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pipeline', methods=['POST'])
def run_pipeline_endpoint():
    """Handle pipeline config upload and execution"""
    
    if 'config' not in request.files:
        return jsonify({'error': 'No config file uploaded'}), 400
    
    file = request.files['config']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.yaml', '.yml')):
        return jsonify({'error': 'Config must be YAML file (.yaml or .yml)'}), 400
    
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        config_path = UPLOAD_FOLDER / filename
        
        # Save config
        file.save(config_path)
        
        # Run pipeline and capture output
        from tools.docs_pipeline.runner import run_pipeline
        import io
        import sys
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            success = run_pipeline(config_path, dry_run=False, parallel=True)
        finally:
            sys.stdout = old_stdout
        
        log_output = captured_output.getvalue()
        
        # Find all generated PDFs in output folder and subdirectories
        generated_pdfs = []
        for pdf_file in OUTPUT_FOLDER.rglob('*.pdf'):
            rel_path = pdf_file.relative_to(OUTPUT_FOLDER)
            generated_pdfs.append({
                'filename': pdf_file.name,
                'path': str(rel_path),
                'download_url': f'/download/{rel_path}',
                'size': f"{pdf_file.stat().st_size / 1024 / 1024:.2f} MB"
            })
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Pipeline executed successfully',
                'log': log_output,
                'outputs': generated_pdfs,
                'count': len(generated_pdfs)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Pipeline execution failed',
                'log': log_output
            }), 500
            
    except Exception as e:
        print(f"Error during pipeline execution: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Pipeline execution failed: {str(e)}'}), 500


if __name__ == '__main__':
    print("🚀 Starting docs-pipeline web demo...")
    print("📍 Server will be available at http://localhost:8080")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📄 Output folder:", OUTPUT_FOLDER)
    print("📚 Examples folder:", EXAMPLES_FOLDER)
    
    app.run(host='0.0.0.0', port=8080, debug=True)

