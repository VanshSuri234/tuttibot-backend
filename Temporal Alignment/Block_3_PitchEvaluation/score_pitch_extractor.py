#!/usr/bin/env python3
"""
Score Pitch Extractor - Extract expected pitches from musical scores

Uses music21 to parse MusicXML/MIDI and extract note information including:
- MIDI pitch numbers
- Frequency in Hz
- Onset times
- Durations

Repository: https://github.com/cuthbertLab/music21
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

try:
    from music21 import converter, stream, note, chord
except ImportError:
    raise ImportError("music21 is required. Install with: pip install music21")


@dataclass
class ScoreNote:
    """Represents a single note from the score"""
    note_index: int
    onset_time: float  # in seconds
    offset_time: float  # in seconds
    duration: float  # in seconds
    midi_pitch: int
    frequency_hz: float
    note_name: str
    octave: int
    quarter_length: float
    part_name: str = "unknown"
    measure_number: int = 0
    
    def to_dict(self):
        """Convert to dictionary with JSON-serializable values"""
        d = asdict(self)
        # Ensure all values are JSON serializable
        d['quarter_length'] = float(d['quarter_length'])
        d['onset_time'] = float(d['onset_time'])
        d['offset_time'] = float(d['offset_time'])
        d['duration'] = float(d['duration'])
        d['frequency_hz'] = float(d['frequency_hz'])
        return d


class ScorePitchExtractor:
    """Extract pitch information from musical scores (MusicXML/MIDI)"""
    
    def __init__(self, reference_frequency: float = 440.0, verbose: bool = True):
        """
        Initialize score pitch extractor
        
        Args:
            reference_frequency: A4 reference frequency (default: 440 Hz)
            verbose: Whether to print progress messages (default: True)
        """
        self.reference_frequency = reference_frequency
        self.verbose = verbose
        self.score = None
        self.notes: List[ScoreNote] = []
        
    def midi_to_hz(self, midi_pitch: int) -> float:
        """
        Convert MIDI pitch number to frequency in Hz
        
        Args:
            midi_pitch: MIDI pitch number (0-127)
            
        Returns:
            Frequency in Hz
        """
        return self.reference_frequency * (2 ** ((midi_pitch - 69) / 12.0))
    
    def hz_to_midi(self, frequency: float) -> int:
        """
        Convert frequency to MIDI pitch number
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            MIDI pitch number
        """
        return int(round(69 + 12 * np.log2(frequency / self.reference_frequency)))
    
    def load_score(self, score_path: str) -> None:
        """
        Load a musical score from file
        
        Args:
            score_path: Path to MusicXML (.xml, .mxl) or MIDI (.mid, .midi) file
        """
        score_path = Path(score_path)
        
        if not score_path.exists():
            raise FileNotFoundError(f"Score file not found: {score_path}")
        
        if self.verbose:
            print(f"Loading score: {score_path.name}")
        
        try:
            self.score = converter.parse(str(score_path))
            if self.verbose:
                print(f"Score loaded successfully")
        except Exception as e:
            raise ValueError(f"Failed to parse score: {e}")
    
    def extract_notes(self, flatten_chords: bool = True) -> List[ScoreNote]:
        """
        Extract all notes from the loaded score
        
        Args:
            flatten_chords: If True, extract individual notes from chords
            
        Returns:
            List of ScoreNote objects
        """
        if self.score is None:
            raise ValueError("No score loaded. Call load_score() first.")
        
        if self.verbose:
            print("Extracting notes from score...")
        
        self.notes = []
        note_index = 0
        
        # Get all parts in the score
        parts = self.score.parts if hasattr(self.score, 'parts') else [self.score]
        
        for part_idx, part in enumerate(parts):
            part_name = part.partName if hasattr(part, 'partName') and part.partName else f"Part_{part_idx}"
            
            # Flatten the part to get all notes in chronological order
            for element in part.flatten().notesAndRests:
                # Get measure number
                measure_num = 0
                if hasattr(element, 'measureNumber') and element.measureNumber:
                    measure_num = element.measureNumber
                
                # Handle regular notes
                if isinstance(element, note.Note):
                    score_note = self._create_score_note(
                        element, note_index, part_name, measure_num
                    )
                    self.notes.append(score_note)
                    note_index += 1
                
                # Handle chords
                elif isinstance(element, chord.Chord) and flatten_chords:
                    for pitch in element.pitches:
                        # Create a note-like object for each pitch in chord
                        chord_note = note.Note(pitch)
                        chord_note.offset = element.offset
                        chord_note.quarterLength = element.quarterLength
                        
                        score_note = self._create_score_note(
                            chord_note, note_index, part_name, measure_num
                        )
                        self.notes.append(score_note)
                        note_index += 1
        
        if self.verbose:
            print(f"Extracted {len(self.notes)} notes from score")
        
        return self.notes
    
    def _create_score_note(self, element: note.Note, note_index: int, 
                          part_name: str, measure_num: int) -> ScoreNote:
        """Create a ScoreNote from a music21 Note element"""
        
        # Get timing information
        onset_time = element.offset
        duration = element.quarterLength
        
        # Convert to seconds using tempo
        # Try to get tempo from the score
        tempo_bpm = 120.0  # default tempo
        if self.score:
            metronome_marks = self.score.flatten().getElementsByClass('MetronomeMark')
            if metronome_marks:
                tempo_bpm = metronome_marks[0].number
        
        # Convert quarter lengths to seconds
        seconds_per_quarter = 60.0 / tempo_bpm
        onset_seconds = onset_time * seconds_per_quarter
        duration_seconds = duration * seconds_per_quarter
        offset_seconds = onset_seconds + duration_seconds
        
        # Get pitch information
        midi_pitch = element.pitch.midi
        frequency_hz = self.midi_to_hz(midi_pitch)
        note_name = element.pitch.name
        octave = element.pitch.octave
        
        return ScoreNote(
            note_index=note_index,
            onset_time=onset_seconds,
            offset_time=offset_seconds,
            duration=duration_seconds,
            midi_pitch=midi_pitch,
            frequency_hz=frequency_hz,
            note_name=note_name,
            octave=octave,
            quarter_length=duration,
            part_name=part_name,
            measure_number=measure_num
        )
    
    def get_pitch_at_time(self, time: float) -> Optional[ScoreNote]:
        """
        Get the expected note/pitch at a given time
        
        Args:
            time: Time in seconds
            
        Returns:
            ScoreNote if a note is active at that time, None otherwise
        """
        for note in self.notes:
            if note.onset_time <= time < note.offset_time:
                return note
        return None
    
    def save_to_json(self, output_path: str) -> None:
        """
        Save extracted notes to JSON file
        
        Args:
            output_path: Path to output JSON file
        """
        output_data = {
            'metadata': {
                'total_notes': len(self.notes),
                'reference_frequency': self.reference_frequency,
                'pitch_range_midi': {
                    'min': min(n.midi_pitch for n in self.notes) if self.notes else 0,
                    'max': max(n.midi_pitch for n in self.notes) if self.notes else 0
                },
                'pitch_range_hz': {
                    'min': min(n.frequency_hz for n in self.notes) if self.notes else 0,
                    'max': max(n.frequency_hz for n in self.notes) if self.notes else 0
                },
                'total_duration': max(n.offset_time for n in self.notes) if self.notes else 0
            },
            'notes': [note.to_dict() for note in self.notes]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        if self.verbose:
            print(f"Score notes saved to: {output_path}")
    
    def get_notes_in_range(self, start_time: float, end_time: float) -> List[ScoreNote]:
        """
        Get all notes that overlap with a time range
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            List of ScoreNote objects
        """
        return [
            note for note in self.notes
            if note.onset_time < end_time and note.offset_time > start_time
        ]
    
    def get_statistics(self) -> Dict:
        """Get statistical summary of extracted notes"""
        if not self.notes:
            return {}
        
        pitches = [n.midi_pitch for n in self.notes]
        frequencies = [n.frequency_hz for n in self.notes]
        durations = [n.duration for n in self.notes]
        
        return {
            'total_notes': len(self.notes),
            'pitch_stats': {
                'min_midi': min(pitches),
                'max_midi': max(pitches),
                'mean_midi': np.mean(pitches),
                'std_midi': np.std(pitches)
            },
            'frequency_stats': {
                'min_hz': min(frequencies),
                'max_hz': max(frequencies),
                'mean_hz': np.mean(frequencies),
                'std_hz': np.std(frequencies)
            },
            'duration_stats': {
                'min_duration': min(durations),
                'max_duration': max(durations),
                'mean_duration': np.mean(durations),
                'std_duration': np.std(durations)
            },
            'total_duration': max(n.offset_time for n in self.notes)
        }


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract pitch information from musical scores')
    parser.add_argument('--score', required=True, help='Path to score file (MusicXML/MIDI)')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--reference-freq', type=float, default=440.0,
                       help='Reference frequency for A4 (default: 440 Hz)')
    
    args = parser.parse_args()
    
    # Extract notes
    extractor = ScorePitchExtractor(reference_frequency=args.reference_freq)
    extractor.load_score(args.score)
    notes = extractor.extract_notes()
    
    # Print statistics
    stats = extractor.get_statistics()
    print("\nStatistics:")
    print(json.dumps(stats, indent=2))
    
    # Save to JSON if specified
    if args.output:
        extractor.save_to_json(args.output)


if __name__ == '__main__':
    main()
