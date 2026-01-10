#!/usr/bin/env python3
"""
TuttiBot Web API
================
Flask web server providing REST API endpoints for TuttiBot music analysis.
Integrates with Unitree G1 Robot and Layer-Aware Groq AI Chat.
"""

import os
import sys
import json
import uuid
import threading
import subprocess
import logging
import re
import psutil
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Setup logging with detailed diagnostics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_system_status(label: str):
    """Log system resource usage for debugging"""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()
        cpu_percent = process.cpu_percent(interval=0.1)
        thread_count = threading.active_count()
        
        logger.info(f"[SYSTEM {label}] RAM: {mem_info.rss / 1024 / 1024:.1f}MB ({mem_percent:.1f}%) | CPU: {cpu_percent:.1f}% | Threads: {thread_count}")
    except Exception as e:
        logger.warning(f"Could not get system status: {e}")

# --- AI INTEGRATION ---
try:
    from groq import Groq
except ImportError:
    logging.warning("Groq library not found. Run: pip install groq")
    Groq = None

# ==========================================
# CONFIGURATION
# ==========================================

# NETWORK INTERFACE - CONFIGURABLE FROM ENVIRONMENT
ROBOT_INTERFACE = os.getenv("ROBOT_INTERFACE", "enp4s0")

# Path to the compiled C++ executable
current_dir = Path(__file__).parent
PATH_TO_LED_EXE = current_dir / "led_control" / "build" / "g1_led_controller"

# Check if LED controller is available
LED_ENABLED = os.path.exists(PATH_TO_LED_EXE) and os.getenv("FLASK_ENV") != "production"

# Add TuttiBot modules to path
sys.path.insert(0, str(current_dir))

# Import TuttiBot pipeline
try:
    from MusicPerformanceAnalysis.pipeline import MusicPerformancePipeline
except ImportError:
    logging.warning("Could not import MusicPerformancePipeline.")
    MusicPerformancePipeline = None
    
# Mock LLM Service if missing
try:
    from llm_service import llm_service
except ImportError:
    llm_service = None

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://music4-d.vercel.app", "http://localhost:3000", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY") 

Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['RESULTS_FOLDER']).mkdir(exist_ok=True)

jobs = {}
job_lock = threading.Lock()

# Initialize Groq client
groq_client = Groq(api_key=app.config['GROQ_API_KEY']) if Groq and app.config['GROQ_API_KEY'] else None

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

# ==========================================
# STATUS PERSISTENCE FUNCTIONS
# ==========================================

def save_job_status(job_id, status_dict):
    """Save job status to disk for cross-worker consistency"""
    try:
        status_file = Path(app.config['RESULTS_FOLDER']) / job_id / 'status.json'
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump(status_dict, f, indent=2)
        logging.info(f"Status saved for job {job_id}: {status_dict.get('status', 'unknown')}")
    except Exception as e:
        logging.error(f"Failed to save status for job {job_id}: {e}")

