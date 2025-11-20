#!/usr/bin/env python3
"""
Audio Pitch Extractor - Extract F0 (fundamental frequency) from audio

CPU-optimized implementation using:
- librosa.pyin (primary - pure Python, no GPU needed)
- CREPE (secondary - can run on CPU)

Repository: https://github.com/librosa/librosa
"""

import json
import numpy as np
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

try:
    import librosa
    import soundfile as sf
except ImportError:
    raise ImportError("librosa and soundfile required. Install with: pip install librosa soundfile")


@dataclass
class PitchFrame:
    """Represents pitch at a single time frame"""
    time: float
    frequency: float  # Hz (NaN if unvoiced)
    confidence: float  # 0-1
    is_voiced: bool


class AudioPitchExtractor:
    """Extract pitch (F0) from audio files - CPU optimized"""
    
    def __init__(self, 
                 sample_rate: int = 22050,
                 hop_length: int = 512,
                 fmin: float = 65.0,  # C2
                 fmax: float = 2093.0,  # C7
                 method: str = 'pyin',  # 'pyin' or 'crepe'
                 confidence_threshold: float = 0.5,
                 verbose: bool = True):
        """
        Initialize audio pitch extractor
        
        Args:
            sample_rate: Target sample rate for analysis
            hop_length: Hop length in samples (affects time resolution)
            fmin: Minimum frequency to detect (Hz)
            fmax: Maximum frequency to detect (Hz)
            method: Pitch extraction method ('pyin' or 'crepe')
            confidence_threshold: Minimum confidence to consider a frame voiced
            verbose: Whether to print progress messages (default: True)
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.fmin = fmin
        self.fmax = fmax
        self.method = method.lower()
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        
        self.audio = None
        self.audio_sr = None
        self.pitch_frames: List[PitchFrame] = []
        
        # Validate method
        if self.method not in ['pyin', 'crepe']:
            warnings.warn(f"Unknown method '{method}', defaulting to 'pyin'")
            self.method = 'pyin'
        
        # Check CREPE availability
        if self.method == 'crepe':
            try:
                import crepe
                self.crepe = crepe
                if self.verbose:
                    print("CREPE available (will use CPU mode)")
            except ImportError:
                warnings.warn("CREPE not available, falling back to pyin")
                self.method = 'pyin'
    
    def load_audio(self, audio_path: str) -> None:
        """
        Load audio file
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if self.verbose:
            print(f"Loading audio: {audio_path.name}")
        
        # Load audio with librosa
        self.audio, self.audio_sr = librosa.load(
            str(audio_path),
            sr=self.sample_rate,
            mono=True
        )
        
        duration = len(self.audio) / self.audio_sr
        if self.verbose:
            print(f"Audio loaded: {duration:.2f} seconds at {self.audio_sr} Hz")
    
    def extract_pitch_pyin(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract pitch using librosa's pYIN algorithm (CPU-friendly)
        
        Returns:
            Tuple of (frequencies, confidences) arrays
        """
        if self.verbose:
            print("Extracting pitch using pYIN (probabilistic YIN)...")
        
        # Use librosa.pyin for pitch tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            self.audio,
            fmin=self.fmin,
            fmax=self.fmax,
            sr=self.audio_sr,
            hop_length=self.hop_length,
            frame_length=self.hop_length * 4,  # Standard window size
            fill_na=None  # Keep NaN for unvoiced regions
        )
        
        # voiced_probs is our confidence measure
        confidences = voiced_probs
        
        if self.verbose:
            print(f"pYIN extraction complete")
        
        return f0, confidences
    
    def extract_pitch_crepe(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract pitch using CREPE algorithm (works on CPU, slower)
        
        Returns:
            Tuple of (frequencies, confidences) arrays
        """
        if self.verbose:
            print("Extracting pitch using CREPE (CPU mode)...")
            print("Note: CREPE on CPU is slower, consider using pyin for faster results")
        
        # CREPE expects 16kHz audio, but can work with other sample rates
        time, frequency, confidence, activation = self.crepe.predict(
            self.audio,
            sr=self.audio_sr,
            model_capacity='tiny',  # Use tiny model for speed
            viterbi=True,  # Use Viterbi decoding for smoother results
            center=True,
            step_size=int(1000 * self.hop_length / self.audio_sr),  # in milliseconds
            verbose=0
        )
        
        if self.verbose:
            print(f"CREPE extraction complete")
        
        return frequency, confidence
    
    def extract_pitch(self) -> List[PitchFrame]:
        """
        Extract pitch from loaded audio
        
        Returns:
            List of PitchFrame objects
        """
        if self.audio is None:
            raise ValueError("No audio loaded. Call load_audio() first.")
        
        # Extract pitch using selected method
        if self.method == 'pyin':
            frequencies, confidences = self.extract_pitch_pyin()
        elif self.method == 'crepe':
            frequencies, confidences = self.extract_pitch_crepe()
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        # Convert to time-frequency frames
        times = librosa.frames_to_time(
            np.arange(len(frequencies)),
            sr=self.audio_sr,
            hop_length=self.hop_length
        )
        
        # Create PitchFrame objects
        self.pitch_frames = []
        voiced_count = 0
        
        for t, f, c in zip(times, frequencies, confidences):
            is_voiced = (not np.isnan(f)) and (c >= self.confidence_threshold)
            
            if is_voiced:
                voiced_count += 1
            
            frame = PitchFrame(
                time=float(t),
                frequency=float(f) if not np.isnan(f) else float('nan'),
                confidence=float(c),
                is_voiced=is_voiced
            )
            self.pitch_frames.append(frame)
        
        if self.verbose:
            voiced_percentage = (voiced_count / len(self.pitch_frames)) * 100
            print(f"Extracted {len(self.pitch_frames)} pitch frames")
            print(f"   Voiced frames: {voiced_count}/{len(self.pitch_frames)} ({voiced_percentage:.1f}%)")
        
        return self.pitch_frames
    
    def get_pitch_at_time(self, time: float, window: float = 0.05) -> Optional[float]:
        """
        Get the pitch (frequency) at a specific time
        
        Args:
            time: Time in seconds
            window: Time window around target time (seconds)
            
        Returns:
            Median frequency in the window, or None if no voiced frames
        """
        # Find frames within the time window
        frames_in_window = [
            frame for frame in self.pitch_frames
            if abs(frame.time - time) <= window / 2 and frame.is_voiced
        ]
        
        if not frames_in_window:
            return None
        
        # Return median frequency (more robust than mean)
        frequencies = [f.frequency for f in frames_in_window]
        return float(np.median(frequencies))
    
    def get_pitch_in_range(self, start_time: float, end_time: float) -> Dict:
        """
        Get pitch statistics for a time range
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Dictionary with pitch statistics
        """
        # Find frames in the time range
        frames_in_range = [
            frame for frame in self.pitch_frames
            if start_time <= frame.time <= end_time and frame.is_voiced
        ]
        
        if not frames_in_range:
            return {
                'median_frequency': None,
                'mean_frequency': None,
                'std_frequency': None,
                'min_frequency': None,
                'max_frequency': None,
                'confidence_mean': 0.0,
                'voiced_ratio': 0.0,
                'frame_count': 0
            }
        
        frequencies = [f.frequency for f in frames_in_range]
        confidences = [f.confidence for f in frames_in_range]
        
        # Total frames in range (including unvoiced)
        total_frames_in_range = len([
            f for f in self.pitch_frames
            if start_time <= f.time <= end_time
        ])
        
        return {
            'median_frequency': float(np.median(frequencies)),
            'mean_frequency': float(np.mean(frequencies)),
            'std_frequency': float(np.std(frequencies)),
            'min_frequency': float(np.min(frequencies)),
            'max_frequency': float(np.max(frequencies)),
            'confidence_mean': float(np.mean(confidences)),
            'voiced_ratio': len(frames_in_range) / max(total_frames_in_range, 1),
            'frame_count': len(frames_in_range)
        }
    
    def estimate_tuning(self) -> float:
        """
        Estimate tuning deviation from A440
        
        Returns:
            Tuning offset in semitones (positive = sharp, negative = flat)
        """
        if self.audio is None:
            raise ValueError("No audio loaded")
        
        if self.verbose:
            print("Estimating tuning...")
        tuning_offset = librosa.estimate_tuning(y=self.audio, sr=self.audio_sr)
        
        if self.verbose:
            print(f"   Tuning offset: {tuning_offset:+.2f} semitones from A440")
        
        return float(tuning_offset)
    
    def save_to_json(self, output_path: str) -> None:
        """
        Save extracted pitch data to JSON file
        
        Args:
            output_path: Path to output JSON file
        """
        # Calculate statistics
        voiced_frames = [f for f in self.pitch_frames if f.is_voiced]
        frequencies = [f.frequency for f in voiced_frames]
        confidences = [f.confidence for f in voiced_frames]
        
        output_data = {
            'metadata': {
                'method': self.method,
                'sample_rate': self.sample_rate,
                'hop_length': self.hop_length,
                'fmin': self.fmin,
                'fmax': self.fmax,
                'confidence_threshold': self.confidence_threshold,
                'total_frames': len(self.pitch_frames),
                'voiced_frames': len(voiced_frames),
                'voiced_percentage': (len(voiced_frames) / len(self.pitch_frames) * 100) if self.pitch_frames else 0
            },
            'statistics': {
                'frequency_range_hz': {
                    'min': float(np.min(frequencies)) if frequencies else None,
                    'max': float(np.max(frequencies)) if frequencies else None,
                    'mean': float(np.mean(frequencies)) if frequencies else None,
                    'median': float(np.median(frequencies)) if frequencies else None,
                    'std': float(np.std(frequencies)) if frequencies else None
                },
                'confidence': {
                    'mean': float(np.mean(confidences)) if confidences else 0,
                    'min': float(np.min(confidences)) if confidences else 0,
                    'max': float(np.max(confidences)) if confidences else 0
                }
            },
            'frames': [
                {
                    'time': float(f.time),
                    'frequency': float(f.frequency) if not np.isnan(f.frequency) else None,
                    'confidence': float(f.confidence),
                    'is_voiced': bool(f.is_voiced)
                }
                for f in self.pitch_frames
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        if self.verbose:
            print(f"Pitch data saved to: {output_path}")


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract pitch from audio files')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--method', choices=['pyin', 'crepe'], default='pyin',
                       help='Pitch extraction method (default: pyin)')
    parser.add_argument('--fmin', type=float, default=65.0,
                       help='Minimum frequency in Hz (default: 65)')
    parser.add_argument('--fmax', type=float, default=2093.0,
                       help='Maximum frequency in Hz (default: 2093)')
    parser.add_argument('--estimate-tuning', action='store_true',
                       help='Estimate tuning deviation')
    
    args = parser.parse_args()
    
    # Extract pitch
    extractor = AudioPitchExtractor(
        method=args.method,
        fmin=args.fmin,
        fmax=args.fmax
    )
    extractor.load_audio(args.audio)
    
    # Estimate tuning if requested
    if args.estimate_tuning:
        tuning = extractor.estimate_tuning()
    
    # Extract pitch
    frames = extractor.extract_pitch()
    
    # Save to JSON if specified
    if args.output:
        extractor.save_to_json(args.output)
    
    # Print sample
    print("\nFirst 5 voiced frames:")
    voiced_frames = [f for f in frames if f.is_voiced][:5]
    for frame in voiced_frames:
        print(f"   t={frame.time:.3f}s: {frame.frequency:.2f} Hz (conf={frame.confidence:.2f})")


if __name__ == '__main__':
    main()
