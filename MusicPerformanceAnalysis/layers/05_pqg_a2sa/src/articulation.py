"""
Articulation detection and note timing refinement module
- Detect staccato vs legato articulation between consecutive notes
- Apply articulation-specific onset/offset detection rules
- Use per-instrument NMF activations for precise timing
"""

import numpy as np
from .config import PQGConfig


class ArticulationRefinement:
    """Per-instrument note-level onset/offset refinement"""
    
    def __init__(self, config=None):
        self.config = config or PQGConfig()
    
    def refine_instrument_notes(self, instrument, inst_activations, 
                                chord_onsets_refined, frame_times):
        """
        Refine all note timings for one instrument
        
        Args:
            instrument: instrument dict with 'notes' list
            inst_activations: dict mapping pitch -> (n_frames,) activation
            chord_onsets_refined: (n_chords,) refined chord onset times
            frame_times: (n_frames,) frame times in seconds
        
        Returns:
            refined_notes: list of dicts with 'pitch', 'onset', 'offset', 'articulation'
        """
        notes = instrument['notes']
        refined_notes = []
        
        # Process notes in pairs to determine boundaries
        i = 0
        while i < len(notes):
            note_alpha = notes[i]
            pitch_alpha = note_alpha['pitch']
            
            # Get activation for this pitch
            if pitch_alpha not in inst_activations:
                # Fallback: keep original timing
                refined_notes.append({
                    **note_alpha,
                    'articulation': 'unknown'
                })
                i += 1
                continue
            
            H_alpha = inst_activations[pitch_alpha]
            
            # Map note onset to audio-derived chord onset
            # Find the chord that this note belongs to (nearest chord onset in score)
            onset_alpha = self._map_note_to_chord_onset(
                note_alpha['onset'], 
                chord_onsets_refined
            )
            
            # Default offset to score timing (will be refined)
            offset_alpha = note_alpha['offset']
            articulation = 'uncertain'
            
            if i < len(notes) - 1:
                # Process pair (alpha, beta) to find alpha's offset and beta's onset
                note_beta = notes[i + 1]
                pitch_beta = note_beta['pitch']
                
                if pitch_beta in inst_activations:
                    H_beta = inst_activations[pitch_beta]
                    
                    # Refine using articulation rules - returns alpha's offset
                    offset_alpha, articulation = self._refine_note_pair(
                        note_alpha, note_beta,
                        H_alpha, H_beta,
                        frame_times,
                        chord_onsets_refined
                    )
            
            refined_notes.append({
                'pitch': pitch_alpha,
                'onset': onset_alpha,
                'offset': offset_alpha,
                'articulation': articulation,
                'velocity': note_alpha.get('velocity', 64)
            })
            
            i += 1
        
        return refined_notes
    
    def _refine_note_pair(self, note_alpha, note_beta, H_alpha, H_beta,
                         frame_times, chord_onsets):
        """
        Refine timing for consecutive note pair (alpha -> beta)
        Focus on finding alpha's offset time based on articulation
        
        Returns:
            offset_alpha: refined offset time for alpha
            articulation: 'staccato' or 'legato'
        """
        # Find chord-level anchor times
        f_a = self._find_nearest_chord_time(note_alpha['onset'], chord_onsets)
        f_b = self._find_nearest_chord_time(note_beta['onset'], chord_onsets)
        
        # Region of interest between the two notes
        f_ROI_start = (f_a + f_b) / 2.0
        f_ROI_end = f_b + (f_b - f_a) / 2.0  # Approximate end
        
        # Convert to frame indices
        roi_start_frame = np.searchsorted(frame_times, f_ROI_start)
        roi_end_frame = np.searchsorted(frame_times, f_ROI_end)
        roi_start_frame = max(0, roi_start_frame)
        roi_end_frame = min(len(frame_times), roi_end_frame)
        
        # Compute average energies
        a_start_frame = np.searchsorted(frame_times, f_a)
        a_end_frame = np.searchsorted(frame_times, f_b)
        e_alpha = np.mean(H_alpha[a_start_frame:a_end_frame]) if a_end_frame > a_start_frame else 0.0
        
        b_start_frame = a_end_frame
        b_end_frame = min(len(frame_times), b_start_frame + 50)  # Arbitrary window
        e_beta = np.mean(H_beta[b_start_frame:b_end_frame]) if b_end_frame > b_start_frame else 0.0
        
        # Sum and difference signals
        H_s = H_alpha + H_beta
        H_d = H_alpha - H_beta
        
        # Detect articulation
        articulation = self._detect_articulation(
            H_s, roi_start_frame, roi_end_frame, e_alpha, e_beta
        )
        
        if articulation == 'staccato':
            # Find rest gap
            rest_start, rest_end = self._find_rest_gap(
                H_s, roi_start_frame, roi_end_frame, e_alpha, e_beta
            )
            
            if rest_start is not None and rest_end is not None:
                # Offset alpha: before rest
                offset_alpha_frame = self._find_staccato_offset(
                    H_alpha, roi_start_frame, rest_start, e_alpha
                )
                
                offset_alpha = frame_times[offset_alpha_frame] if offset_alpha_frame < len(frame_times) else note_alpha['offset']
                return offset_alpha, 'staccato'
        
        # Legato or fallback
        # Find zero-crossing in H_d
        onset_beta_frame = self._find_legato_onset(H_d, roi_start_frame, roi_end_frame, f_b, frame_times)
        
        if onset_beta_frame is not None:
            # Find offset alpha near onset beta
            offset_alpha_frame = self._find_legato_offset(
                H_s, onset_beta_frame
            )
            
            offset_alpha = frame_times[offset_alpha_frame] if offset_alpha_frame < len(frame_times) else note_alpha['offset']
            return offset_alpha, 'legato'
        
        # Fallback: use chord boundary or score timing
        return note_alpha['offset'], 'uncertain'
    
    def _find_nearest_chord_time(self, note_time, chord_onsets):
        """Find nearest chord onset time to note time"""
        if len(chord_onsets) == 0:
            return note_time
        
        idx = np.argmin(np.abs(chord_onsets - note_time))
        return chord_onsets[idx]
    
    def _map_note_to_chord_onset(self, note_score_time, chord_onsets_refined):
        """
        Map a note's score onset time to the corresponding audio-derived chord onset.
        
        This is crucial for proper evaluation: we need to use the audio-derived
        timing, not the MIDI score timing, for onset alignment testing.
        
        Args:
            note_score_time: Note onset time from score (MIDI)
            chord_onsets_refined: Audio-derived chord onset times from VIDTW+IOI-GM
            
        Returns:
            Audio-derived onset time for this note
        """
        if len(chord_onsets_refined) == 0:
            return note_score_time
        
        # Find the chord that this note belongs to
        # (the chord whose onset is closest to this note's score onset)
        idx = np.argmin(np.abs(chord_onsets_refined - note_score_time))
        
        # Return the audio-derived onset time for that chord
        return chord_onsets_refined[idx]
    
    def _detect_articulation(self, H_s, roi_start, roi_end, e_alpha, e_beta):
        """
        Detect if there's a sustained rest gap (staccato) or not (legato)
        
        Rest condition: H_s < k_rest * (e_alpha + e_beta) for T_s consecutive frames
        """
        threshold = self.config.K_REST * (e_alpha + e_beta)
        T_s_frames = self.config.ms_to_frames(self.config.T_S_MS)
        
        if roi_end <= roi_start:
            return 'legato'
        
        # Find continuous low-energy regions
        low_energy = H_s[roi_start:roi_end] < threshold
        
        # Check for sustained gap
        max_consecutive = 0
        current_consecutive = 0
        
        for is_low in low_energy:
            if is_low:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        if max_consecutive >= T_s_frames:
            return 'staccato'
        else:
            return 'legato'
    
    def _find_rest_gap(self, H_s, roi_start, roi_end, e_alpha, e_beta):
        """Find the rest gap interval [f_rest, f'_rest]"""
        threshold = self.config.K_REST * (e_alpha + e_beta)
        T_s_frames = self.config.ms_to_frames(self.config.T_S_MS)
        
        if roi_end <= roi_start:
            return None, None
        
        low_energy = H_s[roi_start:roi_end] < threshold
        
        # Find longest consecutive low-energy region
        max_start = None
        max_end = None
        max_length = 0
        
        current_start = None
        current_length = 0
        
        for i, is_low in enumerate(low_energy):
            if is_low:
                if current_start is None:
                    current_start = i
                current_length += 1
            else:
                if current_length >= T_s_frames and current_length > max_length:
                    max_start = current_start
                    max_end = i
                    max_length = current_length
                current_start = None
                current_length = 0
        
        # Check final region
        if current_length >= T_s_frames and current_length > max_length:
            max_start = current_start
            max_end = len(low_energy)
        
        if max_start is not None:
            return roi_start + max_start, roi_start + max_end
        
        return None, None
    
    def _find_staccato_offset(self, H_alpha, roi_start, rest_start, e_alpha):
        """Find offset of alpha before rest gap"""
        threshold = self.config.K_OFF * e_alpha
        
        # Search backwards from rest_start
        for t in range(rest_start - 1, roi_start - 1, -1):
            if t < len(H_alpha) and H_alpha[t] > threshold:
                return t
        
        return roi_start
    
    def _find_staccato_onset(self, H_beta, rest_end, roi_end, e_beta):
        """Find onset of beta after rest gap"""
        threshold = self.config.K_ON * e_beta
        
        # Search forward from rest_end
        for t in range(rest_end, roi_end):
            if t < len(H_beta) and H_beta[t] > threshold:
                return t
        
        return rest_end
    
    def _find_legato_onset(self, H_d, roi_start, roi_end, expected_time, frame_times):
        """Find zero-crossing in H_d (where alpha ends and beta begins)"""
        if roi_end <= roi_start + 1:
            return None
        
        # Find sign changes
        H_d_roi = H_d[roi_start:roi_end]
        
        # Find zero crossings (sign change)
        zero_crossings = []
        for i in range(len(H_d_roi) - 1):
            if H_d_roi[i] * H_d_roi[i + 1] <= 0:
                zero_crossings.append(roi_start + i)
        
        if not zero_crossings:
            return None
        
        # Choose zero crossing nearest to expected time
        expected_frame = np.searchsorted(frame_times, expected_time)
        nearest_crossing = min(zero_crossings, key=lambda f: abs(f - expected_frame))
        
        return nearest_crossing
    
    def _find_legato_offset(self, H_s, onset_beta_frame):
        """Find offset of alpha near onset of beta (local maximum in H_s)"""
        T_l_frames = self.config.ms_to_frames(self.config.T_L_MS)
        
        # Search window before onset_beta
        search_start = max(0, onset_beta_frame - T_l_frames)
        search_end = onset_beta_frame
        
        if search_end <= search_start:
            return onset_beta_frame
        
        # Find local maximum
        H_s_window = H_s[search_start:search_end]
        
        # Find first decreasing point (H_s[t] > H_s[t+1])
        for i in range(len(H_s_window) - 1):
            if H_s_window[i] > H_s_window[i + 1]:
                return search_start + i
        
        return onset_beta_frame