def load_job_status(job_id):
    """Load job status from disk"""
    try:
        status_file = Path(app.config['RESULTS_FOLDER']) / job_id / 'status.json'
        if status_file.exists():
            with open(status_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logging.error(f"Failed to load status for job {job_id}: {e}")
        return None

# ==========================================
# UPDATED: CHATBOT SERVICE (MAPPED TO BLOCKS)
# ==========================================

import json
import logging
from pathlib import Path
from flask import current_app



import json
import logging
from pathlib import Path
from flask import current_app

import json
from pathlib import Path
from flask import current_app

import json
import logging
from pathlib import Path
from flask import current_app

import json
import logging
from pathlib import Path
from flask import current_app

class ChatbotService:

    @staticmethod
    def detect_intent(message):
        msg = message.lower()
        if any(k in msg for k in ["timing", "rhythm", "tempo"]):
            return "timing"
        if "pitch" in msg or "intonation" in msg:
            return "pitch"
        if any(k in msg for k in ["dynamic", "loud", "soft", "accent"]):
            return "dynamics"
        if "match" in msg or "score" in msg:
            return "score_match"
        if any(k in msg for k in ["improve", "practice", "better"]):
            return "improvement"
        return "general"

    @staticmethod
    def generate_response(job_id, user_message, chat_history):
        from flask import current_app
        from app import groq_client
        import json
        from pathlib import Path

        summary_path = Path(current_app.config["RESULTS_FOLDER"]) / job_id / "chatbot_summary.json"

        if not summary_path.exists():
            return "Your analysis is still being prepared. Please try again shortly."

        with open(summary_path) as f:
            data = json.load(f)

        intent = ChatbotService.detect_intent(user_message)

        scores = data.get("scores", {})
        pitch = data.get("pitch", {})
        rhythm = data.get("rhythm", {})
        dynamics = data.get("dynamics", {})
        match = data.get("score_match", {})

        # =========================
        # DATA-DRIVEN RESPONSES
        # =========================
        if intent == "pitch":
            response = (
                f"Your pitch accuracy is {pitch.get('accuracy_pct')}%. "
                f"Pitch inconsistencies appear in bars {pitch.get('incorrect_bars')}. "
                "Focus on slow practice and pitch reference for these sections."
            )

        elif intent == "timing":
            response = (
                f"Your average timing deviation is {rhythm.get('mean_onset_error_ms')} ms. "
                f"You tend to play early in bars {rhythm.get('early_bars')} "
                f"and late in bars {rhythm.get('late_bars')}. "
                "Practicing with a metronome will help stabilize this."
            )

        elif intent == "dynamics":
            response = (
                f"Your dynamic range is approximately {dynamics.get('dynamic_range_db')} dB. "
                "There is room to exaggerate contrasts between soft and loud passages."
            )

        elif intent == "score_match":
            response = (
                f"Your note accuracy compared to the score is {match.get('note_accuracy_percent')}%. "
                f"Extra notes: {match.get('extra_notes')}, "
                f"Missing notes: {match.get('missing_notes')}."
            )

        elif intent == "improvement":
            response = (
                "To improve your performance, prioritize pitch stability in inaccurate bars, "
                "then address rhythmic consistency and expressive dynamics."
            )

        else:
            response = (
                f"Your overall performance score is {scores.get('overall')} out of 100. "
                "You can ask about pitch, timing, dynamics, score accuracy, or improvement strategies."
            )

        # =========================
        # LLM POLISH (NO FACT ADDITION)
        # =========================
        system_prompt = (
            "You are a calm, experienced music teacher. "
            "Do not add new facts. Only rephrase clearly and supportively."
        )

        llm_resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": response}
            ],
            temperature=0.2
        )

        return llm_resp.choices[0].message.content

# ==========================================
# ROBOT CONTROL FUNCTIONS (PRESERVED)
# ==========================================

