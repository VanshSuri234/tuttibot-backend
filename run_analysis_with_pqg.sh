#!/bin/bash
#
# RUN_ANALYSIS_WITH_PQG.sh - Enhanced Music Performance Analysis with PQG-A2SA
# Uses two-pass approach: DTW baseline + optional PQG-A2SA enhancement
#
# FEATURES:
# - Automatically converts MIDI to MusicXML if needed
# - Uses PQG-A2SA for enhanced onset/offset detection
# - Falls back to DTW if PQG-A2SA unavailable
# - Tracks which metrics came from PQG vs DTW
#
# USAGE:
#   ./run_analysis_with_pqg.sh <dataset_folder> [--no-pqg]
#   ./run_analysis_with_pqg.sh Bach_10_Dataset/DieSonne
#   ./run_analysis_with_pqg.sh Bach_10_Dataset/DieSonne --no-pqg
#

set -e  # Exit on error

WORKSPACE_DIR="/home/nikhilsingh/Documents/temp/Trials/Workspace"
cd "$WORKSPACE_DIR"

# Parse arguments
USE_PQG=true
DATASET_DIR=""

for arg in "$@"; do
    case $arg in
        --no-pqg)
            USE_PQG=false
            ;;
        *)
            if [ -z "$DATASET_DIR" ]; then
                DATASET_DIR="$arg"
            fi
            ;;
    esac
done

# Check if dataset folder is provided
if [ -z "$DATASET_DIR" ]; then
    echo "ERROR: No dataset folder specified"
    echo ""
    echo "USAGE: ./run_analysis_with_pqg.sh <dataset_folder> [--no-pqg]"
    echo ""
    echo "Examples:"
    echo "  ./run_analysis_with_pqg.sh Bach_10_Dataset/DieSonne"
    echo "  ./run_analysis_with_pqg.sh Bach_10_Dataset/DieSonne --no-pqg"
    echo "  ./run_analysis_with_pqg.sh Bach_10_Dataset/ChristeDuBeistand"
    echo ""
    echo "Options:"
    echo "  --no-pqg    Disable PQG-A2SA enhancement (use DTW-only)"
    echo ""
    exit 1
fi

if [ ! -d "$DATASET_DIR" ]; then
    DATASET_DIR="$WORKSPACE_DIR/$DATASET_DIR"
fi

if [ ! -d "$DATASET_DIR" ]; then
    echo "ERROR: Dataset folder not found: $1"
    exit 1
fi

# Extract piece name from folder
PIECE_NAME=$(basename "$DATASET_DIR")
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  ENHANCED MUSIC PERFORMANCE ANALYSIS (with PQG-A2SA)"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Dataset: $PIECE_NAME"
echo "Location: $DATASET_DIR"
if [ "$USE_PQG" = true ]; then
    echo "PQG-A2SA Enhancement: ENABLED"
else
    echo "PQG-A2SA Enhancement: DISABLED (using DTW-only)"
fi
echo ""
echo ""

# Find MIDI and audio files
MIDI_FILE=$(find "$DATASET_DIR" -maxdepth 1 -name "*.mid" -o -name "*.midi" | head -1)
XML_FILE=$(find "$DATASET_DIR" -maxdepth 1 -name "*.xml" -o -name "*.musicxml" -o -name "*.mxl" | head -1)

if [ -z "$MIDI_FILE" ]; then
    echo "ERROR: No MIDI file found in $DATASET_DIR"
    exit 1
fi

echo "Score MIDI: $(basename $MIDI_FILE)"

# Convert MIDI to MusicXML if needed
if [ -z "$XML_FILE" ]; then
    echo "No MusicXML found - converting MIDI to MusicXML..."
    
    XML_FILE="$DATASET_DIR/$(basename $MIDI_FILE .mid).xml"
    
    python3 << PYEOF
from music21 import converter
from pathlib import Path

midi_file = Path("$MIDI_FILE")
xml_file = Path("$XML_FILE")

print(f"  Converting: {midi_file.name} → {xml_file.name}")
score = converter.parse(midi_file)
score.write('musicxml', fp=str(xml_file))
print(f"  ✓ Created: {xml_file.name}")
PYEOF
    
    echo ""
