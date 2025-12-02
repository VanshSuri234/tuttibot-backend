#!/usr/bin/env python3
"""
TuttiBot Web API
================

Flask web server providing REST API endpoints for TuttiBot music analysis.

Endpoints:
- POST /analyze - Upload audio and score files for analysis
- GET /status/<job_id> - Check analysis status
- GET /results/<job_id> - Get analysis results
- GET /download/<job_id>/<file> - Download specific result files
"""

import os
import sys
import json
import uuid
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import logging

# Add TuttiBot modules to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import TuttiBot pipeline
try:
    from main import TuttiBotPipeline
except ImportError:
    # Fallback if main.py is not importable directly (e.g. if it has code at module level)
    # But looking at main.py content, it has a main() function and if __name__ == "__main__" block
    # so it should be safe to import.
    logging.warning("Could not import TuttiBotPipeline from main.py")
    TuttiBotPipeline = None

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['RESULTS_FOLDER']).mkdir(exist_ok=True)

# Job status tracking
jobs = {}
job_lock = threading.Lock()

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'flac', 'aac', 'ogg'}
ALLOWED_SCORE_EXTENSIONS = {'pdf', 'xml', 'musicxml', 'mxl', 'mid', 'midi'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

class JobStatus:
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

def run_analysis(job_id, audio_path, score_path):
    """Run TuttiBot analysis in background thread"""
    
    with job_lock:
        jobs[job_id]['status'] = JobStatus.PROCESSING
        jobs[job_id]['started_at'] = datetime.now().isoformat()
    
    try:
        # Create output directory for this job
        job_output_dir = Path(app.config['RESULTS_FOLDER']) / job_id
        job_output_dir.mkdir(exist_ok=True)
        
        if TuttiBotPipeline:
            # Initialize TuttiBot pipeline
            pipeline = TuttiBotPipeline(output_dir=str(job_output_dir))
            
            # Run analysis
            success = pipeline.run_complete_pipeline(audio_path, score_path)
            
            # Collect results
            results = {}
            if success:
                # Collect all JSON outputs
                json_files = list(job_output_dir.rglob("*.json"))
                for json_file in json_files:
                    try:
                        with open(json_file) as f:
                            data = json.load(f)
                        results[json_file.stem] = data
                    except Exception as e:
                        logging.warning(f"Could not load {json_file}: {e}")
                
                # Update job status
                with job_lock:
                    jobs[job_id]['status'] = JobStatus.COMPLETED
                    jobs[job_id]['completed_at'] = datetime.now().isoformat()
                    jobs[job_id]['results'] = results
                    jobs[job_id]['output_dir'] = str(job_output_dir)
            else:
                with job_lock:
                    jobs[job_id]['status'] = JobStatus.FAILED
                    jobs[job_id]['error'] = "Analysis pipeline failed"
        else:
             with job_lock:
                jobs[job_id]['status'] = JobStatus.FAILED
                jobs[job_id]['error'] = "Pipeline not available"

    except Exception as e:
        with job_lock:
            jobs[job_id]['status'] = JobStatus.FAILED
            jobs[job_id]['error'] = str(e)
        logging.exception(f"Analysis failed for job {job_id}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Submit audio and score files for analysis
    """
    
    if 'audio_file' not in request.files or 'score_file' not in request.files:
        return jsonify({'error': 'Missing audio_file or score_file'}), 400
    
    audio_file = request.files['audio_file']
    score_file = request.files['score_file']
    
    if audio_file.filename == '' or score_file.filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Validate file types
    if not allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
        return jsonify({'error': f'Invalid audio file type. Allowed: {ALLOWED_AUDIO_EXTENSIONS}'}), 400
    
    if not allowed_file(score_file.filename, ALLOWED_SCORE_EXTENSIONS):
        return jsonify({'error': f'Invalid score file type. Allowed: {ALLOWED_SCORE_EXTENSIONS}'}), 400
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded files
    audio_filename = secure_filename(f"{job_id}_audio_{audio_file.filename}")
    score_filename = secure_filename(f"{job_id}_score_{score_file.filename}")
    
    audio_path = Path(app.config['UPLOAD_FOLDER']) / audio_filename
    score_path = Path(app.config['UPLOAD_FOLDER']) / score_filename
    
    audio_file.save(str(audio_path))
    score_file.save(str(score_path))
    
    # Initialize job tracking
    with job_lock:
        jobs[job_id] = {
            'status': JobStatus.QUEUED,
            'created_at': datetime.now().isoformat(),
            'audio_file': audio_file.filename,
            'score_file': score_file.filename,
            'audio_path': str(audio_path),
            'score_path': str(score_path)
        }
    
    # Start analysis in background thread
    thread = threading.Thread(
        target=run_analysis, 
        args=(job_id, str(audio_path), str(score_path))
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': JobStatus.QUEUED,
        'message': 'Analysis started'
    }), 202

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get analysis status for a job"""
    
    with job_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = jobs[job_id].copy()
    
    # Remove sensitive paths from response
    job_info.pop('audio_path', None)
    job_info.pop('score_path', None)
    job_info.pop('output_dir', None)
    
    return jsonify(job_info)

@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """Get detailed analysis results for completed job"""
    
    with job_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = jobs[job_id]
    
    if job_info['status'] != JobStatus.COMPLETED:
        return jsonify({'error': f'Job status: {job_info["status"]}'}), 400
    
    return jsonify({
        'job_id': job_id,
        'status': job_info['status'],
        'completed_at': job_info.get('completed_at'),
        'results': job_info.get('results', {})
    })

@app.route('/download/<job_id>/<filename>', methods=['GET'])
def download_file(job_id, filename):
    """Download specific result file"""
    
    with job_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = jobs[job_id]
    
    if job_info['status'] != JobStatus.COMPLETED:
        return jsonify({'error': f'Job status: {job_info["status"]}'}), 400
    
    output_dir = Path(job_info.get('output_dir', ''))
    if not output_dir.exists():
        return jsonify({'error': 'Results directory not found'}), 404
    
    # Find the requested file
    file_path = None
    for f in output_dir.rglob(filename):
        file_path = f
        break
    
    if not file_path or not file_path.exists():
        return jsonify({'error': f'File {filename} not found'}), 404
    
    return send_file(str(file_path), as_attachment=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Development server
    print("🎵 TuttiBot Web API Server")
    print("=" * 30)
    print("Starting server on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
