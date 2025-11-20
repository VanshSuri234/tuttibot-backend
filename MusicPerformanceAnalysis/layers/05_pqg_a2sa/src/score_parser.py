"""
Score parsing module
- Extract chord sequences from multi-instrument scores
- Parse per-instrument note lists with onset/offset positions
- Compute score-level chroma for each chord
"""

import numpy as np
import pretty_midi
from collections import defaultdict
from sklearn.preprocessing import normalize


class ScoreParser:
    """Parse MIDI/MusicXML scores for PQG-A2SA"""
    
    def __init__(self):
        pass
    
    def load_midi(self, midi_path):
        """Load MIDI file using pretty_midi"""
        return pretty_midi.PrettyMIDI(midi_path)
    
    def extract_chords(self, midi_obj, time_resolution=0.01):
        """
        Extract chord sequence from multi-instrument MIDI
        A chord = all notes with the same onset time across instruments
        
        Args:
            midi_obj: PrettyMIDI object
            time_resolution: bin size for grouping simultaneous onsets (seconds)
        
        Returns:
            chords: list of dicts with keys:
                - 'onset_time': score time (beats or seconds)
                - 'pitches': list of MIDI pitch numbers
                - 'instruments': list of instrument indices
                - 'chroma': 12-D normalized chroma vector
        """
        # Collect all note onsets across instruments
        onset_events = []
        
        for inst_idx, instrument in enumerate(midi_obj.instruments):
            if instrument.is_drum:
                continue
            
            for note in instrument.notes:
                onset_events.append({
                    'time': note.start,
                    'pitch': note.pitch,
                    'instrument': inst_idx,
                    'note_obj': note
                })
        
        # Sort by onset time
        onset_events.sort(key=lambda x: x['time'])
        
        if not onset_events:
            return []
        
        # Group into chords (notes with similar onset times)
        chords = []
        current_chord = {
            'onset_time': onset_events[0]['time'],
            'pitches': [onset_events[0]['pitch']],
            'instruments': [onset_events[0]['instrument']],
            'note_objects': [onset_events[0]['note_obj']]
        }
        
        for event in onset_events[1:]:
            if abs(event['time'] - current_chord['onset_time']) <= time_resolution:
                # Same chord
                current_chord['pitches'].append(event['pitch'])
                current_chord['instruments'].append(event['instrument'])
                current_chord['note_objects'].append(event['note_obj'])
            else:
                # Finalize current chord
                current_chord['chroma'] = self._pitches_to_chroma(current_chord['pitches'])
                chords.append(current_chord)
                
                # Start new chord
                current_chord = {
                    'onset_time': event['time'],
                    'pitches': [event['pitch']],
                    'instruments': [event['instrument']],
                    'note_objects': [event['note_obj']]
                }
        
        # Finalize last chord
        current_chord['chroma'] = self._pitches_to_chroma(current_chord['pitches'])
        chords.append(current_chord)
        
        return chords
    
    def extract_instrument_notes(self, midi_obj):
        """
        Extract per-instrument note sequences
        
        Returns:
            instruments: list of dicts, one per instrument:
                - 'name': instrument name
                - 'program': MIDI program number
                - 'notes': list of dicts with 'pitch', 'onset', 'offset', 'velocity'
        """
        instruments = []
        
        for inst_idx, instrument in enumerate(midi_obj.instruments):
            if instrument.is_drum:
                continue
            
            notes = []
            for note in sorted(instrument.notes, key=lambda n: n.start):
                notes.append({
                    'pitch': note.pitch,
                    'onset': note.start,
                    'offset': note.end,
                    'velocity': note.velocity,
                    'duration': note.end - note.start
                })
            
            instruments.append({
                'name': instrument.name or f"Instrument_{inst_idx}",
                'program': instrument.program,
                'notes': notes,
                'index': inst_idx
            })
        
        return instruments
    
    def _pitches_to_chroma(self, pitches):
        """
        Convert list of MIDI pitches to 12-D normalized chroma
        
        Args:
            pitches: list of MIDI pitch numbers
        
        Returns:
            chroma: (12,) normalized array
        """
        chroma = np.zeros(12)
        
        for pitch in pitches:
            pitch_class = pitch % 12
            chroma[pitch_class] += 1.0
        
        # L2 normalize
        norm = np.linalg.norm(chroma)
        if norm > 0:
            chroma = chroma / norm
        
        return chroma
    
    def get_chord_chroma_sequence(self, chords):
        """
        Extract just the chroma sequence from chord list
        
        Returns:
            chroma_seq: (12, n_chords) array
            onset_times: (n_chords,) array of onset times
        """
        if not chords:
            return np.zeros((12, 0)), np.array([])
        
        chroma_seq = np.column_stack([chord['chroma'] for chord in chords])
        onset_times = np.array([chord['onset_time'] for chord in chords])
        
        return chroma_seq, onset_times
    
    def build_pitch_templates(self, instruments, n_bins=88, fmin_midi=21):
        """
        Build spectral templates for each instrument/pitch
        Simplified version: returns pitch activation patterns
        
        Args:
            instruments: output from extract_instrument_notes
            n_bins: number of frequency bins
            fmin_midi: lowest MIDI note
        
        Returns:
            templates: dict mapping (inst_idx, pitch) -> template vector
        """
        templates = {}
        
        # Simple Gaussian-like template for each pitch
        for inst in instruments:
            inst_idx = inst['index']
            pitches = set(note['pitch'] for note in inst['notes'])
            
            for pitch in pitches:
                # Create a simple template (could be replaced with real harmonic templates)
                template = np.zeros(n_bins)
                
                # Map MIDI pitch to bin
                bin_idx = pitch - fmin_midi
                if 0 <= bin_idx < n_bins:
                    # Fundamental + harmonics (simplified)
                    template[bin_idx] = 1.0
                    if bin_idx + 12 < n_bins:
                        template[bin_idx + 12] = 0.5  # Octave
                    if bin_idx + 19 < n_bins:
                        template[bin_idx + 19] = 0.3  # Fifth
                
                templates[(inst_idx, pitch)] = template
        
        return templates