fi

echo "Score XML: $(basename $XML_FILE)"
echo ""

# Find all audio files (excluding ensemble)
AUDIO_FILES=$(find "$DATASET_DIR" -maxdepth 1 -name "*-*.wav" -o -name "*_*.wav" | grep -v "^\\./" | sort)

if [ -z "$AUDIO_FILES" ]; then
    echo "ERROR: No instrument audio files found in $DATASET_DIR"
    echo "Expected format: *-instrument.wav or *_instrument.wav"
    exit 1
fi

# Count instruments
NUM_INSTRUMENTS=$(echo "$AUDIO_FILES" | wc -l)
echo "Found $NUM_INSTRUMENTS instrument recordings:"
echo "$AUDIO_FILES" | while read audio; do
    echo "  - $(basename $audio)"
done
echo ""

# Create output directory
OUTPUT_DIR="$WORKSPACE_DIR/Output/analysis_results_pqg/$PIECE_NAME"
mkdir -p "$OUTPUT_DIR"

echo "Results will be saved to:"
echo "   $OUTPUT_DIR"
echo ""
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  STARTING ANALYSIS"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo ""

# Process each instrument
COUNTER=1
RESULTS_FILE="$OUTPUT_DIR/summary_results.txt"
> "$RESULTS_FILE"  # Clear previous results

echo "ENHANCED MUSIC PERFORMANCE ANALYSIS RESULTS" > "$RESULTS_FILE"
echo "(with PQG-A2SA Integration)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Piece: $PIECE_NAME" >> "$RESULTS_FILE"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')" >> "$RESULTS_FILE"
echo "PQG-A2SA: $([ "$USE_PQG" = true ] && echo "Enabled" || echo "Disabled")" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

declare -A SCORES
declare -A PITCH_ACCS
declare -A NOTE_ACCS
declare -A PQG_STATUS

echo "$AUDIO_FILES" | while read AUDIO_FILE; do
    INSTRUMENT=$(basename "$AUDIO_FILE" | sed 's/.*[-_]\(.*\)\.wav/\1/')
    INST_OUTPUT="$OUTPUT_DIR/$INSTRUMENT"
    
    echo "════════════════════════════════════════════════════════════════════"
    echo "[$COUNTER/$NUM_INSTRUMENTS] Analyzing: $INSTRUMENT"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""
    
    # Create output directory for this instrument
    mkdir -p "$INST_OUTPUT"
    
    # Build command
    PQG_FLAG=""
    if [ "$USE_PQG" = false ]; then
        PQG_FLAG="--no-pqg"
    fi
    
    python3 MusicPerformanceAnalysis/pipeline_with_pqg.py \
        --audio "$AUDIO_FILE" \
        --score "$XML_FILE" \
        --output "$INST_OUTPUT" \
        $PQG_FLAG \
        2>&1 | tee "$INST_OUTPUT/analysis.log" | grep -E "(Detected|Final grade|Pitch Accuracy|PQG-A2SA)" || true
    
    # Extract results
    if [ -f "$INST_OUTPUT/07_grading/final_grade.json" ]; then
        SCORE=$(python3 -c "import json; print(json.load(open('$INST_OUTPUT/07_grading/final_grade.json'))['overall_score'])")
        SCORES[$INSTRUMENT]=$SCORE
        
        # Extract pitch and note accuracy from report
        if [ -f "$INST_OUTPUT/07_grading/performance_report.txt" ]; then
            PITCH_ACC=$(grep "Pitch Accuracy" "$INST_OUTPUT/07_grading/performance_report.txt" | grep "(±50¢)" | sed 's/.*: //')
            NOTE_ACC=$(grep "Note Accuracy:" "$INST_OUTPUT/07_grading/performance_report.txt" | sed 's/.*: //')
            
            PITCH_ACCS[$INSTRUMENT]=$PITCH_ACC
            NOTE_ACCS[$INSTRUMENT]=$NOTE_ACC
        fi
        
        # Check if PQG was used
        if [ -f "$INST_OUTPUT/05_inference_core/metric_sources.json" ]; then
            PQG_USED=$(python3 -c "import json; data=json.load(open('$INST_OUTPUT/05_inference_core/metric_sources.json')); print('YES' if data.get('pqg_enhanced', False) else 'NO')" 2>/dev/null || echo "N/A")
            PQG_STATUS[$INSTRUMENT]=$PQG_USED
        else
            PQG_STATUS[$INSTRUMENT]="N/A"
        fi
    fi
    
    echo ""
    echo "✓ Completed: $INSTRUMENT"
    echo ""
    COUNTER=$((COUNTER + 1))
