# Block 0 — Build the ScoreGraph (Unified Version)

This module provides three different methods to parse MusicXML/MIDI and create a canonical, linearized score timeline with bars, beats, and node durations. The output is `scoregraph.json`.

## Available Methods

### 1. Simple Method (default)
- **Dependencies**: None (uses only Python standard library)
- **Input**: MusicXML files only
- **Advantages**: No external dependencies, fast, reliable
- **Disadvantages**: Basic parsing, no repeat expansion

### 2. Music21 Method (recommended)
- **Dependencies**: `music21` library
- **Input**: MusicXML, MIDI, and many other formats
- **Advantages**: Professional-grade parsing, handles complex notation, repeat expansion
- **Disadvantages**: Requires external library

### 3. Pretty-MIDI Method
- **Dependencies**: `pretty_midi` library  
- **Input**: MIDI files only
- **Advantages**: Fast MIDI processing, beat tracking
- **Disadvantages**: MIDI only, different beat interpretation

## Installation

```bash
# For music21 method
pip install music21

# For pretty_midi method  
pip install pretty_midi

# Or install all dependencies
pip install -r requirements_unified.txt
```

## Usage

```bash
# Using simple method (default, no dependencies)
python build_scoregraph_unified.py --score score.musicxml --meta score_meta.json

# Using music21 method (recommended for MusicXML)
python build_scoregraph_unified.py --score score.musicxml --meta score_meta.json --method music21

# Using pretty_midi method (for MIDI files)
python build_scoregraph_unified.py --score score.mid --meta score_meta.json --method prettymidi

# With optional segmentation
python build_scoregraph_unified.py --score score.musicxml --meta score_meta.json --seg segmentation.json --method music21
```

## Input Files

### score_meta.json
```json
{
  "meter": "4/4",
  "key_signature": "C", 
  "tuning_hz": 440,
  "tempo_marks": [
    {"beat": 0, "bpm": 120}
  ],
  "fermatas": [],
  "cadences": []
}
```

### segmentation.json (optional)
```json
{
  "cadences": ["5_4", "10_2"],
  "sections": ["1_1", "20_1", "40_1"]
}
```

## Output

All methods produce the same `scoregraph.json` structure:

```json
{
  "bars": [
    {
      "bar": 1,
      "time_sig": "2/2", 
      "downbeat_abs_beat": 0.0
    }
  ],
  "nodes": [
    {
      "id": "1_1",
      "bar": 1,
      "beat": 1,
      "abs_beat": 0.0,
      "D_beats": 1.0,
      "flags": []
    }
  ],
  "tempo_marks": [...],
  "key_signature": "C",
  "tuning_hz": 440,
  "maps": {
    "bar_beat_to_abs_beat": {...},
    "abs_beat_to_bar_beat": {...}
  }
}
```

## Method Comparison

| Feature | Simple | Music21 | Pretty-MIDI |
|---------|--------|---------|-------------|
| Dependencies | None | music21 | pretty_midi |
| MusicXML | ✅ | ✅ | ❌ |
| MIDI | ❌ | ✅ | ✅ |
| Repeat Expansion | ❌ | ✅ | ❌ |
| Beat Tracking | Basic | Advanced | Advanced |
| Performance | Fast | Medium | Fast |
| Reliability | High | High | Medium |

## Recommendations

- **For MusicXML files**: Use `music21` method for best results
- **For MIDI files**: Use `pretty_midi` method
- **For minimal dependencies**: Use `simple` method
- **For production**: Use `music21` method with proper error handling

## References

- **music21**: https://web.mit.edu/music21/
- **pretty_midi**: https://github.com/craffel/pretty-midi
- **Partitura**: https://github.com/CPJKU/partitura (inspiration for original implementation)
