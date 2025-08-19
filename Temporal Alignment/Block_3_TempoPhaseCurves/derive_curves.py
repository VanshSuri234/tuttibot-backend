import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import csv

def derive_curves(time_map_path, scoregraph_path, tempo_curve_path, phase_curve_path, diagnostics_path):
    # Load time_map.json
    with open(time_map_path, 'r') as f:
        time_map = json.load(f)
    path = time_map['path']
    # Load scoregraph.json
    with open(scoregraph_path, 'r') as f:
        scoregraph = json.load(f)
    nodes = scoregraph['nodes']
    # Compute tempo curve (finite differences)
    abs_beats = np.array([p[0] for p in path])
    perf_times = np.array([p[1] for p in path])
    d_abs_beat = np.diff(abs_beats)
    d_time = np.diff(perf_times)
    bpm = np.divide(d_abs_beat, d_time, out=np.zeros_like(d_abs_beat), where=d_time!=0) * 60
    abs_beat_mid = (abs_beats[:-1] + abs_beats[1:]) / 2
    # Save tempo_curve.csv
    with open(tempo_curve_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['abs_beat', 'bpm'])
        for ab, b in zip(abs_beat_mid, bpm):
            writer.writerow([ab, b])
    # Compute phase curve
    phase_curve = []
    for ab in abs_beats:
        # Find corresponding node
        node = min(nodes, key=lambda n: abs(n['abs_beat'] - ab))
        phi = (ab - node['abs_beat']) / node['D_beats'] if node['D_beats'] else 0
        phase_curve.append([ab, phi])
    # Save phase_curve.csv
    with open(phase_curve_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['abs_beat', 'phi'])
        for ab, phi in phase_curve:
            writer.writerow([ab, phi])
    # Plot diagnostics
    plt.plot(abs_beat_mid, bpm)
    plt.xlabel('abs_beat')
    plt.ylabel('BPM')
    plt.title('Tempo Curve')
    plt.savefig(diagnostics_path)
    plt.close()
    print(f'Tempo and phase curves saved. Diagnostics plot: {diagnostics_path}')

def main():
    parser = argparse.ArgumentParser(description='Derive tempo and phase curves from time map and scoregraph')
    parser.add_argument('--timemap', required=True, help='Path to time_map.json')
    parser.add_argument('--scoregraph', required=True, help='Path to scoregraph.json')
    parser.add_argument('--tempo', default='tempo_curve.csv', help='Output tempo curve CSV')
    parser.add_argument('--phase', default='phase_curve.csv', help='Output phase curve CSV')
    parser.add_argument('--diagnostics', default='diagnostics.png', help='Output diagnostics plot')
    args = parser.parse_args()
    derive_curves(args.timemap, args.scoregraph, args.tempo, args.phase, args.diagnostics)

if __name__ == '__main__':
    main()