def trigger_robot_leds(score_data):
    """Determines color based on score and calls C++ executable."""
    try:
        exe_path = str(PATH_TO_LED_EXE)
        if not os.path.exists(exe_path):
            logging.error(f"Robot executable not found at {exe_path}")
            return

        overall_score = 0.0
        if 'grade_data' in score_data and 'overall_score' in score_data['grade_data']:
            overall_score = float(score_data['grade_data']['overall_score'])
        elif 'overall_score' in score_data:
            overall_score = float(score_data['overall_score'])
        
        # Color mapping: Green for high, Blue/Pink for mid, Red for low
        r, g, b = 0, 0, 0
        if overall_score > 75: r, g, b = 0, 255, 0 
        elif overall_score >= 60: r, g, b = 255, 100, 255 
        else: r, g, b = 255, 0, 0 

        logging.info(f"Triggering Robot LED: Score {overall_score} -> RGB({r},{g},{b})")
        
        cmd = [exe_path, ROBOT_INTERFACE, str(r), str(g), str(b)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0:
            logging.error(f"ROBOT LED FAILED: {result.stderr}")
        else:
            logging.info(f"Robot LED Success: {result.stdout.strip()}")

    except Exception as e:
        logging.error(f"Failed to trigger robot LEDs: {e}")

# ==========================================
# PIPELINE LOGIC (PRESERVED REGEX + CONTEXT SYNC)
# ==========================================

def run_analysis(job_id, audio_path, score_path):
    log_system_status(f"RUN_ANALYSIS_START_{job_id}")
    logger.info(f"\n{'='*80}")
    logger.info(f"[EXECUTION_START] Job: {job_id}")
    logger.info(f"[INPUTS] Audio: {audio_path} | Score: {score_path}")
    logger.info(f"{'='*80}\n")
    start_time = datetime.now()
    
    with job_lock:
        jobs[job_id]['status'] = JobStatus.PROCESSING
        jobs[job_id]['started_at'] = start_time.isoformat()
    
    try:
        job_output_dir = Path(app.config['RESULTS_FOLDER']) / job_id
        job_output_dir.mkdir(exist_ok=True)
        logger.info(f"[OUTPUT_DIR] {job_output_dir}")

        # Write initial status to disk
        logger.info(f"[STATUS_UPDATE] Layer 0: Initializing")
        save_job_status(job_id, {
            'status': JobStatus.PROCESSING,
            'current_layer': 'Layer 0: Initializing',
            'progress': 0,
            'timestamp': datetime.now().isoformat()
        })

        # 1. RUN PIPELINE
        success = False
        try:
            if MusicPerformancePipeline:
                logger.info(f"\n[CHECKPOINT] Importing MusicPerformancePipeline")
                logger.info(f"[PIPELINE_INIT] Creating pipeline object for job {job_id}")
                log_system_status(f"BEFORE_PIPELINE_INIT__{job_id}")
                
                pipeline_obj = MusicPerformancePipeline(audio_path, score_path, str(job_output_dir))
                logger.info(f"[PIPELINE_INIT_COMPLETE] Pipeline object created successfully")
                log_system_status(f"AFTER_PIPELINE_INIT__{job_id}")
                
                # Update status to Layer 1
                logger.info(f"[STATUS_UPDATE] Layer 1: Input Standardization")
                save_job_status(job_id, {
                    'status': JobStatus.PROCESSING,
                    'current_layer': 'Layer 1: Input Standardization',
                    'progress': 15,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"\n[PIPELINE_EXECUTION_START] Calling pipeline.run_pipeline() for job {job_id}")
                log_system_status(f"BEFORE_RUN_PIPELINE__{job_id}")
                
                success = pipeline_obj.run_pipeline()
                
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"\n[PIPELINE_EXECUTION_END] Status: {success} | Total Time: {elapsed:.2f}s")
                log_system_status(f"AFTER_RUN_PIPELINE__{job_id}")
                
                # --- UPDATED: GENERATE CHATBOT CONTEXT ---
                if success and hasattr(pipeline_obj, 'get_chatbot_context'):
                    pipeline_obj.get_chatbot_context()
            else:
                logger.error("Pipeline module not loaded - MusicPerformancePipeline is None")
                success = False
        except Exception as e:
            logger.error(f"[PIPELINE_ERROR] job {job_id}: {str(e)}", exc_info=True)
            log_system_status(f"AFTER_PIPELINE_ERROR__{job_id}")
            success = False

        results = {'grade_data': {}}
        
        # 2. READ JSON SUMMARY
        summary_path = job_output_dir / "pipeline_summary.json"
        summary_data = {}
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                summary_data = json.load(f)
                if 'overall_score' in summary_data:
                    results['grade_data']['overall_score'] = summary_data['overall_score']
                results['pipeline_summary'] = summary_data

        # 3. READ TEXT REPORT (PRESERVED ORIGINAL REGEX LOGIC)
        grading_dir = job_output_dir / "07_grading"
        report_path = grading_dir / "performance_report.txt"
        report_text = ""

        if report_path.exists():
            with open(report_path, 'r') as f:
                report_text = f.read()
                results['report_text'] = report_text
                
                # Regex for Overall Score
                if 'overall_score' not in results['grade_data']:
                    overall_match = re.search(r"Overall Score:\s*([\d\.]+)/100", report_text)
                    if overall_match:
                        results['grade_data']['overall_score'] = float(overall_match.group(1))
                
                # Regex for Component Scores
                comp_section = re.search(r"COMPONENT SCORES\n-+\n(.*?)\n\n", report_text, re.DOTALL)
                if comp_section:
                    results['grade_data']['components'] = {}
                    for line in comp_section.group(1).strip().split('\n'):
                        parts = re.match(r"([^:]+):\s*([\d\.]+)%", line.strip())
                        if parts:
                            results['grade_data']['components'][parts.group(1).strip()] = float(parts.group(2))

                # Regex for Detailed Metrics (Category-based)
                detailed_section = re.search(r"DETAILED METRICS\n-+\n(.*?)((?:={10,})|$)", report_text, re.DOTALL)
                if detailed_section:
                    results['grade_data']['detailed_metrics'] = {}
                    current_category = "General"
                    for line in detailed_section.group(1).strip().split('\n'):
                        line = line.strip()
                        if not line: continue
                        if line.endswith(':'):
                            current_category = line[:-1]
                            results['grade_data']['detailed_metrics'][current_category] = {}
                        elif ':' in line:
                            parts = line.split(':', 1)
                            results['grade_data']['detailed_metrics'][current_category][parts[0].strip()] = parts[1].strip()

        with job_lock:
            jobs[job_id]['status'] = JobStatus.COMPLETED
            jobs[job_id]['completed_at'] = datetime.now().isoformat()
            jobs[job_id]['results'] = results
            jobs[job_id]['output_dir'] = str(job_output_dir)
        
        # Write completion status to disk
        save_job_status(job_id, {
            'status': JobStatus.COMPLETED,
            'current_layer': 'Layer 7: Grading Complete',
            'progress': 100,
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        
        if llm_service:
            llm_response = llm_service.initialize_analysis(job_id, json.dumps(summary_data, indent=2), report_text)
            with job_lock:
                jobs[job_id]['llm_initial_analysis'] = llm_response

    except Exception as e:
        with job_lock:
            jobs[job_id]['status'] = JobStatus.FAILED
            jobs[job_id]['error'] = str(e)
        
        # Write error status to disk
        save_job_status(job_id, {
            'status': JobStatus.FAILED,
            'current_layer': 'Error',
            'progress': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
        logging.exception(f"Analysis failed for job {job_id}")

# ==========================================
# ROUTES (ALL ORIGINAL ROUTES PRESERVED)
# ==========================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - returns API info"""
    return jsonify({
        'service': 'TuttiBot Backend API',
        'version': '1.0.0',
        'status': 'healthy',
        'endpoints': {
            'POST /upload': 'Upload audio and score files',
            'GET /status/<job_id>': 'Check analysis status',
            'GET /results/<job_id>': 'Get analysis results',
            'POST /chat': 'Chat about analysis results',
            'GET /health': 'Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '1.0.0'})

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'audio_file' not in request.files or 'score_file' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    
    audio_file = request.files['audio_file']
    score_file = request.files['score_file']
    
    job_id = str(uuid.uuid4())
    audio_path = Path(app.config['UPLOAD_FOLDER']) / secure_filename(f"{job_id}_audio_{audio_file.filename}")
    score_path = Path(app.config['UPLOAD_FOLDER']) / secure_filename(f"{job_id}_score_{score_file.filename}")
    
    audio_file.save(str(audio_path))
    score_file.save(str(score_path))
    
    with job_lock:
        jobs[job_id] = {'status': JobStatus.QUEUED, 'created_at': datetime.now().isoformat()}
    
    thread = threading.Thread(target=run_analysis, args=(job_id, str(audio_path), str(score_path)))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id, 'status': JobStatus.QUEUED}), 202

@app.route('/upload', methods=['POST'])
def upload():
    """Alias for /analyze endpoint for frontend compatibility"""
    return analyze()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    job_id = data.get('job_id')
    user_message = data.get('message')
    history = data.get('history', [])

    # Validation: Ensure we have the minimum requirements to talk to the AI
    if not job_id or not user_message:
        return jsonify({"error": "Missing job_id or message"}), 400

    try:
        # Call as a Static Method: ClassName.method()
        bot_response = ChatbotService.generate_response(job_id, user_message, history)
        return jsonify({"response": bot_response})
    except Exception as e:
        # This logging will now catch errors properly
        logging.error(f"Chat Route Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    with job_lock:
        if job_id not in jobs: return jsonify({'error': 'Job not found'}), 404
        job_info = jobs[job_id]
    
    if job_info['status'] == JobStatus.COMPLETED and 'results' in job_info:
        trigger_robot_leds(job_info['results'])
    
    return jsonify(job_info)

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    # First, try to read from disk (cross-worker consistency)
    job_status_path = Path(app.config['RESULTS_FOLDER']) / job_id / 'status.json'
    if job_status_path.exists():
        try:
            with open(job_status_path, 'r') as f:
                status_data = json.load(f)
                return jsonify(status_data), 200
        except Exception as e:
            logging.error(f"Error reading status from disk: {e}")
    
    # Fall back to in-memory dict
    with job_lock:
        if job_id not in jobs: 
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = jobs[job_id]
        status = job_info['status']
        
        # Check for timeout (15 minutes)
        if status == JobStatus.PROCESSING:
            started_at = datetime.fromisoformat(job_info['started_at'])
            elapsed = (datetime.now() - started_at).total_seconds()
            if elapsed > 900:  # 15 minutes
                status = JobStatus.FAILED
                job_info['status'] = status
                job_info['error'] = f'Analysis timeout after {elapsed:.0f} seconds'
        
        return jsonify({
            'status': status, 
            'error': job_info.get('error'),
            'created_at': job_info.get('created_at'),
            'started_at': job_info.get('started_at')
        })

@app.route('/download/<job_id>/<filename>', methods=['GET'])
def download_file(job_id, filename):
    with job_lock:
        if job_id not in jobs: return jsonify({'error': 'Not found'}), 404
        output_dir = Path(jobs[job_id].get('output_dir', ''))
    
    for f in output_dir.rglob(filename):
        return send_file(str(f), as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check system status"""
    return jsonify({
        'status': 'ok',
        'pipeline_loaded': MusicPerformancePipeline is not None,
        'groq_configured': groq_client is not None,
        'upload_folder': str(Path(app.config['UPLOAD_FOLDER']).absolute()),
        'results_folder': str(Path(app.config['RESULTS_FOLDER']).absolute()),
        'active_jobs': len([j for j in jobs.values() if j['status'] == JobStatus.PROCESSING]),
        'total_jobs': len(jobs)
    })

if __name__ == '__main__':
    # IMPORTANT: This should NEVER be reached in production!
    # On Render, Gunicorn runs directly: gunicorn app:app
    # This code only runs locally for development
    
    # Safety check: Prevent Flask dev server in production
    if os.getenv("FLASK_ENV") == "production":
        logging.error("ERROR: Flask development server should not run in production!")
        logging.error("Use: gunicorn -w 2 --timeout 600 app:app")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv("PORT", 5000))
    print("TuttiBot Web API Ready - Flask Dev Server (LOCAL ONLY)")
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)

