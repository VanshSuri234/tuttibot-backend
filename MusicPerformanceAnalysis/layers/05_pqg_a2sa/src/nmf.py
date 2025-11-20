"""
Score-informed NMF module
- Build spectral template matrix W from score pitches
- Initialize activation matrix H using refined chord alignment
- Decompose ensemble spectrogram V ≈ W·H
"""

import numpy as np
from sklearn.decomposition import NMF as SklearnNMF
from .config import PQGConfig


class ScoreInformedNMF:
    """Non-negative Matrix Factorization guided by score information"""
    
    def __init__(self, config=None):
        self.config = config or PQGConfig()
    
    def build_template_matrix(self, instruments, n_freq_bins):
        """
        Build W matrix from score instrument/pitch information
        
        Args:
            instruments: list of instrument dicts from ScoreParser
            n_freq_bins: number of frequency bins in spectrogram
        
        Returns:
            W: (n_freq_bins, n_templates) template matrix
            template_map: list of (inst_idx, pitch) tuples for each column
        """
        template_map = []
        templates = []
        
        # For each instrument, create templates for each pitch used
        for inst in instruments:
            inst_idx = inst['index']
            pitches = sorted(set(note['pitch'] for note in inst['notes']))
            
            for pitch in pitches:
                template = self._create_pitch_template(pitch, n_freq_bins)
                templates.append(template)
                template_map.append((inst_idx, pitch))
        
        # Add background/noise template
        noise_template = np.ones(n_freq_bins) / np.sqrt(n_freq_bins)
        templates.append(noise_template)
        template_map.append((-1, -1))  # -1 indicates background
        
        W = np.column_stack(templates)
        
        # Max-normalize each column
        W = W / (W.max(axis=0, keepdims=True) + 1e-8)
        
        return W, template_map
    
    def _create_pitch_template(self, midi_pitch, n_freq_bins):
        """
        Create a simple harmonic template for a MIDI pitch
        
        More sophisticated version would use actual instrument samples
        """
        template = np.zeros(n_freq_bins)
        
        # Map MIDI to frequency
        f0 = 440.0 * (2.0 ** ((midi_pitch - 69) / 12.0))
        
        # Assuming FFT with standard parameters
        sr = self.config.SAMPLE_RATE
        fft_size = self.config.FRAME_SIZE
        
        # Add harmonics (fundamental + overtones)
        for harmonic in [1, 2, 3, 4, 5]:
            freq = f0 * harmonic
            bin_idx = int(freq * fft_size / sr)
            
            if 0 <= bin_idx < n_freq_bins:
                # Gaussian envelope around the bin
                amplitude = 1.0 / harmonic  # Decay with harmonic number
                
                for offset in range(-2, 3):
                    idx = bin_idx + offset
                    if 0 <= idx < n_freq_bins:
                        weight = np.exp(-0.5 * (offset ** 2))
                        template[idx] += amplitude * weight
        
        # Normalize
        norm = np.linalg.norm(template)
        if norm > 0:
            template = template / norm
        
        return template
    
    def initialize_activations(self, template_map, instruments, 
                               chord_onsets_refined, n_frames, frame_times):
        """
        Initialize H matrix using refined chord alignment
        
        Args:
            template_map: list of (inst_idx, pitch) from build_template_matrix
            instruments: instrument data with note lists
            chord_onsets_refined: (n_chords,) refined onset times
            n_frames: total number of frames
            frame_times: (n_frames,) frame times in seconds
        
        Returns:
            H: (n_templates, n_frames) initialized activation matrix
        """
        n_templates = len(template_map)
        H = np.zeros((n_templates, n_frames))
        
        # Convert tolerances to seconds
        onset_tol = self.config.ONSET_TOLERANCE_MS / 1000.0
        offset_tol = self.config.OFFSET_TOLERANCE_MS / 1000.0
        
        # For each template, activate frames where corresponding note is expected
        for template_idx, (inst_idx, pitch) in enumerate(template_map):
            if inst_idx == -1:  # Background template
                H[template_idx, :] = 0.1  # Low constant activation
                continue
            
            # Find instrument
            inst = next((i for i in instruments if i['index'] == inst_idx), None)
            if inst is None:
                continue
            
            # Find notes with this pitch
            for note in inst['notes']:
                if note['pitch'] != pitch:
                    continue
                
                # Expected onset/offset times (with tolerance)
                onset_start = note['onset'] - onset_tol
                onset_end = note['onset'] + onset_tol
                offset_start = note['offset'] - offset_tol
                offset_end = note['offset'] + offset_tol
                
                # Find frame range
                frame_start = np.searchsorted(frame_times, onset_start)
                frame_end = np.searchsorted(frame_times, offset_end)
                
                # Activate frames
                H[template_idx, frame_start:frame_end] = 1.0
        
        return H
    
    def decompose(self, V, W, H_init, n_iter=None):
        """
        Run NMF to refine H given V and W
        
        Args:
            V: (n_freq_bins, n_frames) magnitude spectrogram
            W: (n_freq_bins, n_templates) template matrix (fixed)
            H_init: (n_templates, n_frames) initial activations
            n_iter: number of iterations (default from config)
        
        Returns:
            H: (n_templates, n_frames) refined activations
            W_normalized: W with max-normalized columns
        """
        n_iter = n_iter or self.config.NMF_ITERATIONS
        
        # Ensure consistent dtypes
        V = V.astype(np.float64)
        W = W.astype(np.float64)
        H_init = H_init.astype(np.float64)
        
        # Use manual multiplicative updates (fixed W, update H only)
        H = self._nmf_multiplicative_update(V, W, H_init, n_iter)
        
        # Max-normalize W columns for consistent activation scaling
        W_normalized = W / (W.max(axis=0, keepdims=True) + 1e-8)
        
        return H, W_normalized
    
    def _nmf_multiplicative_update(self, V, W, H, n_iter):
        """
        Manual NMF with multiplicative updates (W fixed, update H only)
        
        Update rule: H = H * (W^T V) / (W^T W H + eps)
        """
        eps = 1e-10
        H = H.copy()
        
        WtW = W.T @ W
        
        for _ in range(n_iter):
            WtV = W.T @ V
            H = H * WtV / (WtW @ H + eps)
        
        return H
    
    def get_instrument_activations(self, H, template_map, inst_idx):
        """
        Extract activations for a specific instrument
        
        Args:
            H: (n_templates, n_frames) activation matrix
            template_map: list of (inst_idx, pitch) tuples
            inst_idx: instrument index to extract
        
        Returns:
            inst_H: dict mapping pitch -> (n_frames,) activation vector
        """
        inst_H = {}
        
        for template_idx, (t_inst_idx, pitch) in enumerate(template_map):
            if t_inst_idx == inst_idx:
                inst_H[pitch] = H[template_idx, :]
        
        return inst_H
