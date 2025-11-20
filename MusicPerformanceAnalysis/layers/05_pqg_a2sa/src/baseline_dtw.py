"""
Baseline DTW Alignment Module

Implements standard DTW alignment for comparison with PQG-A2SA.
Uses vanilla DTW from librosa without tempo/duration constraints.
"""

import numpy as np
import librosa
from scipy.spatial.distance import cdist


class BaselineDTWAligner:
    """
    Standard DTW alignment without PQG-A2SA refinements.
    
    This serves as a baseline to compare against the full PQG-A2SA pipeline.
    Uses simple DTW with cosine distance between chroma features.
    """
    
    def __init__(self, hop_length=1024, sr=22050):
        """
        Initialize baseline aligner.
        
        Args:
            hop_length: Hop length for audio frames (default: 1024)
            sr: Sample rate (default: 22050)
        """
        self.hop_length = hop_length
        self.sr = sr
        
    def align(self, audio_chroma, score_chroma, score_notes):
        """
        Align audio to score using standard DTW.
        
        Args:
            audio_chroma: Audio chroma features (frames × 12)
            score_chroma: Score chroma features (events × 12)
            score_notes: List of score note dictionaries with onset_time, offset_time
            
        Returns:
            results: Dictionary containing aligned note timings
        """
        print("\n[Baseline DTW] Starting alignment...")
        
        # Compute DTW with cosine distance
        print(f"  Audio chroma: {audio_chroma.shape}")
        print(f"  Score chroma: {score_chroma.shape}")
        
        # Audio and score chroma are already in (time × 12) format
        # No need to transpose
        X = score_chroma  # events × 12
        Y = audio_chroma  # frames × 12
        
        # Compute cost matrix using cosine distance
        D = self._compute_cost_matrix(X, Y, metric='cosine')
        
        # Run DTW
        wp = self._dtw(D)
        
        print(f"  DTW path length: {len(wp)}")
        
        # Convert alignment path to note timings
        results = self._path_to_note_timings(wp, score_notes)
        
        # Store DTW metadata
        results['dtw_cost_matrix'] = D
        results['dtw_path'] = wp
        
        print("[Baseline DTW] Alignment complete!")
        
        return results
    
    def _compute_cost_matrix(self, X, Y, metric='cosine'):
        """
        Compute pairwise distance matrix.
        
        Args:
            X: Score features (events × features)
            Y: Audio features (frames × features)
            metric: Distance metric ('cosine' or 'euclidean')
            
        Returns:
            D: Cost matrix (events × frames)
        """
        if metric == 'cosine':
            # Cosine distance = 1 - cosine_similarity
            D = cdist(X, Y, metric='cosine')
        elif metric == 'euclidean':
            D = cdist(X, Y, metric='euclidean')
        else:
            raise ValueError(f"Unknown metric: {metric}")
            
        return D
    
    def _dtw(self, C):
        """
        Standard DTW algorithm.
        
        Args:
            C: Cost matrix (N × M)
            
        Returns:
            wp: Alignment path as list of (i, j) tuples
        """
        N, M = C.shape
        
        # Initialize accumulated cost matrix
        D = np.zeros((N, M))
        D[0, 0] = C[0, 0]
        
        # Initialize first row and column
        for i in range(1, N):
            D[i, 0] = D[i-1, 0] + C[i, 0]
        for j in range(1, M):
            D[0, j] = D[0, j-1] + C[0, j]
        
        # Fill accumulated cost matrix
        for i in range(1, N):
            for j in range(1, M):
                D[i, j] = C[i, j] + min(
                    D[i-1, j],    # Insertion
                    D[i, j-1],    # Deletion
                    D[i-1, j-1]   # Match
                )
        
        # Backtrack to find optimal path
        wp = []
        i, j = N - 1, M - 1
        wp.append((i, j))
        
        while i > 0 or j > 0:
            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                # Choose minimum predecessor
                tb = np.argmin([D[i-1, j-1], D[i-1, j], D[i, j-1]])
                if tb == 0:
                    i -= 1
                    j -= 1
                elif tb == 1:
                    i -= 1
                else:
                    j -= 1
            wp.append((i, j))
        
        # Reverse to get forward path
        wp.reverse()
        
        return wp
    
    def _path_to_note_timings(self, wp, score_notes):
        """
        Convert DTW path to note onset/offset timings.
        
        Args:
            wp: DTW alignment path [(score_idx, audio_idx), ...]
            score_notes: List of score note dictionaries
            
        Returns:
            results: Dictionary with aligned note timings per instrument
        """
        # Create mapping from score event to audio frames
        score_to_audio = {}
        for score_idx, audio_idx in wp:
            if score_idx not in score_to_audio:
                score_to_audio[score_idx] = []
            score_to_audio[score_idx].append(audio_idx)
        
        # Group notes by instrument
        instruments = {}
        for note in score_notes:
            inst = note.get('instrument', 'unknown')
            if inst not in instruments:
                instruments[inst] = []
            instruments[inst].append(note)
        
        # Align each instrument's notes
        results = {}
        for inst_name, notes in instruments.items():
            aligned_notes = []
            
            for note in notes:
                # Get score event index for this note
                # Assume notes are ordered by onset time
                score_idx = note.get('score_index', 0)
                
                if score_idx in score_to_audio:
                    # Get audio frames aligned to this score event
                    audio_frames = score_to_audio[score_idx]
                    
                    # Onset = first aligned frame
                    onset_frame = min(audio_frames)
                    onset_time = librosa.frames_to_time(
                        onset_frame, 
                        sr=self.sr, 
                        hop_length=self.hop_length
                    )
                    
                    # Offset = last aligned frame
                    offset_frame = max(audio_frames)
                    offset_time = librosa.frames_to_time(
                        offset_frame, 
                        sr=self.sr, 
                        hop_length=self.hop_length
                    )
                    
                    aligned_notes.append({
                        'pitch': note['pitch'],
                        'onset_time': onset_time,
                        'offset_time': offset_time,
                        'duration': offset_time - onset_time,
                        'velocity': note.get('velocity', 64)
                    })
            
            results[inst_name] = aligned_notes
        
        return results


def extract_note_times(results_dict):
    """
    Extract onset and offset times from results dictionary.
    
    Args:
        results_dict: Alignment results (instrument -> notes)
        
    Returns:
        onsets: List of onset times
        offsets: List of offset times
    """
    onsets = []
    offsets = []
    
    # Handle PQG-A2SA format with 'instruments' key
    if 'instruments' in results_dict:
        for inst in results_dict['instruments']:
            for note in inst['notes']:
                onsets.append(note.get('onset'))
                offsets.append(note.get('offset'))
    # Handle baseline format (flat dict)
    else:
        for inst_name, notes in results_dict.items():
            if inst_name in ['dtw_cost_matrix', 'dtw_path']:
                continue
            for note in notes:
                # Handle both key formats: 'onset_time'/'offset_time' and 'onset'/'offset'
                onset = note.get('onset_time', note.get('onset'))
                offset = note.get('offset_time', note.get('offset'))
                onsets.append(onset)
                offsets.append(offset)
    
    return np.array(onsets), np.array(offsets)
