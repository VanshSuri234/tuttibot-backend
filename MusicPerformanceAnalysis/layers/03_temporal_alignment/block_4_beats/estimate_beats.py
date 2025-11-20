import argparse
import json
import numpy as np

def estimate_beats(audio_path, beats_path):
    """
    Estimate beats and downbeats from audio with confidence scores.
    
    Args:
        audio_path: Path to audio file
        beats_path: Path to save beats JSON
        
    Returns:
        List of beat dictionaries with time, downbeat flag, and confidence
    """
    try:
        from beatnet.model import BeatNet
        
        # Initialize BeatNet with offline mode
        beatnet = BeatNet(
            1,  # Model selection
            mode='offline',
            inference_model='DBN',
            plot=[],
            thread=False
        )
        
        # Process audio and get full output
        print(f'Processing audio: {audio_path}')
        output = beatnet.process(audio_path)
        
        # Extract beats with confidence scores
        beats_json = []
        
        if output is not None and len(output) > 0:
            # BeatNet output format: each row is [time, beat_position, confidence]
            for i, beat_info in enumerate(output):
                time_sec = float(beat_info[0])
                beat_position = int(beat_info[1]) if len(beat_info) > 1 else 0
                confidence = float(beat_info[2]) if len(beat_info) > 2 else 1.0
                
                # Ensure confidence is in valid range
                confidence = max(0.0, min(1.0, confidence))
                
                beats_json.append({
                    "t": round(time_sec, 4),
                    "downbeat": 1 if beat_position == 1 else 0,
                    "confidence": round(confidence, 4)
                })
        else:
            print('Warning: BeatNet returned no beats, using fallback method')
            # Fallback: generate beats at 120 BPM with default confidence
            import librosa
            y, sr = librosa.load(audio_path)
            duration = len(y) / sr
            beat_times = np.arange(0, duration, 0.5)  # 120 BPM
            
            for i, t in enumerate(beat_times):
                beats_json.append({
                    "t": round(float(t), 4),
                    "downbeat": 1 if i % 4 == 0 else 0,
                    "confidence": 0.5  # Default confidence for fallback
                })
        
        # Sort by time
        beats_json = sorted(beats_json, key=lambda x: x["t"])
        
        # Save to file
        with open(beats_path, 'w') as f:
            json.dump(beats_json, f, indent=2)
        
        # Print summary statistics
        total_beats = len(beats_json)
        downbeats = sum(1 for b in beats_json if b['downbeat'] == 1)
        avg_confidence = np.mean([b['confidence'] for b in beats_json])
        
        print(f'Extracted {total_beats} beats ({downbeats} downbeats)')
        print(f'Average confidence: {avg_confidence:.3f}')
        print(f'Saved to: {beats_path}')
        
        return beats_json
        
    except ImportError as e:
        print(f'Error: BeatNet not available. {e}')
        print('Please install: pip install beatnet')
        raise
    except Exception as e:
        print(f'Error processing audio: {e}')
        raise

def main():
    parser = argparse.ArgumentParser(description='Estimate beats and downbeats from audio using BeatNet')
    parser.add_argument('--audio', required=True, help='Path to perf.wav')
    parser.add_argument('--beats', default='beats.json', help='Output beats JSON file')
    args = parser.parse_args()
    estimate_beats(args.audio, args.beats)

if __name__ == '__main__':
    main()
