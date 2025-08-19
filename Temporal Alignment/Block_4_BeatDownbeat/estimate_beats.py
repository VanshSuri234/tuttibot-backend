import argparse
import json
from beatnet import BeatNet
import soundfile as sf

# Helper to run BeatNet and save outputs
def estimate_beats(audio_path, beats_path):
    # Run BeatNet
    beatnet = BeatNet()
    beats, downbeats = beatnet.process(audio_path)
    # Format output
    beats_json = []
    for t in beats:
        beats_json.append({"t": t, "downbeat": 0})
    for t in downbeats:
        beats_json.append({"t": t, "downbeat": 1})
    beats_json = sorted(beats_json, key=lambda x: x["t"])
    with open(beats_path, 'w') as f:
        json.dump(beats_json, f, indent=2)
    print(f'Extracted {len(beats_json)} beats/downbeats.')
    return beats_json

def main():
    parser = argparse.ArgumentParser(description='Estimate beats and downbeats from audio using BeatNet')
    parser.add_argument('--audio', required=True, help='Path to perf.wav')
    parser.add_argument('--beats', default='beats.json', help='Output beats JSON file')
    args = parser.parse_args()
    estimate_beats(args.audio, args.beats)

if __name__ == '__main__':
    main()
