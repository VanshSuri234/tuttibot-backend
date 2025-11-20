#!/bin/bash
#
# RUN_ANALYSIS.sh - Automated Music Performance Analysis
# Handles MIDI-only datasets (automatically converts MIDI to MusicXML)
#
# USAGE:
#   ./run_analysis.sh <dataset_folder>
#   ./run_analysis.sh Bach_10_Dataset/DieSonne
#

set -e  # Exit on error

WORKSPACE_DIR="/home/nikhilsingh/Documents/temp/Trials/Workspace"
cd "$WORKSPACE_DIR"

# Check if dataset folder is provided
if [ -z "$1" ]; then
    echo "ERROR: No dataset folder specified"
    echo ""
    echo "USAGE: ./run_analysis.sh <dataset_folder>"
    echo ""
    echo "Examples:"
    echo "  ./run_analysis.sh Bach_10_Dataset/DieSonne"
    echo "  ./run_analysis.sh Bach_10_Dataset/ChristeDuBeistand"
    echo "  ./run_analysis.sh Bach_10_Dataset/DieNacht"
    echo ""
    exit 1
fi

DATASET_DIR="$1"
if [ ! -d "$DATASET_DIR" ]; then
    DATASET_DIR="$WORKSPACE_DIR/$1"
fi

if [ ! -d "$DATASET_DIR" ]; then
    echo "ERROR: Dataset folder not found: $1"
    exit 1
fi

# Extract piece name from folder
PIECE_NAME=$(basename "$DATASET_DIR")
echo ""
echo "  MUSIC PERFORMANCE ANALYSIS"
echo ""
echo "Dataset: $PIECE_NAME"
echo "Location: $DATASET_DIR"
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
OUTPUT_DIR="$WORKSPACE_DIR/Output/analysis_results/$PIECE_NAME"
mkdir -p "$OUTPUT_DIR"

echo "Results will be saved to:"
echo "   $OUTPUT_DIR"
echo ""
echo ""
echo "  STARTING ANALYSIS"
echo ""
echo ""

# Process each instrument
COUNTER=1
RESULTS_FILE="$OUTPUT_DIR/summary_results.txt"
> "$RESULTS_FILE"  # Clear previous results

echo "MUSIC PERFORMANCE ANALYSIS RESULTS" > "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Piece: $PIECE_NAME" >> "$RESULTS_FILE"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

declare -A SCORES
declare -A PITCH_ACCS
declare -A NOTE_ACCS

echo "$AUDIO_FILES" | while read AUDIO_FILE; do
    INSTRUMENT=$(basename "$AUDIO_FILE" | sed 's/.*[-_]\(.*\)\.wav/\1/')
    INST_OUTPUT="$OUTPUT_DIR/$INSTRUMENT"
    
    echo "[$COUNTER/$NUM_INSTRUMENTS] Analyzing: $INSTRUMENT"
    echo ""
    
    python3 MusicPerformanceAnalysis/pipeline.py \
        --audio "$AUDIO_FILE" \
        --score "$XML_FILE" \
        --output "$INST_OUTPUT" \
        2>&1 | tee "$INST_OUTPUT/analysis.log" | grep -E "(Detected|Final grade|Pitch Accuracy)" || true
    
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
    fi
    
    echo ""
    COUNTER=$((COUNTER + 1))
done

echo ""
echo "  ANALYSIS COMPLETE!"
echo ""
echo ""

# Generate final summary
python3 << 'PYEOF'
import json
from pathlib import Path
import sys

output_dir = Path(sys.argv[1])
piece_name = sys.argv[2]

print("=" * 80)
print(f"RESULTS SUMMARY: {piece_name}")
print("=" * 80)
print(f"{'Instrument':<12} {'Score':>8} {'Pitch Acc':>12} {'Note Acc':>12} {'Part':<10}")
print("-" * 80)

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
        
        print(f"{inst:<12} {score:>8.1f} {pitch_acc:>12} {note_acc:>12} {part:<10}")
        results.append({
            'instrument': inst,
            'score': score,
            'pitch_acc': pitch_acc,
            'note_acc': note_acc,
            'part': part
        })
    else:
        print(f"{inst:<12} {'FAILED':>8} {'N/A':>12} {'N/A':>12} {'N/A':<10}")

print("=" * 80)
print()

# Save results
summary_file = output_dir / "ANALYSIS_SUMMARY.json"
with open(summary_file, 'w') as f:
    json.dump({
        'piece': piece_name,
        'results': results,
        'timestamp': str(Path('.').resolve())
    }, f, indent=2)

print(f"✓ Summary saved to: {summary_file}")

PYEOF "$OUTPUT_DIR" "$PIECE_NAME"

echo ""
echo ""
echo "  RESULTS LOCATION"
echo ""
echo ""
echo "Main Results Directory:"
echo "   $OUTPUT_DIR"
echo ""
echo "Files Generated (per instrument):"
echo "   ├── violin/"
echo "   │   ├── 01_input_layer/          - Validated input files"
echo "   │   ├── 02_processing/           - Normalized audio"
echo "   │   ├── 03_temporal_alignment/   - Transcription & alignment"
echo "   │   ├── 04_extraction/           - Feature extraction"
echo "   │   ├── 06_inference/            - Grading metrics"
echo "   │   ├── 07_grading/"
echo "   │   │   ├── final_grade.json    NUMERIC SCORE"
echo "   │   │   └── performance_report.txt DETAILED REPORT"
echo "   │   └── analysis.log             - Full analysis log"
echo "   ├── bassoon/ (same structure)"
echo "   ├── clarinet/ (same structure)"
echo "   └── saxophone/ (same structure)"
echo ""
echo "Summary Files:"
echo "   ├── ANALYSIS_SUMMARY.json        COMBINED RESULTS (JSON)"
echo "   └── summary_results.txt          - Text summary"
echo ""
echo ""
echo "  KEY OUTPUT FILES"
echo ""
echo ""
echo "For each instrument, check these files for results:"
echo ""
echo "NUMERIC SCORE (0-100):"
echo "   $OUTPUT_DIR/<instrument>/07_grading/final_grade.json"
echo "   Format: JSON with 'overall_score' field"
echo ""
echo "DETAILED REPORT (human-readable):"
echo "   $OUTPUT_DIR/<instrument>/07_grading/performance_report.txt"
echo "   Contains: Pitch accuracy, note accuracy, rhythm, tempo, articulation"
echo ""
echo "COMBINED SUMMARY:"
echo "   $OUTPUT_DIR/ANALYSIS_SUMMARY.json"
echo "   Format: JSON with all instruments' scores"
echo ""
echo ""
echo "ANALYSIS COMPLETE FOR: $PIECE_NAME"
echo ""