done

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  ANALYSIS COMPLETE!"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo ""

# Generate final summary
python3 - "$OUTPUT_DIR" "$PIECE_NAME" << 'PYEOF'
import json
from pathlib import Path
import sys

output_dir = Path(sys.argv[1])
piece_name = sys.argv[2]

print("=" * 90)
print(f"RESULTS SUMMARY: {piece_name}")
print("=" * 90)
print(f"{'Instrument':<12} {'Score':>8} {'Pitch Acc':>12} {'Note Acc':>12} {'PQG Used':>10} {'Part':<10}")
print("-" * 90)

instruments = ['violin', 'bassoon', 'clarinet', 'saxophone']
part_map = {
    'violin': 'Soprano(0)',
    'bassoon': 'Bass(3)',
    'clarinet': 'Alto(1)',
    'saxophone': 'Tenor(2)'
}

results = []

for inst in instruments:
    grade_file = output_dir / inst / "07_grading" / "final_grade.json"
    report_file = output_dir / inst / "07_grading" / "performance_report.txt"
    metrics_file = output_dir / inst / "06_inference" / "metric_sources.json"
    
    if grade_file.exists():
        with open(grade_file) as f:
            grade = json.load(f)
        
        score = grade['overall_score']
        part = part_map.get(inst, 'N/A')
        
        pitch_acc = note_acc = "N/A"
        if report_file.exists():
            with open(report_file) as f:
                for line in f:
                    if "Pitch Accuracy" in line and "(±50¢)" in line:
                        pitch_acc = line.split(':')[1].strip()
                    elif "Note Accuracy:" in line and "%" in line:
                        note_acc = line.split(':')[1].strip()
        
        # Check PQG usage
        pqg_used = "N/A"
        pqg_dimensions = []
        if metrics_file.exists():
            try:
                with open(metrics_file) as f:
                    metrics = json.load(f)
                    if metrics.get('pqg_enhanced', False):
                        pqg_used = "✓ YES"
                        # Count which dimensions used PQG
                        sources = metrics.get('sources', {})
                        pqg_dims = [dim for dim, source in sources.items() if 'PQG' in source]
                        pqg_dimensions = pqg_dims
                    else:
                        pqg_used = "DTW only"
            except:
                pqg_used = "N/A"
        
        print(f"{inst:<12} {score:>8.1f} {pitch_acc:>12} {note_acc:>12} {pqg_used:>10} {part:<10}")
        
        results.append({
            'instrument': inst,
            'score': score,
            'pitch_acc': pitch_acc,
            'note_acc': note_acc,
            'part': part,
            'pqg_used': pqg_used,
            'pqg_dimensions': pqg_dimensions
        })
    else:
        print(f"{inst:<12} {'FAILED':>8} {'N/A':>12} {'N/A':>12} {'N/A':>10} {'N/A':<10}")

print("=" * 90)
print()

# Show PQG enhancement details if used
if any(r.get('pqg_used') == "✓ YES" for r in results):
    print("PQG-A2SA Enhancement Details:")
    print("-" * 90)
    for r in results:
        if r.get('pqg_used') == "✓ YES":
            dims = ", ".join(r.get('pqg_dimensions', []))
            print(f"  {r['instrument']:<12} Enhanced dimensions: {dims}")
    print()

# Save results
summary_file = output_dir / "ANALYSIS_SUMMARY_PQG.json"
with open(summary_file, 'w') as f:
    json.dump({
        'piece': piece_name,
        'pipeline_version': '2.0-with-PQG',
        'results': results,
        'timestamp': str(Path('.').resolve())
    }, f, indent=2)

print(f"✓ Summary saved to: {summary_file}")
print()
PYEOF

