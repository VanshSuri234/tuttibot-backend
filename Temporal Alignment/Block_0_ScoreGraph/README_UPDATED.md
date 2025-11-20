# Block 0: ScoreGraph with DAG Edge Structure

## What This Does

This module parses a MusicXML score file and creates a structured representation (ScoreGraph) that captures the musical timeline, beat positions, fermatas, cadences, and note information. The ScoreGraph serves as the reference structure for all downstream alignment and analysis.

## Key Improvements

### DAG Edge Structure
Each beat node now includes an `edges` field that points to the next beat(s) in the musical sequence. This creates a Directed Acyclic Graph (DAG) that represents the linear flow of time through the score.

Currently, edges are simple linear pointers (each beat → next beat), but this structure supports future extensions like:
- Multiple paths for repeat sections
- Alternative endings
- Da capo / dal segno jumps

## Input

Required:
- `--score`: Path to MusicXML file (.xml or .mxl)
- `--meta`: Path to metadata JSON with tempo, key, fermatas

Optional:
- `--seg`: Path to segmentation JSON with cadence positions

### Metadata Format
```json
{
  "tempo_marks": [{"beat": 0, "bpm": 120}],
  "key_signature": "C major",
  "meter": "4/4",
  "tuning_hz": 440,
  "fermatas": ["8_2", "16_4"]
}
```

## Output

A comprehensive ScoreGraph JSON containing:

### 1. Bars
Each measure with time signature and downbeat position:
```json
{
  "bar": 1,
  "time_sig": "4/4",
  "downbeat_abs_beat": 0.0
}
```

### 2. Nodes (Beat Grid)
Each beat in the score with edges to next beat:
```json
{
  "id": "1_1",
  "bar": 1,
  "beat": 1,
  "abs_beat": 0.0,
  "D_beats": 1.0,
  "flags": ["fermata"],
  "edges": ["1_2"]
}
```

### 3. Musical Notes
All notes with MIDI pitch and timing:
```json
{
  "type": "note",
  "pitch": 60,
  "pitch_name": "C4",
  "offset_beats": 0.5,
  "offset_seconds": 0.25,
  "duration_beats": 1.0,
  "duration_seconds": 0.5,
  "velocity": 64
}
```

### 4. Metadata and Mappings
- Total measures, notes count
- Bar/beat ↔ absolute beat conversion maps
- Tempo marks
- Key signature and tuning

## How to Use

Basic usage:
```bash
python build_scoregraph_with_repeats.py --score score.musicxml --meta score_meta.json
```

With segmentation (for cadences):
```bash
python build_scoregraph_with_repeats.py --score score.musicxml --meta score_meta.json --seg segmentation.json
```

Output file: `scoregraph.json`

## How It Works

1. Parse MusicXML file using music21 library
2. Expand all repeat signs (D.C., D.S., repeat bars) into linear sequence
3. Extract time signatures for each measure
4. Create beat nodes for each beat position in each measure
5. Attach fermata and cadence flags from metadata
6. Add edges: each beat points to the next beat in sequence
7. Extract all musical notes with MIDI pitch and timing
8. Create mapping tables for easy lookup

## Repeat Expansion

The system uses music21's `expandRepeats()` to unroll all repeat structures. For example, if a score has:
```
||: A :|| B
```

The expanded ScoreGraph will contain:
```
A, A, B
```

This ensures the ScoreGraph represents the actual performed sequence without requiring complex jump logic during alignment.

## Edge Structure Details

Currently, edges form a simple linear chain:
```
1_1 → 1_2 → 1_3 → 1_4 → 2_1 → 2_2 → ...
```

Each beat has exactly one outgoing edge (except the final beat, which has none).

The `edges` field is an array to support future extensions where a node might have multiple possible next nodes (e.g., first/second endings in repeats).

## For Musicians

Think of this as converting the sheet music into a numbered timeline where:
- Each beat gets a unique ID (e.g., "measure 3, beat 2" becomes "3_2")
- Fermatas and cadences are marked
- Every note is listed with its exact timing
- The system knows which beat comes after which beat

This structured format makes it easy for the computer to follow the music the same way a musician reads the score left-to-right, top-to-bottom.

## What Changed from Original

The original version created beat nodes but did not connect them. The updated version:
- Adds `edges` field to each node
- Populates edges after all nodes are created
- Creates a DAG structure ready for context-aware alignment

This enables future algorithms to:
- Walk through the score graph beat-by-beat
- Check neighboring beats when making alignment decisions
- Understand musical context (what comes before/after)
