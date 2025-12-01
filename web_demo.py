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

# Use Docker paths if /app exists, otherwise use local paths
BASE_DIR = Path('/app') if Path('/app').exists() else Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
OUTPUT_FOLDER = BASE_DIR / 'output'
EXAMPLES_FOLDER = BASE_DIR / 'docs' / 'examples' / 'generated'

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
        from convert_final import markdown_to_pdf
        
        # Convert markdown to PDF (use Playwright renderer for Docker compatibility)
        markdown_to_pdf(str(md_path), str(pdf_path), renderer='playwright')
        
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


@app.route('/examples')
def list_examples():
    """List pre-generated example PDFs"""
    examples = [
        {
            'name': 'SOLID Implementation Analysis',
            'description': 'Deep dive into SOLID principles in the PDF generation system',
            'file': 'solid-implementation.pdf',
            'source': 'docs/development/pdf-solid-implementation.md',
            'size': '2.3 MB'
        },
        {
            'name': 'Structurizr Architecture Evaluation',
            'description': 'Evaluation of Structurizr CLI for architecture diagrams',
            'file': 'structurizr-evaluation.pdf',
            'source': 'docs/development/structurizr-solid-evaluation.md',
            'size': '1.8 MB'
        },
        {
            'name': 'PDF Generation Setup Guide',
            'description': 'Complete setup and configuration documentation',
            'file': 'pdf-setup-guide.pdf',
            'source': 'tools/pdf/docs/PDF_GENERATION_SETUP.md',
            'size': '1.2 MB'
        }
    ]
    
    # Filter to only examples that actually exist
    available_examples = []
    for example in examples:
        example_path = EXAMPLES_FOLDER / example['file']
        if example_path.exists():
            example['available'] = True
            available_examples.append(example)
        else:
            example['available'] = False
            available_examples.append(example)
    
    return jsonify(available_examples)


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

