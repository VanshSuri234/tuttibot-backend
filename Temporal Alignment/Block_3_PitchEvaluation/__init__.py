"""
Block 3: Pitch Evaluation System

This module evaluates pitch accuracy by comparing:
- Score pitches (from MusicXML/MIDI)
- Performance pitches (from audio F0 extraction)

Outputs pitch deviation metrics and grades.
"""

from .score_pitch_extractor import ScorePitchExtractor
from .audio_pitch_extractor import AudioPitchExtractor
from .pitch_comparator import PitchComparator
from .pitch_grader import PitchGrader
from .pitch_visualizer import PitchVisualizer

__all__ = [
    'ScorePitchExtractor',
    'AudioPitchExtractor',
    'PitchComparator',
    'PitchGrader',
    'PitchVisualizer'
]

__version__ = '1.0.0'
