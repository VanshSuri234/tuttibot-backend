import argparse
import csv
import numpy as np
from matchmaker import ScoreFollower
import partitura
from partitura import load_score

def follow_online_sim(score_path, audio_path, trace_path):
    # Load score
    score = load_score(score_path)
    # Initialize Matchmaker ScoreFollower
    follower = ScoreFollower(score)
    # Simulate online following from audio file
    # (Assume follower.run returns a list of dicts with time_sec, score_abs_beat, bar, beat, conf)
    trace = follower.run(audio_path)
    # Save online_trace.csv
    with open(trace_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_sec', 'score_abs_beat', 'bar', 'beat', 'conf'])
        for row in trace:
            writer.writerow([row['time_sec'], row['score_abs_beat'], row['bar'], row['beat'], row['conf']])
    print(f'Online trace saved to {trace_path}')
    # Optionally: compare to time_map.json and compute mean absolute error
    # (User should provide time_map.json for validation)

def main():
    parser = argparse.ArgumentParser(description='Run Matchmaker online follower simulation')
    parser.add_argument('--score', required=True, help='Path to score.musicxml or score.mid')
    parser.add_argument('--audio', required=True, help='Path to perf.wav')
    parser.add_argument('--trace', default='online_trace.csv', help='Output online trace CSV')
    args = parser.parse_args()
    follow_online_sim(args.score, args.audio, args.trace)

if __name__ == '__main__':
    main()
