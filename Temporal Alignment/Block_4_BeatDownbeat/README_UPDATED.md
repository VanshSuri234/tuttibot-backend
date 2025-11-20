# Block 4: Beat and Downbeat Detection with Confidence

## What This Does

This module detects where beats and downbeats occur in an audio performance, and assigns a confidence score to each detection. Think of it as finding the rhythm pulse of the music.

## Why Confidence Matters

When the music has a clear, steady beat, the detector is very confident. When the rhythm is unclear or complex, the confidence is lower. These confidence scores help the alignment system know which beats to trust more when matching the performance to the score.

## Input

- Audio file (.wav format recommended)
- Typical: recorded performance of a musical piece

## Output

A JSON file containing:
- Time of each beat (in seconds)
- Whether it is a downbeat (start of a measure)
- Confidence score (0.0 to 1.0, higher means more certain)

Example output format:
```json
[
  {
    "t": 0.5234,
    "downbeat": 1,
    "confidence": 0.9123
  },
  {
    "t": 1.0156,
    "downbeat": 0,
    "confidence": 0.8756
  }
]
```

## How to Use

Basic usage:
```bash
python estimate_beats.py --audio performance.wav --beats beats.json
```

The script will:
1. Analyze the audio for rhythmic patterns
2. Identify beat positions and measure boundaries
3. Calculate confidence for each detection
4. Save results with statistics

## What Changed

Previous version only detected beat times. Updated version now:
- Captures confidence scores from the beat detection model
- Provides fallback method if primary detection fails
- Reports average confidence and statistics
- Better error handling and user feedback

## Technical Notes

Uses BeatNet model with offline processing mode. The confidence scores come from the internal probability estimates of the beat tracking algorithm. High confidence (above 0.7) indicates strong rhythmic clarity at that moment in the music.

## For Musicians

This is like having someone tap along to the music and tell you "I'm very sure about this beat" or "I'm less certain here". The system uses this information to make smarter decisions about how the performance matches the written score.
