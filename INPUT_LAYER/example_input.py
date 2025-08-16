#!/usr/bin/env python3
"""
Example usage and testing script for the Music Input Layer
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import our module
sys.path.insert(0, str(Path(__file__).parent))

from input_layer import MusicInputLayer, AudioInputProcessor, ScoreInputProcessor


def test_audio_processor():
    """Test the audio processor with various scenarios."""
    print("Testing Audio Processor")
    print("=" * 40)
    
    processor = AudioInputProcessor()
    
    # Test cases (you would replace these with actual file paths)
    test_cases = [
        "test_audio.wav",      # Standard format
        "test_audio.mp3",      # Needs conversion
        "nonexistent.wav",     # File not found
        "test_audio.flac",     # Different format
    ]
    
    for audio_file in test_cases:
        print(f"\nTesting: {audio_file}")
        result = processor.process_audio(audio_file)
        
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success'] and result['original_format']:
            fmt = result['original_format']
            print(f"Original: {fmt['sample_rate']}Hz, {fmt['channels']}ch, {fmt['format']}")
            print(f"Converted: {result['converted']}")
            if result['converted']:
                print(f"Output: {result['output_path']}")


def test_score_processor():
    """Test the score processor with various scenarios."""
    print("\n\nTesting Score Processor")
    print("=" * 40)
    
    processor = ScoreInputProcessor()
    
    # Test cases (you would replace these with actual file paths)
    test_cases = [
        "test_score.pdf",      # Needs OMR conversion
        "test_score.mid",      # MIDI - no conversion
        "test_score.xml",      # MusicXML - no conversion
        "nonexistent.pdf",     # File not found
        "test_score.txt",      # Unsupported format
    ]
    
    for score_file in test_cases:
        print(f"\nTesting: {score_file}")
        result = processor.process_score(score_file)
        
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success']:
            print(f"Format: {result['original_format']}")
            print(f"Converted: {result['converted']}")
            if result['converted']:
                print(f"Output: {result['output_path']}")


def test_full_pipeline():
    """Test the complete input layer pipeline."""
    print("\n\nTesting Complete Pipeline")
    print("=" * 40)
    
    input_layer = MusicInputLayer()
    
    # Example with mock files (replace with real files for actual testing)
    audio_file = "example_performance.wav"
    score_file = "example_score.pdf"
    
    print(f"Processing: {audio_file} + {score_file}")
    
    results = input_layer.process_inputs(audio_file, score_file)
    
    print(f"\nOverall Success: {results['overall_success']}")
    
    # Audio results
    audio_result = results['audio']
    print(f"\nAudio Processing:")
    print(f"  Success: {audio_result['success']}")
    print(f"  Message: {audio_result['message']}")
    
    # Score results  
    score_result = results['score']
    print(f"\nScore Processing:")
    print(f"  Success: {score_result['success']}")
    print(f"  Message: {score_result['message']}")


def create_sample_audio():
    """Create a sample audio file for testing (requires librosa and soundfile)."""
    try:
        import librosa
        import soundfile as sf
        import numpy as np
        
        print("\nCreating sample audio file...")
        
        # Generate a simple sine wave (440Hz A note for 3 seconds)
        sample_rate = 44100
        duration = 3.0
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Save as WAV file
        output_file = "sample_audio.wav"
        sf.write(output_file, audio_data, sample_rate, subtype='PCM_16')
        
        print(f"Created: {output_file}")
        print(f"Format: {sample_rate}Hz, 16-bit, mono")
        
        return output_file
        
    except ImportError:
        print("Cannot create sample audio - missing librosa/soundfile")
        return None


if __name__ == "__main__":
    print("Music Performance Evaluation - Input Layer Testing")
    print("=" * 60)
    
    # Test individual processors
    test_audio_processor()
    test_score_processor()
    
    # Test complete pipeline
    test_full_pipeline()
    
    # Create a sample audio file for testing
    print("\n" + "=" * 60)
    sample_file = create_sample_audio()
    
    if sample_file:
        print(f"\nYou can now test with the generated file:")
        print(f"python input_layer.py {sample_file} your_score.pdf")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("\nTo test with real files:")
    print("1. Place your audio and score files in this directory")
    print("2. Run: python input_layer.py <audio_file> <score_file>")
    print("3. Or modify the file paths in this example script")
    
    print("\nSupported formats:")
    print("Audio: .wav, .mp3, .flac, .aac, .ogg")
    print("Score: .pdf, .mid, .midi, .xml, .musicxml, .mxl")