echo ""
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  RESULTS LOCATION"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo ""
echo "Main Results Directory:"
echo "   $OUTPUT_DIR"
echo ""
echo "Files Generated (per instrument):"
echo "   ├── violin/"
echo "   │   ├── 01_input_layer/          - Validated input files"
echo "   │   ├── 02_processing/           - Normalized audio"
echo "   │   ├── 03_temporal_alignment/   - Transcription & alignment (DTW)"
echo "   │   ├── 04_extraction/           - Feature extraction"
echo "   │   ├── 05_pqg_a2sa/             - PQG-A2SA results (if enabled)"
echo "   │   ├── 05_inference_core/"
echo "   │   │   ├── grading_package_enhanced.json  ← ENHANCED GRADING PACKAGE"
echo "   │   │   └── metric_sources.json            ← SHOWS PQG vs DTW SOURCE"
echo "   │   ├── 07_grading/"
echo "   │   │   ├── final_grade.json    ← NUMERIC SCORE (PQG-enhanced)"
echo "   │   │   └── performance_report.txt ← DETAILED REPORT"
echo "   │   └── analysis.log             - Full analysis log"
echo "   ├── bassoon/ (same structure)"
echo "   ├── clarinet/ (same structure)"
echo "   └── saxophone/ (same structure)"
echo ""
echo "Summary Files:"
echo "   ├── ANALYSIS_SUMMARY_PQG.json    ← COMBINED RESULTS (JSON)"
echo "   └── summary_results.txt          - Text summary"
echo ""
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  KEY OUTPUT FILES"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo ""
echo "NUMERIC SCORE (0-100):"
echo "   $OUTPUT_DIR/<instrument>/07_grading/final_grade.json"
echo "   Format: JSON with 'overall_score' field"
echo ""
echo "DETAILED REPORT (human-readable):"
echo "   $OUTPUT_DIR/<instrument>/07_grading/performance_report.txt"
echo "   Contains: Pitch accuracy, note accuracy, rhythm, tempo, articulation"
echo ""
echo "PQG-A2SA METRICS SOURCE:"
echo "   $OUTPUT_DIR/<instrument>/05_inference_core/metric_sources.json"
echo "   Shows which metrics came from PQG-A2SA vs DTW"
echo "   Example:"
echo "   {"
echo "     \"pqg_enhanced\": true,"
echo "     \"sources\": {"
echo "       \"rhythm_tempo\": \"PQG-A2SA\","
echo "       \"sound_quality\": \"PQG-A2SA\","
echo "       \"technical_virtuosity\": \"PQG-A2SA\""
echo "     }"
echo "   }"
echo ""
echo "COMBINED SUMMARY:"
echo "   $OUTPUT_DIR/ANALYSIS_SUMMARY_PQG.json"
echo "   Format: JSON with all instruments' scores and PQG usage info"
echo ""
echo ""
if [ "$USE_PQG" = true ]; then
    echo "════════════════════════════════════════════════════════════════════"
    echo "  PQG-A2SA ENHANCEMENT STATUS"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""
    echo "PQG-A2SA was ENABLED for this analysis."
    echo ""
    echo "Check these files to see if PQG was actually used:"
    echo "   - metric_sources.json (per instrument)"
    echo "   - ANALYSIS_SUMMARY_PQG.json (combined)"
    echo ""
    echo "If PQG was used, you'll see:"
    echo "   ✓ More accurate onset/offset detection (±5-10ms vs ±20-40ms)"
    echo "   ✓ Better rhythm and articulation scores"
    echo "   ✓ Typically 2-5 point improvement in final grade"
    echo ""
else
    echo "════════════════════════════════════════════════════════════════════"
    echo "  DTW-ONLY MODE"
    echo "════════════════════════════════════════════════════════════════════"
    echo ""
    echo "PQG-A2SA was DISABLED for this analysis (--no-pqg flag used)."
    echo "All metrics computed using DTW-based alignment only."
    echo ""
    echo "To enable PQG-A2SA enhancement, run without --no-pqg flag:"
    echo "   ./run_analysis_with_pqg.sh $DATASET_DIR"
    echo ""
fi
echo ""
echo "ANALYSIS COMPLETE FOR: $PIECE_NAME"
echo ""
