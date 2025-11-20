#!/bin/bash

# Production Branch Setup Script
# This script creates a clean production branch with only necessary files

echo "Creating production branch for Music Performance Analysis..."
echo ""

# Create and switch to production branch
echo "Step 1: Creating production branch..."
git checkout -b production

# Add core pipeline files
echo "Step 2: Adding core pipeline files..."
git add MusicPerformanceAnalysis/pipeline.py
git add MusicPerformanceAnalysis/pipeline_with_pqg.py
git add MusicPerformanceAnalysis/__init__.py

# Add all layer modules
echo "Step 3: Adding layer modules..."
git add MusicPerformanceAnalysis/INPUT3_LAYER/
git add MusicPerformanceAnalysis/PROCESSING_LAYER/
git add MusicPerformanceAnalysis/TEMPORAL_ALIGNMENT/
git add MusicPerformanceAnalysis/EXTRACTION_LAYER/
git add MusicPerformanceAnalysis/PQG_A2SA/
git add MusicPerformanceAnalysis/INFERENCE_CORE/
git add MusicPerformanceAnalysis/GRADING/

# Add execution scripts
echo "Step 4: Adding execution scripts..."
git add run_analysis.sh
git add run_analysis_with_pqg.sh
git add batch_process_instrument.sh
git add generate_all_instruments_comparison.py
git add evaluate_tuttibotv02.py

# Add comparison and evaluation scripts
echo "Step 5: Adding comparison/evaluation scripts..."
git add compare_*.py

# Add test dataset
echo "Step 6: Adding Bach_10_Dataset..."
git add Bach_10_Dataset/

# Add documentation
echo "Step 7: Adding documentation..."
git add README.md
git add requirements.txt
git add run_help.txt
git add ESSENTIAL_FILES_FOR_PRODUCTION.txt
git add PRODUCTION_BRANCH_GUIDE.txt

# Create docs directory and add selected documentation
echo "Step 8: Organizing documentation..."
mkdir -p docs
git add docs/LAYER_ARCHITECTURE_AND_GRADING_FORMULAS.txt 2>/dev/null || true
git add docs/PQG_INTEGRATION_SUCCESS.md 2>/dev/null || true
git add docs/DieSonne_PQG_Results_Summary.txt 2>/dev/null || true
git add docs/LLM_FEEDBACK_DATA_REQUIREMENTS.txt 2>/dev/null || true

# Add configuration files
echo "Step 9: Adding configuration files..."
git add .gitignore

# Remove development-only documentation
echo "Step 10: Removing development documentation..."
git rm --cached COMPLETE_*.md 2>/dev/null || true
git rm --cached CURRENT_STATUS_*.md 2>/dev/null || true
git rm --cached IMPLEMENTATION_*.md 2>/dev/null || true
git rm --cached ARCHITECTURE_GAP_*.md 2>/dev/null || true
git rm --cached BLOCK_0_*.md 2>/dev/null || true
git rm --cached CONSOLIDATION_*.md 2>/dev/null || true
git rm --cached CONTEXT_ALIGNMENT_*.md 2>/dev/null || true
git rm --cached DEPENDENCY_*.md 2>/dev/null || true
git rm --cached DTW_*.md 2>/dev/null || true
git rm --cached ENHANCED_*.md 2>/dev/null || true
git rm --cached EVALUATION_*.md 2>/dev/null || true
git rm --cached FINAL_*.md 2>/dev/null || true
git rm --cached GRADING_IMPLEMENTATION_*.md 2>/dev/null || true
git rm --cached GRADING_SYSTEM_*.md 2>/dev/null || true
git rm --cached HANDOFF_*.md 2>/dev/null || true
git rm --cached HYBRID_*.md 2>/dev/null || true
git rm --cached INFERENCE_CORE_*.md 2>/dev/null || true
git rm --cached GPU_*.md 2>/dev/null || true
git rm --cached CROSS_*.md 2>/dev/null || true

# Remove temporary scripts
echo "Step 11: Removing temporary/development scripts..."
git rm --cached deploy_*.sh 2>/dev/null || true
git rm --cached docker_*.sh 2>/dev/null || true
git rm --cached install_*.sh 2>/dev/null || true
git rm --cached Dockerfile.txt 2>/dev/null || true
git rm --cached gpu_manager.py 2>/dev/null || true
git rm --cached hpc_compatibility_check.py 2>/dev/null || true

# Remove unnecessary dependency files (created during development)
echo "Step 12: Removing development artifacts..."
git rm --cached "=*" 2>/dev/null || true

# Check status
echo ""
echo "Step 13: Checking git status..."
git status

echo ""
echo "Production branch prepared!"
echo ""
echo "Next steps:"
echo "1. Review the git status output above"
echo "2. If everything looks correct, commit:"
echo "   git commit -m 'Production release with PQG-A2SA integration'"
echo "3. Push to remote:"
echo "   git push origin production"
echo ""
echo "To verify before pushing:"
echo "  git log --oneline -5"
echo "  git diff --name-status main..production"
