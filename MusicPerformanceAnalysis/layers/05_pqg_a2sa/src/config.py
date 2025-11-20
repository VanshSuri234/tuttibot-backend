"""
Default configuration parameters for PQG-A2SA pipeline
Based on paper's best settings (Section 8 of detailed notes)
"""

import numpy as np


class PQGConfig:
    """Configuration class with all default parameters"""
    
    # Audio feature extraction
    SAMPLE_RATE = 44100
    FRAME_SIZE = 2048  # ~46ms at 44.1kHz
    HOP_LENGTH = 1024  # ~23ms at 44.1kHz
    N_CHROMA = 12
    
    # CQT parameters
    FMIN = 32.70  # C1
    N_BINS = 84  # 7 octaves
    BINS_PER_OCTAVE = 12
    
    # VIDTW clustering
    K_CL = 10  # Clusters per chord
    
    # IOI-Guided Modification
    IOI_DELTA = 4  # ±4 chords for local velocity
    R_LOW = 0.6
    R_HIGH = 1.67  # 1/R_LOW
    FINE_GRID_RESOLUTION = 0.02  # beats
    
    # Score-informed NMF
    NMF_ITERATIONS = 150
    NMF_GAMMA = 1.0  # log compression exponent
    ONSET_TOLERANCE_MS = 150
    OFFSET_TOLERANCE_MS = 200
    
    # Articulation detection
    K_REST = 0.15  # Rest detection threshold
    K_OFF = 0.65   # Offset detection (0.6-0.7)
    K_ON = 0.2     # Onset detection
    T_S_MS = 150   # Staccato gap minimum (ms)
    T_L_MS = 30    # Legato window (ms)
    
    # Evaluation thresholds
    EVAL_THRESHOLDS_MS = [30, 60, 90, 120, 150, 180, 200]
    
    @classmethod
    def ms_to_frames(cls, ms):
        """Convert milliseconds to frame count"""
        return int(ms * cls.SAMPLE_RATE / (cls.HOP_LENGTH * 1000))
    
    @classmethod
    def frames_to_ms(cls, frames):
        """Convert frame count to milliseconds"""
        return frames * cls.HOP_LENGTH * 1000 / cls.SAMPLE_RATE
    
    @classmethod
    def frames_to_seconds(cls, frames):
        """Convert frame count to seconds"""
        return frames * cls.HOP_LENGTH / cls.SAMPLE_RATE
    
    @classmethod
    def seconds_to_frames(cls, seconds):
        """Convert seconds to frame count"""
        return int(seconds * cls.SAMPLE_RATE / cls.HOP_LENGTH)
