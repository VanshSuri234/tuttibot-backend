"""
Variable-Interval DTW (VIDTW) module
- DTW between score chord chroma and audio cluster chroma
- Tempo-free coarse alignment at chord level
"""

import numpy as np
from scipy.spatial.distance import euclidean


class VIDTW:
    """Variable-Interval Dynamic Time Warping for ensemble alignment"""
    
    def __init__(self):
        pass
    
    def align(self, score_chroma, audio_chroma, return_path=True):
        """
        Perform DTW between score and audio chroma sequences
        
        Args:
            score_chroma: (12, L_chord) array of score chord chromas
            audio_chroma: (12, L_cluster) array of audio cluster chromas
            return_path: whether to return the alignment path
        
        Returns:
            cost: total alignment cost
            path: list of (score_idx, audio_idx) tuples if return_path=True
            score_to_audio: dict mapping score chord index -> audio cluster index(es)
        """
        L_score = score_chroma.shape[1]
        L_audio = audio_chroma.shape[1]
        
        # Initialize cost matrix
        D = np.full((L_score + 1, L_audio + 1), np.inf)
        D[0, 0] = 0.0
        
        # Fill cost matrix
        for x in range(1, L_score + 1):
            for y in range(1, L_audio + 1):
                # Distance between chord x-1 and cluster y-1
                dist = euclidean(score_chroma[:, x - 1], audio_chroma[:, y - 1])
                
                # Allowed transitions:
                # - (x, y-1): same chord continues to next cluster
                # - (x-1, y-1): advance to next chord with next cluster
                D[x, y] = dist + min(
                    D[x, y - 1],      # Horizontal: audio slower
                    D[x - 1, y - 1]   # Diagonal: synchronized advance
                )
        
        total_cost = D[L_score, L_audio]
        
        if not return_path:
            return total_cost, None, None
        
        # Backtrack to find optimal path
        path = []
        x, y = L_score, L_audio
        
        while x > 0 and y > 0:
            path.append((x - 1, y - 1))  # Convert to 0-indexed
            
            # Determine which predecessor was used
            candidates = [
                (D[x, y - 1], (x, y - 1)),      # Horizontal
                (D[x - 1, y - 1], (x - 1, y - 1))  # Diagonal
            ]
            
            min_cost, (prev_x, prev_y) = min(candidates, key=lambda c: c[0])
            x, y = prev_x, prev_y
        
        path.reverse()
        
        # Build score-to-audio mapping
        score_to_audio = {}
        for score_idx, audio_idx in path:
            if score_idx not in score_to_audio:
                score_to_audio[score_idx] = []
            score_to_audio[score_idx].append(audio_idx)
        
        return total_cost, path, score_to_audio
    
    def get_chord_onset_times(self, score_to_audio, cluster_boundaries, frame_times):
        """
        Extract preliminary chord onset times from alignment
        
        Args:
            score_to_audio: dict from align() mapping chord idx -> cluster idx(es)
            cluster_boundaries: (n_clusters+1,) array of frame indices
            frame_times: (n_frames,) array of frame times in seconds
        
        Returns:
            chord_onsets: (n_chords,) array of onset times in seconds
        """
        n_chords = max(score_to_audio.keys()) + 1
        chord_onsets = np.zeros(n_chords)
        
        for chord_idx in range(n_chords):
            if chord_idx in score_to_audio:
                # Take the first cluster aligned to this chord
                first_cluster_idx = min(score_to_audio[chord_idx])
                
                # Onset time = start time of first cluster
                first_frame = cluster_boundaries[first_cluster_idx]
                chord_onsets[chord_idx] = frame_times[first_frame]
            else:
                # Fallback: interpolate
                if chord_idx > 0:
                    chord_onsets[chord_idx] = chord_onsets[chord_idx - 1]
        
        return chord_onsets
    
    def align_with_constraints(self, score_chroma, audio_chroma, 
                               score_times, audio_times,
                               window_size=None):
        """
        DTW with local timing constraints (for IOI-GM local re-alignment)
        
        Args:
            score_chroma: (12, L_score) array
            audio_chroma: (12, L_audio) array
            score_times: (L_score,) onset times in score units (beats)
            audio_times: (L_audio,) times in seconds
            window_size: Sakoe-Chiba band width (None = no constraint)
        
        Returns:
            Similar to align() but with banded DTW
        """
        L_score = score_chroma.shape[1]
        L_audio = audio_chroma.shape[1]
        
        # Initialize cost matrix
        D = np.full((L_score + 1, L_audio + 1), np.inf)
        D[0, 0] = 0.0
        
        for x in range(1, L_score + 1):
            for y in range(1, L_audio + 1):
                # Apply band constraint if specified
                if window_size is not None:
                    # Compute expected y position assuming linear tempo
                    if L_score > 1 and L_audio > 1:
                        expected_y = (x - 1) * (L_audio - 1) / (L_score - 1) + 1
                        if abs(y - expected_y) > window_size:
                            continue
                
                dist = euclidean(score_chroma[:, x - 1], audio_chroma[:, y - 1])
                
                D[x, y] = dist + min(
                    D[x, y - 1],
                    D[x - 1, y - 1],
                    D[x - 1, y]  # Allow vertical move for local flexibility
                )
        
        total_cost = D[L_score, L_audio]
        
        # Backtrack
        path = []
        x, y = L_score, L_audio
        
        while x > 0 and y > 0:
            path.append((x - 1, y - 1))
            
            candidates = [
                (D[x, y - 1], (x, y - 1)),
                (D[x - 1, y - 1], (x - 1, y - 1)),
                (D[x - 1, y], (x - 1, y))
            ]
            
            min_cost, (prev_x, prev_y) = min(candidates, key=lambda c: c[0])
            x, y = prev_x, prev_y
        
        # Handle remaining path
        while x > 0:
            path.append((x - 1, 0))
            x -= 1
        while y > 0:
            path.append((0, y - 1))
            y -= 1
        
        path.reverse()
        
        # Build mapping
        score_to_audio = {}
        for score_idx, audio_idx in path:
            if score_idx not in score_to_audio:
                score_to_audio[score_idx] = []
            score_to_audio[score_idx].append(audio_idx)
        
        return total_cost, path, score_to_audio
