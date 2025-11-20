"""
IOI-Guided Modification (IOI-GM) module
- Detect tempo deviations using inter-onset intervals
- Locally re-align deviated segments with duration constraints
"""

import numpy as np
from .config import PQGConfig
from .vidtw import VIDTW


class IOIGuidedModification:
    """IOI-based refinement of coarse chord alignment"""
    
    def __init__(self, config=None):
        self.config = config or PQGConfig()
        self.vidtw = VIDTW()
    
    def refine_alignment(self, chord_onsets_preliminary, chord_score_positions,
                        score_chroma, audio_chroma_frames, frame_times):
        """
        Refine chord alignment by detecting and re-aligning deviated segments
        
        Args:
            chord_onsets_preliminary: (n_chords,) preliminary onset times (seconds)
            chord_score_positions: (n_chords,) onset positions in score (beats)
            score_chroma: (12, n_chords) score chord chromas
            audio_chroma_frames: (12, n_frames) audio frame chromas
            frame_times: (n_frames,) frame times in seconds
        
        Returns:
            chord_onsets_refined: (n_chords,) refined onset times
        """
        n_chords = len(chord_onsets_preliminary)
        
        # Compute velocities (s/beat)
        velocities = self._compute_velocities(
            chord_onsets_preliminary, 
            chord_score_positions
        )
        
        # Compute local average velocities
        local_velocities = self._compute_local_velocities(
            chord_onsets_preliminary,
            chord_score_positions,
            delta=self.config.IOI_DELTA
        )
        
        # Compute ratios and detect deviants
        ratios = velocities / (local_velocities + 1e-8)
        deviated_mask = (ratios < self.config.R_LOW) | (ratios > self.config.R_HIGH)
        
        # Find deviated segments (consecutive deviated chords)
        segments = self._find_deviated_segments(deviated_mask)
        
        # Refine each segment locally
        chord_onsets_refined = chord_onsets_preliminary.copy()
        
        for segment_start, segment_end in segments:
            # Expand segment by 1 chord on each side for context
            seg_start = max(0, segment_start - 1)
            seg_end = min(n_chords - 1, segment_end + 1)
            
            # Re-align this segment
            refined_onsets = self._realign_segment(
                seg_start, seg_end,
                chord_score_positions,
                score_chroma,
                audio_chroma_frames,
                frame_times,
                chord_onsets_preliminary
            )
            
            # Update refined onsets for the deviated portion
            chord_onsets_refined[segment_start:segment_end + 1] = \
                refined_onsets[segment_start - seg_start:segment_end - seg_start + 1]
        
        return chord_onsets_refined
    
    def _compute_velocities(self, onset_times, score_positions):
        """
        Compute per-chord velocities (s/beat)
        
        v_i = (t_{i+1} - t_i) / (l_{i+1} - l_i)
        """
        n = len(onset_times)
        velocities = np.zeros(n)
        
        for i in range(n - 1):
            dt = onset_times[i + 1] - onset_times[i]
            dl = score_positions[i + 1] - score_positions[i]
            
            if dl > 0:
                velocities[i] = dt / dl
            else:
                velocities[i] = velocities[i - 1] if i > 0 else 0.0
        
        # Last chord velocity = same as previous
        velocities[-1] = velocities[-2] if n > 1 else 0.0
        
        return velocities
    
    def _compute_local_velocities(self, onset_times, score_positions, delta=4):
        """
        Compute local average velocities over ±delta chords
        
        v'_i = (t_{i+delta} - t_{i-delta}) / (l_{i+delta} - l_{i-delta})
        """
        n = len(onset_times)
        local_velocities = np.zeros(n)
        
        for i in range(n):
            i_minus = max(0, i - delta)
            i_plus = min(n - 1, i + delta)
            
            dt = onset_times[i_plus] - onset_times[i_minus]
            dl = score_positions[i_plus] - score_positions[i_minus]
            
            if dl > 0:
                local_velocities[i] = dt / dl
            else:
                local_velocities[i] = 1.0  # Fallback
        
        return local_velocities
    
    def _find_deviated_segments(self, deviated_mask):
        """
        Find consecutive runs of deviated chords
        
        Returns:
            segments: list of (start_idx, end_idx) tuples (inclusive)
        """
        segments = []
        in_segment = False
        start_idx = 0
        
        for i, is_deviated in enumerate(deviated_mask):
            if is_deviated and not in_segment:
                start_idx = i
                in_segment = True
            elif not is_deviated and in_segment:
                segments.append((start_idx, i - 1))
                in_segment = False
        
        # Close final segment if needed
        if in_segment:
            segments.append((start_idx, len(deviated_mask) - 1))
        
        return segments
    
    def _realign_segment(self, seg_start, seg_end, chord_score_positions,
                        score_chroma, audio_chroma_frames, frame_times,
                        preliminary_onsets):
        """
        Re-align a segment of chords with duration constraints
        
        Uses fine-grained DTW between:
        - Score: quantized to fine grid (0.02 beat resolution)
        - Audio: frames around preliminary alignment
        """
        # Extract segment chroma
        seg_score_chroma = score_chroma[:, seg_start:seg_end + 1]
        
        # Score time range (beats)
        score_start = chord_score_positions[seg_start]
        score_end = chord_score_positions[seg_end]
        
        # Create fine grid in score space
        fine_grid_beats = np.arange(
            score_start,
            score_end + self.config.FINE_GRID_RESOLUTION,
            self.config.FINE_GRID_RESOLUTION
        )
        
        # Interpolate score chroma onto fine grid (repeat each chord until next)
        fine_score_chroma = self._interpolate_score_chroma(
            seg_score_chroma,
            chord_score_positions[seg_start:seg_end + 1],
            fine_grid_beats
        )
        
        # Audio time range (with margin)
        audio_start_time = preliminary_onsets[seg_start] - 0.5
        audio_end_time = preliminary_onsets[seg_end] + 0.5
        
        # Find corresponding frame indices
        frame_start = np.searchsorted(frame_times, audio_start_time)
        frame_end = np.searchsorted(frame_times, audio_end_time)
        frame_start = max(0, frame_start)
        frame_end = min(len(frame_times), frame_end)
        
        # Extract audio frames for segment
        seg_audio_chroma = audio_chroma_frames[:, frame_start:frame_end]
        seg_frame_times = frame_times[frame_start:frame_end]
        
        if seg_audio_chroma.shape[1] == 0 or fine_score_chroma.shape[1] == 0:
            # Fallback: return preliminary
            return preliminary_onsets[seg_start:seg_end + 1]
        
        # Perform constrained DTW
        _, _, score_to_audio = self.vidtw.align_with_constraints(
            fine_score_chroma,
            seg_audio_chroma,
            fine_grid_beats,
            seg_frame_times,
            window_size=20  # Mild tempo constraint
        )
        
        # Map chord positions to audio times
        refined_onsets = np.zeros(seg_end - seg_start + 1)
        
        for i, chord_idx in enumerate(range(seg_start, seg_end + 1)):
            chord_pos = chord_score_positions[chord_idx]
            
            # Find closest fine grid point
            grid_idx = np.argmin(np.abs(fine_grid_beats - chord_pos))
            
            # Get aligned audio frame
            if grid_idx in score_to_audio and score_to_audio[grid_idx]:
                audio_idx = score_to_audio[grid_idx][0]
                if audio_idx < len(seg_frame_times):
                    refined_onsets[i] = seg_frame_times[audio_idx]
                else:
                    refined_onsets[i] = preliminary_onsets[chord_idx]
            else:
                refined_onsets[i] = preliminary_onsets[chord_idx]
        
        return refined_onsets
    
    def _interpolate_score_chroma(self, chord_chromas, chord_positions, fine_grid):
        """
        Expand chord chromas to fine grid (step function)
        Each chord's chroma is repeated until next chord
        """
        n_chords = chord_chromas.shape[1]
        n_grid = len(fine_grid)
        fine_chroma = np.zeros((12, n_grid))
        
        for i, grid_pos in enumerate(fine_grid):
            # Find which chord this grid point belongs to
            chord_idx = np.searchsorted(chord_positions, grid_pos, side='right') - 1
            chord_idx = max(0, min(n_chords - 1, chord_idx))
            
            fine_chroma[:, i] = chord_chromas[:, chord_idx]
        
        return fine_chroma
