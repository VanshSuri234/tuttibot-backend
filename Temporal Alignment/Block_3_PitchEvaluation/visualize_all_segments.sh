#!/bin/bash

# Generate musician-friendly visualizations for all evaluated segments
# Usage: ./visualize_all_segments.sh

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "======================================"
echo "Generating Musician-Friendly Visualizations"
echo "======================================"
echo ""

# Find all evaluation directories in Data_Pitch/pitch_results_movement1
MOVEMENT1_DIR="../../Data_Pitch/pitch_results_movement1"

if [ ! -d "$MOVEMENT1_DIR" ]; then
    echo "Error: Movement1 results directory not found at $MOVEMENT1_DIR"
    exit 1
fi

# Find all evaluation directories
EVAL_DIRS=()
for segment_dir in "$MOVEMENT1_DIR"/segment*/; do
    if [ -d "$segment_dir" ]; then
        for eval_dir in "$segment_dir"pitch_evaluation_*/; do
            if [ -d "$eval_dir" ]; then
                EVAL_DIRS+=("$eval_dir")
            fi
        done
    fi
done

total=${#EVAL_DIRS[@]}

if [ $total -eq 0 ]; then
    echo "Error: No evaluation results found"
    exit 1
fi

echo "Found $total evaluations"
echo ""

# Process each evaluation
count=0
for eval_dir in "${EVAL_DIRS[@]}"; do
    count=$((count + 1))
    eval_name=$(echo "$eval_dir" | sed 's|/$||')
    
    echo "[$count/$total] Processing: $eval_name"
    
    # Check if data exists
    if [ ! -f "$eval_dir/data/comparison_results.json" ]; then
        echo "  ⚠ Skipping - no comparison data found"
        continue
    fi
    
    # Generate visualizations
    python3 musician_visualizer.py "$eval_dir" 2>&1 | grep -E "(Saved|visualizations saved|Error)" || true
    
    echo "  ✓ Done"
    echo ""
done

echo ""
echo "======================================"
echo "Visualization Complete!"
echo "======================================"
echo ""
echo "Results saved in:"
echo "  $MOVEMENT1_DIR/segment*/pitch_evaluation_*/musician_visualizations/"
echo ""
echo "Each evaluation now has 4 musician-friendly plots:"
echo "  1. pitch_over_time.png      - Note names on Y-axis"
echo "  2. note_errors.png           - Bar chart of individual note errors"
echo "  3. accuracy_summary.png      - Overall performance summary"
echo "  4. error_distribution.png    - Histogram of pitch errors"
echo ""
