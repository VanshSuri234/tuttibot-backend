#!/usr/bin/env python3
"""
Metric Utilities - Common metric computation functions
======================================================

Shared functions for computing performance metrics across analyzers.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from scipy.stats import pearsonr
from scipy.spatial.distance import euclidean


def compute_onset_errors(score_onsets: List[float], 
                         perf_onsets: List[float],
                         time_map: Optional[List[Dict]] = None) -> Dict:
    """
    Compute onset timing errors
    
    Args:
        score_onsets: Expected onset times from score
        perf_onsets: Actual onset times from performance
        time_map: Optional alignment time map for correction
        
    Returns:
        Dictionary with error statistics
    """
    if not score_onsets or not perf_onsets:
        return {
            'mean_absolute_error_ms': None,
            'std_error_ms': None,
            'max_error_ms': None,
            'percentage_within_50ms': None,
            'percentage_within_100ms': None,
            'error_distribution': []
        }
    
    # Align onsets using time map if available
    errors = []
    
    if time_map:
        # Use time map for alignment
        for score_onset in score_onsets:
            # Find corresponding performance time
            perf_time = map_score_to_perf_time(score_onset, time_map)
            if perf_time is not None:
                # Find nearest performance onset
                nearest_perf = min(perf_onsets, key=lambda x: abs(x - perf_time))
                error = (nearest_perf - perf_time) * 1000  # Convert to ms
                errors.append(error)
    else:
        # Simple alignment by order
        min_len = min(len(score_onsets), len(perf_onsets))
        for i in range(min_len):
            error = (perf_onsets[i] - score_onsets[i]) * 1000  # ms
            errors.append(error)
    
    if not errors:
        return {
            'mean_absolute_error_ms': None,
            'std_error_ms': None,
            'max_error_ms': None,
            'percentage_within_50ms': None,
            'percentage_within_100ms': None,
            'error_distribution': []
        }
    
    errors_abs = [abs(e) for e in errors]
    
    return {
        'mean_absolute_error_ms': float(np.mean(errors_abs)),
        'std_error_ms': float(np.std(errors)),
        'max_error_ms': float(np.max(errors_abs)),
        'percentage_within_50ms': float(sum(1 for e in errors_abs if e <= 50) / len(errors) * 100),
        'percentage_within_100ms': float(sum(1 for e in errors_abs if e <= 100) / len(errors) * 100),
        'error_distribution': [float(e) for e in errors]
    }


def compute_pitch_errors(score_pitches: List[int],
                         perf_pitches: List[int],
                         alignment_indices: Optional[List[Tuple[int, int]]] = None) -> Dict:
    """
    Compute pitch accuracy errors
    
    Args:
        score_pitches: Expected MIDI pitches
        perf_pitches: Performed MIDI pitches
        alignment_indices: Optional list of (score_idx, perf_idx) pairs
        
    Returns:
        Dictionary with pitch error statistics
    """
    if not score_pitches or not perf_pitches:
        return {
            'mean_pitch_error_cents': None,
            'std_pitch_error_cents': None,
            'pitch_match_rate': None,
            'out_of_tune_notes_count': None,
            'error_distribution': []
        }
    
    errors_semitones = []
    
    if alignment_indices:
        # Use provided alignment
        for score_idx, perf_idx in alignment_indices:
            if score_idx < len(score_pitches) and perf_idx < len(perf_pitches):
                error = perf_pitches[perf_idx] - score_pitches[score_idx]
                errors_semitones.append(error)
    else:
        # Simple alignment by order
        min_len = min(len(score_pitches), len(perf_pitches))
        for i in range(min_len):
            error = perf_pitches[i] - score_pitches[i]
            errors_semitones.append(error)
    
    if not errors_semitones:
        return {
            'mean_pitch_error_cents': None,
            'std_pitch_error_cents': None,
            'pitch_match_rate': None,
            'out_of_tune_notes_count': None,
            'error_distribution': []
        }
    
    # Convert to cents (1 semitone = 100 cents)
    errors_cents = [e * 100 for e in errors_semitones]
    errors_abs_cents = [abs(e) for e in errors_cents]
    
    # Pitch match rate (within 50 cents = half semitone)
    matches = sum(1 for e in errors_abs_cents if e <= 50)
    pitch_match_rate = (matches / len(errors_cents)) * 100
    
    # Out of tune notes (> 50 cents)
    out_of_tune = sum(1 for e in errors_abs_cents if e > 50)
    
    return {
        'mean_pitch_error_cents': float(np.mean(errors_abs_cents)),
        'std_pitch_error_cents': float(np.std(errors_cents)),
        'pitch_match_rate': float(pitch_match_rate),
        'out_of_tune_notes_count': int(out_of_tune),
        'error_distribution': [float(e) for e in errors_cents]
    }


def compute_ioi_correlation(score_onsets: List[float],
                            perf_onsets: List[float]) -> float:
    """
    Compute Inter-Onset Interval correlation
    
    Args:
        score_onsets: Score onset times
        perf_onsets: Performance onset times
        
    Returns:
        Pearson correlation coefficient
    """
    if len(score_onsets) < 2 or len(perf_onsets) < 2:
        return None
    
    # Compute IOIs
    score_ioi = np.diff(score_onsets)
    perf_ioi = np.diff(perf_onsets)
    
    # Use minimum length
    min_len = min(len(score_ioi), len(perf_ioi))
    if min_len < 2:
        return None
    
    try:
        correlation, _ = pearsonr(score_ioi[:min_len], perf_ioi[:min_len])
        return float(correlation)
    except:
        return None


def compute_tempo_stability(tempo_curve: List[float]) -> Dict:
    """
    Compute tempo stability metrics
    
    Args:
        tempo_curve: Tempo values over time (BPM)
        
    Returns:
        Dictionary with stability metrics
    """
    if not tempo_curve or len(tempo_curve) < 2:
        return {
            'mean_tempo_bpm': None,
            'std_tempo_bpm': None,
            'coefficient_of_variation': None,
            'tempo_drift': None,
            'sudden_changes': None
        }
    
    tempo_array = np.array(tempo_curve)
    mean_tempo = float(np.mean(tempo_array))
    std_tempo = float(np.std(tempo_array))
    cv = std_tempo / mean_tempo if mean_tempo > 0 else None
    
    # Linear trend (drift)
    x = np.arange(len(tempo_array))
    drift = float(np.polyfit(x, tempo_array, 1)[0])  # Slope
    
    # Count sudden changes (> 10% change between adjacent points)
    diffs = np.abs(np.diff(tempo_array))
    threshold = mean_tempo * 0.10
    sudden_changes = int(np.sum(diffs > threshold))
    
    return {
        'mean_tempo_bpm': mean_tempo,
        'std_tempo_bpm': std_tempo,
        'coefficient_of_variation': float(cv) if cv is not None else None,
        'tempo_drift': drift,
        'sudden_changes': sudden_changes
    }


def compute_dynamic_range(rms_energy: List[float]) -> float:
    """
    Compute dynamic range in dB
    
    Args:
        rms_energy: RMS energy values
        
    Returns:
        Dynamic range in dB
    """
    if not rms_energy:
        return None
    
    energy_array = np.array(rms_energy)
    energy_array = energy_array[energy_array > 0]  # Remove zeros
    
    if len(energy_array) == 0:
        return None
    
    max_energy = np.max(energy_array)
    min_energy = np.min(energy_array)
    
    if min_energy == 0:
        return None
    
    dynamic_range_db = 20 * np.log10(max_energy / min_energy)
    return float(dynamic_range_db)


def map_score_to_perf_time(score_time: float, time_map: List[Dict]) -> Optional[float]:
    """
    Map score time to performance time using time map
    
    Args:
        score_time: Time in score (seconds)
        time_map: List of {'score': float, 'perf': float} mappings
        
    Returns:
        Corresponding performance time or None
    """
    if not time_map:
        return None
    
    # Handle different time map formats
    if isinstance(time_map[0], dict):
        # Format: [{'score': s, 'perf': p}, ...]
        score_times = [m.get('score', m.get('score_time', 0)) for m in time_map]
        perf_times = [m.get('perf', m.get('perf_time', m.get('performance_time', 0))) for m in time_map]
    elif isinstance(time_map[0], (list, tuple)):
        # Format: [[s, p], ...]
        score_times = [m[0] for m in time_map]
        perf_times = [m[1] for m in time_map]
    else:
        return None
    
    # Linear interpolation
    perf_time = np.interp(score_time, score_times, perf_times)
    return float(perf_time)


def compute_spectral_stability(spectral_values: List[float]) -> float:
    """
    Compute stability of spectral features
    
    Args:
        spectral_values: Spectral feature values over time
        
    Returns:
        Coefficient of variation (lower = more stable)
    """
    if not spectral_values or len(spectral_values) < 2:
        return None
    
    mean_val = np.mean(spectral_values)
    std_val = np.std(spectral_values)
    
    if mean_val == 0:
        return None
    
    cv = std_val / mean_val
    return float(cv)


def normalize_to_percent(value: float, min_val: float, max_val: float, 
                         invert: bool = False) -> float:
    """
    Normalize value to 0-100 percentage scale
    
    Args:
        value: Value to normalize
        min_val: Minimum expected value
        max_val: Maximum expected value
        invert: If True, invert scale (lower is better)
        
    Returns:
        Normalized percentage (0-100)
    """
    if value is None:
        return None
    
    # Clip to range
    value = max(min_val, min(max_val, value))
    
    # Normalize to 0-1
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)
    
    # Invert if needed
    if invert:
        normalized = 1.0 - normalized
    
    # Convert to percentage
    return float(normalized * 100)


def interpret_score(score: float, thresholds: Dict[str, Tuple[float, float]]) -> str:
    """
    Interpret numerical score as quality level
    
    Args:
        score: Numerical score (0-100)
        thresholds: Dict of {'excellent': (90, 100), 'good': (75, 90), ...}
        
    Returns:
        Interpretation string
    """
    if score is None:
        return "unknown"
    
    for level, (min_val, max_val) in sorted(thresholds.items(), 
                                            key=lambda x: -x[1][0]):
        if min_val <= score <= max_val:
            return level
    
    return "unknown"
