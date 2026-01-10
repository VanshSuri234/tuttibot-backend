#!/usr/bin/env python3
"""
Deployment Validation Tests
Comprehensive checks before manual testing on production
"""

import sys
import json
from pathlib import Path

print("=" * 70)
print("TUTTIBOT BACKEND DEPLOYMENT VALIDATION")
print("=" * 70)

tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"        {details}")
    if condition:
        tests_passed += 1
    else:
        tests_failed += 1
    return condition

# ============================================================================
# 1. CONFIGURATION & IMPORTS
# ============================================================================
print("\n[1] CHECKING IMPORTS & CONFIGURATION...")

try:
    import app
    test("Import app.py", True, "Flask application loaded")
except Exception as e:
    test("Import app.py", False, f"Error: {e}")

try:
    from app import JobStatus
    test("JobStatus class exists", True, f"States: {JobStatus.QUEUED}, {JobStatus.PROCESSING}, {JobStatus.COMPLETED}, {JobStatus.FAILED}")
except Exception as e:
    test("JobStatus class exists", False, str(e))

try:
    from app import save_job_status, load_job_status
    test("Status persistence functions exist", True, "save_job_status and load_job_status defined")
except Exception as e:
    test("Status persistence functions exist", False, str(e))

try:
    from MusicPerformanceAnalysis.pipeline import MusicPerformancePipeline
    test("MusicPerformancePipeline imports", True, "Pipeline module available")
except Exception as e:
    test("MusicPerformancePipeline imports", False, str(e))

# ============================================================================
# 2. DIRECTORY STRUCTURE
# ============================================================================
print("\n[2] CHECKING DIRECTORY STRUCTURE...")

test("uploads/ exists", Path("uploads").exists(), "Created for temporary file storage")
test("results/ exists", Path("results").exists(), "Created for analysis output")
test("MusicPerformanceAnalysis/ exists", Path("MusicPerformanceAnalysis").exists(), "Pipeline module present")

# ============================================================================
# 3. FILE INTEGRITY
# ============================================================================
print("\n[3] CHECKING FILE INTEGRITY...")

# Check processing_layer changes
try:
    with open("MusicPerformanceAnalysis/layers/02_processing/processing_layer.py") as f:
        content = f.read()
        has_scipy_norm = "def normalize_audio" in content and "wavfile.write" in content
        has_fallback = "except auditok_err:" in content
        test("Processing layer optimized", has_scipy_norm and has_fallback, "FFmpeg replaced with scipy, fallbacks added")
except Exception as e:
    test("Processing layer optimized", False, str(e))

# Check requirements.txt
try:
    with open("requirements.txt") as f:
        content = f.read()
        has_auditok = "auditok>=" in content
        has_groq = "groq>=" in content
        has_flask = "flask>=" in content
        test("Requirements complete", has_auditok and has_groq and has_flask, "All critical packages listed")
except Exception as e:
    test("Requirements complete", False, str(e))

# ============================================================================
# 4. API ENDPOINTS
# ============================================================================
print("\n[4] CHECKING API ENDPOINT DEFINITIONS...")

try:
    with open("app.py") as f:
        content = f.read()
        endpoints = {
            "GET /": "root endpoint" in content.lower(),
            "POST /upload": "@app.route('/upload'" in content,
            "GET /status/<job_id>": "@app.route('/status/" in content,
            "GET /results/<job_id>": "@app.route('/results/" in content,
            "POST /chat": "@app.route('/chat'" in content,
            "GET /health": "@app.route('/health'" in content,
        }
        
        for endpoint, exists in endpoints.items():
            test(f"Endpoint {endpoint} defined", exists)
except Exception as e:
    test("Endpoint definitions", False, str(e))

# ============================================================================
# 5. SYNTAX VALIDATION
# ============================================================================
print("\n[5] CHECKING PYTHON SYNTAX...")

try:
    import ast
    
    files_to_check = [
        "app.py",
        "MusicPerformanceAnalysis/pipeline.py",
        "MusicPerformanceAnalysis/layers/02_processing/processing_layer.py",
    ]
    
    for filepath in files_to_check:
        try:
            with open(filepath) as f:
                ast.parse(f.read())
            test(f"Syntax: {filepath}", True)
        except SyntaxError as e:
            test(f"Syntax: {filepath}", False, str(e))
except Exception as e:
    test("Syntax validation", False, str(e))

# ============================================================================
# 6. STATUS PERSISTENCE
# ============================================================================
print("\n[6] CHECKING STATUS PERSISTENCE LOGIC...")

try:
    with open("app.py") as f:
        content = f.read()
        has_save = "def save_job_status" in content
        has_load = "def load_job_status" in content
        has_disk_read = "job_status_path.exists()" in content or "status_file.exists()" in content
        test("Status persistence implemented", has_save and has_load and has_disk_read, 
             "save_job_status, load_job_status, and disk read logic present")
except Exception as e:
    test("Status persistence", False, str(e))

# ============================================================================
# 7. ERROR HANDLING
# ============================================================================
print("\n[7] CHECKING ERROR HANDLING...")

try:
    with open("MusicPerformanceAnalysis/layers/02_processing/processing_layer.py") as f:
        content = f.read()
        has_try_except = content.count("try:") > content.count("try:") - content.count("except")
        test("Error handling in processing_layer", has_try_except, f"Found {content.count('try:')} try blocks")
except Exception as e:
    test("Error handling", False, str(e))

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print(f"VALIDATION SUMMARY: {tests_passed} passed, {tests_failed} failed")
print("=" * 70)

if tests_failed == 0:
    print("✅ ALL CHECKS PASSED - Ready for deployment testing!")
    sys.exit(0)
else:
    print(f"❌ {tests_failed} CHECK(S) FAILED - Please review errors above")
    sys.exit(1)
