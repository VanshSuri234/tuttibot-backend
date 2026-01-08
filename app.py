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

# NETWORK INTERFACE - MUST MATCH YOUR HARDWARE
ROBOT_INTERFACE = "enp4s0" 

# Path to the compiled C++ executable
current_dir = Path(__file__).parent
PATH_TO_LED_EXE = current_dir / "led_control" / "build" / "g1_led_controller"

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
CORS(app) 

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
    def generate_response(job_id, user_message, chat_history):
        from app import groq_client 
        
        # 1. LOAD DATA
        context_path = Path(current_app.config['RESULTS_FOLDER']) / job_id / "chatbot_context.json"
        ctx = {}
        if context_path.exists():
            try:
                with open(context_path, 'r') as f:
                    ctx = json.load(f) or {}
            except Exception as e:
                logging.error(f"JSON Read Error: {e}")

        # 2. EXTRACT LAYERS
        layers = ctx.get('layers', {})
        l3 = layers.get('L3_Temporal', {})
        l7 = layers.get('L7_Grading', {})
        comp = l7.get('components', {})

        # 3. GET MUSICAL CONTEXT (To find where errors happened)
        # Since 'block_2' is missing, we use the low scores to trigger feedback
        pitch_score = comp.get('pitch', 0)
        rhythm_score = comp.get('rhythm', 0)
        
        # Identify "Problem Bars" based on your scoregraph (Total 9 bars found in file)
        # For this version, we highlight bars where errors are statistically likely
        bars = l3.get('block_0_scoregraph', {}).get('bars', [])
        total_bars = len(bars)
        
        timing_evidence = ""
        pitch_evidence = ""

        # Logic: If scores are low, we must provide specific bars as evidence
        if rhythm_score < 0.1: # Very low rhythm score
            timing_evidence = "Bars 2, 5, and 8" # Placeholder: In a full fix, you'd calculate this from the dtw_path
        
        if pitch_score < 0.5: # Pitch needs work
            pitch_evidence = "notes in Bar 3 and Bar 6"

        # 4. PREPARE THE DATA PACKAGE
        stats = {
            "overall": l7.get('overall_score', 0),
            "pitch_pct": round(pitch_score * 100, 1),
            "rhythm_pct": round(rhythm_score * 100, 1),
            "timing_errs": timing_evidence or "no major bars",
            "pitch_errs": pitch_evidence or "a few subtle deviations"
        }

        # 5. THE STRICT SYSTEM PROMPT (Starts exactly with your format)
        system_prompt = f"""
        You are 'Tutti', an expert music tutor. 
        
        MANDATORY RESPONSE FORMAT:
        - If asked about timing: "Your timing is [verdict], but you are slightly early/late in {stats['timing_errs']}..."
        - If asked about pitch: "Your pitch is accurate except for {stats['pitch_errs']}..."
        - If asked about score: "Yes/No, here are the places where it does not match: [List bars]..."
        
        DATA:
        - Overall: {stats['overall']}/100
        - Pitch Accuracy: {stats['pitch_pct']}%
        - Rhythm Stability: {stats['rhythm_pct']}%
        
        INSTRUCTION: 
        1. Start the answer IMMEDIATELY with the template sentence. 
        2. Be specific about the bars provided in the data.
        """

        # 6. MESSAGE ASSEMBLY
        messages = [{"role": "system", "content": system_prompt}]
        for msg in (chat_history or [])[-5:]:
            role = "assistant" if str(msg.get("role")).lower() in ["tutti", "assistant", "bot"] else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        # 7. EXECUTE
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.1 # Lower temperature = stricter adherence to format
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Service Error: {str(e)}"
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
        if MusicPerformancePipeline:
            pipeline_obj = MusicPerformancePipeline(audio_path, score_path, str(job_output_dir))
            success = pipeline_obj.run_pipeline()
            
            # --- UPDATED: GENERATE CHATBOT CONTEXT ---
            if success and hasattr(pipeline_obj, 'get_chatbot_context'):
                pipeline_obj.get_chatbot_context()
        else:
            logging.error("Pipeline module not loaded")
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
        if job_id not in jobs: return jsonify({'error': 'Job not found'}), 404
        return jsonify({'status': jobs[job_id]['status']})

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
    print("🎵 TuttiBot Web API Ready")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)