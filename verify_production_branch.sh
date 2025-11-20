#!/bin/bash

# Production Branch Verification Script
# Run this after pushing to verify the production branch is complete

echo "Verifying production branch setup..."
echo ""

# Check if we're on production branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "production" ]; then
    echo "Warning: Not on production branch (currently on $CURRENT_BRANCH)"
    echo "Switch to production branch first: git checkout production"
    exit 1
fi

echo "Current branch: $CURRENT_BRANCH"
echo ""

# Verify essential files exist
echo "Checking essential files..."
MISSING_FILES=0

check_file() {
    if [ ! -f "$1" ]; then
        echo "  MISSING: $1"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "  OK: $1"
    fi
}

check_dir() {
    if [ ! -d "$1" ]; then
        echo "  MISSING DIR: $1"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "  OK: $1/"
    fi
}

# Core files
echo ""
echo "Core pipeline files:"
check_file "MusicPerformanceAnalysis/pipeline.py"
check_file "MusicPerformanceAnalysis/pipeline_with_pqg.py"
check_file "MusicPerformanceAnalysis/__init__.py"

# Execution scripts
echo ""
echo "Execution scripts:"
check_file "run_analysis.sh"
check_file "run_analysis_with_pqg.sh"
check_file "batch_process_instrument.sh"

# Documentation
echo ""
echo "Documentation files:"
check_file "README.md"
check_file "requirements.txt"
check_file "run_help.txt"
check_file "ESSENTIAL_FILES_FOR_PRODUCTION.txt"
check_file "PRODUCTION_BRANCH_GUIDE.txt"

# Configuration
echo ""
echo "Configuration:"
check_file ".gitignore"

# Test dataset
echo ""
echo "Test dataset:"
check_dir "Bach_10_Dataset"
if [ -d "Bach_10_Dataset" ]; then
    SONG_COUNT=$(find Bach_10_Dataset -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo "  Found $SONG_COUNT songs in Bach_10_Dataset"
fi

# Layer modules
echo ""
echo "Layer modules:"
check_dir "MusicPerformanceAnalysis/INPUT3_LAYER"
check_dir "MusicPerformanceAnalysis/PROCESSING_LAYER"
check_dir "MusicPerformanceAnalysis/TEMPORAL_ALIGNMENT"
check_dir "MusicPerformanceAnalysis/EXTRACTION_LAYER"
check_dir "MusicPerformanceAnalysis/PQG_A2SA"
check_dir "MusicPerformanceAnalysis/INFERENCE_CORE"
check_dir "MusicPerformanceAnalysis/GRADING"

# Check for files that should NOT be in production
echo ""
echo "Checking for development-only files (should be absent)..."
UNWANTED_FILES=0

check_absent() {
    if [ -f "$1" ] || [ -d "$1" ]; then
        echo "  SHOULD BE REMOVED: $1"
        UNWANTED_FILES=$((UNWANTED_FILES + 1))
    fi
}

check_absent "Output"
check_absent "deploy_original_system.sh"
check_absent "deploy_python310.sh"
check_absent "docker_setup.sh"
check_absent "Dockerfile.txt"
check_absent "gpu_manager.py"
check_absent "hpc_compatibility_check.py"

# Count development docs
DEV_DOCS=$(ls COMPLETE_*.md CURRENT_STATUS_*.md IMPLEMENTATION_*.md 2>/dev/null | wc -l)
if [ "$DEV_DOCS" -gt 0 ]; then
    echo "  SHOULD BE REMOVED: $DEV_DOCS development documentation files"
    UNWANTED_FILES=$((UNWANTED_FILES + DEV_DOCS))
fi

# Summary
echo ""
echo "Verification Summary:"
echo "  Missing essential files: $MISSING_FILES"
echo "  Unwanted files present: $UNWANTED_FILES"

if [ $MISSING_FILES -eq 0 ] && [ $UNWANTED_FILES -eq 0 ]; then
    echo ""
    echo "SUCCESS: Production branch is complete and clean!"
    echo ""
    echo "You can now push to remote:"
    echo "  git push origin production"
elif [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "ERROR: Missing essential files. Run setup_production_branch.sh again."
    exit 1
elif [ $UNWANTED_FILES -gt 0 ]; then
    echo ""
    echo "WARNING: Development files still present. Clean them up before pushing."
    exit 1
fi

# Test if pipeline can be imported
echo ""
echo "Testing Python imports..."
python3 -c "import sys; sys.path.insert(0, '.'); from MusicPerformanceAnalysis import pipeline" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  OK: Pipeline module imports successfully"
else
    echo "  WARNING: Pipeline module import failed (check dependencies)"
fi

echo ""
echo "Verification complete!"
