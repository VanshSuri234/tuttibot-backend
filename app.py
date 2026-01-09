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
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS

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
    with job_lock:
        jobs[job_id]['status'] = JobStatus.PROCESSING
        jobs[job_id]['started_at'] = datetime.now().isoformat()
    
    try:
        job_output_dir = Path(app.config['RESULTS_FOLDER']) / job_id
        job_output_dir.mkdir(exist_ok=True)

        # 1. RUN PIPELINE
        success = False
        try:
            if MusicPerformancePipeline:
                logging.info(f"Starting pipeline for job {job_id}")
                pipeline_obj = MusicPerformancePipeline(audio_path, score_path, str(job_output_dir))
                success = pipeline_obj.run_pipeline()
                logging.info(f"Pipeline completed for job {job_id}: success={success}")
                
                # --- UPDATED: GENERATE CHATBOT CONTEXT ---
                if success and hasattr(pipeline_obj, 'get_chatbot_context'):
                    pipeline_obj.get_chatbot_context()
            else:
                logging.error("Pipeline module not loaded - MusicPerformancePipeline is None")
                success = False
        except Exception as e:
            logging.error(f"Pipeline error for job {job_id}: {str(e)}", exc_info=True)
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
        
        if llm_service:
            llm_response = llm_service.initialize_analysis(job_id, json.dumps(summary_data, indent=2), report_text)
            with job_lock:
                jobs[job_id]['llm_initial_analysis'] = llm_response

    except Exception as e:
        with job_lock:
            jobs[job_id]['status'] = JobStatus.FAILED
            jobs[job_id]['error'] = str(e)
        logging.exception(f"Analysis failed for job {job_id}")

# ==========================================
# ROUTES (ALL ORIGINAL ROUTES PRESERVED)
# ==========================================

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

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_ENV", "development") != "production"
    print("TuttiBot Web API Ready")
    app.run(host="0.0.0.0", port=port, debug=debug_mode, threaded=True)

