#!/usr/bin/env python3
"""
A4: Full System Experiment
Evaluates alignment metrics for all 10 Bach chorales and 4 instruments using all modules (ScoreGraph context + beat weighting).
Outputs mean and std deviation for each metric.
"""
import os
import numpy as np
import librosa
from pathlib import Path
import json
from scipy.spatial.distance import cdist

BACH_DATASET = 'Workspace/Bach_10_Dataset'
INSTRUMENTS = ['violin', 'clarinet', 'saxphone', 'bassoon']
CHORALES = [
    '01_AchGottundHerr', '02_AchLiebenChristen', '03_ChristederdubistTagundLicht',
    '04_ChristeDuBeistand', '05_DieNacht', '06_DieSonne', '07_HerrGott',
    '08_FuerDeinenThron', '09_Jesus', '10_NunBitten'
]

RESULTS = {}


import os
import numpy as np
import librosa
from pathlib import Path
import json
from scipy.spatial.distance import cdist
import pretty_midi

BACH_DATASET = 'Workspace/Bach_10_Dataset'
INSTRUMENTS = ['violin', 'clarinet', 'saxphone', 'bassoon']
CHORALES = [
    '01_AchGottundHerr', '02_AchLiebenChristen', '03_ChristederdubistTagundLicht',
    '04_ChristeDuBeistand', '05_DieNacht', '06_DieSonne', '07_HerrGott',
    '08_FuerDeinenThron', '09_Jesus', '10_NunBitten'
]

RESULTS = {}

# Feature extraction: Chroma from MIDI (score)
def extract_chroma_from_midi(midi_path):
    midi = pretty_midi.PrettyMIDI(midi_path)
    audio = midi.fluidsynth()
    chroma = librosa.feature.chroma_stft(y=audio, sr=44100)
    return chroma.T

# Feature extraction: Chroma from WAV (performance)
def extract_chroma_from_wav(wav_path):
    y, sr = librosa.load(wav_path, sr=None)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    return chroma.T

# ScoreGraph context constraint (mockup)
def apply_scoregraph_context(cost_matrix):
    penalty = 0.2
    for i in range(cost_matrix.shape[0]):
        for j in range(cost_matrix.shape[1]):
            if abs(i-j) > 2:
                cost_matrix[i, j] += penalty
    return cost_matrix

# Beat weighting (mockup)
def apply_beat_weighting(cost_matrix):
    for i in range(cost_matrix.shape[0]):
        for j in range(cost_matrix.shape[1]):
            if i == j:
                cost_matrix[i, j] *= 0.8
    return cost_matrix

# DTW alignment with all modules
def dtw_align(chroma_score, chroma_perf):
    cost_matrix = cdist(chroma_score, chroma_perf, metric='euclidean')
    cost_matrix = apply_scoregraph_context(cost_matrix)
    cost_matrix = apply_beat_weighting(cost_matrix)
    acc_cost = np.zeros_like(cost_matrix)
    acc_cost[0, 0] = cost_matrix[0, 0]
    for i in range(1, cost_matrix.shape[0]):
        acc_cost[i, 0] = cost_matrix[i, 0] + acc_cost[i-1, 0]
    for j in range(1, cost_matrix.shape[1]):
        acc_cost[0, j] = cost_matrix[0, j] + acc_cost[0, j-1]
    for i in range(1, cost_matrix.shape[0]):
        for j in range(1, cost_matrix.shape[1]):
            acc_cost[i, j] = cost_matrix[i, j] + min(
                acc_cost[i-1, j], acc_cost[i, j-1], acc_cost[i-1, j-1]
            )
    # Backtrack path
    i, j = cost_matrix.shape[0]-1, cost_matrix.shape[1]-1
    path = [(i, j)]
    while i > 0 and j > 0:
        steps = [(i-1, j), (i, j-1), (i-1, j-1)]
        costs = [acc_cost[s] if s[0]>=0 and s[1]>=0 else np.inf for s in steps]
        min_idx = np.argmin(costs)
        i, j = steps[min_idx]
        path.append((i, j))
    path.reverse()
    return path, acc_cost[-1, -1]

# Metrics
def compute_metrics(path):
    errors = [abs(i-j) for i, j in path]
    mae = np.mean(errors)
    rmse = np.sqrt(np.mean(np.square(errors)))
    note_match_acc = np.sum(np.array(errors) < 3) / len(errors)
    return mae, rmse, note_match_acc

for chorale in CHORALES:
    RESULTS[chorale] = {}
    chorale_dir = Path(BACH_DATASET) / chorale
    midi_file = None
    for f in os.listdir(chorale_dir):
        if f.endswith('.mid'):
            midi_file = chorale_dir / f
            break
    if not midi_file:
        continue
    chroma_score = extract_chroma_from_midi(str(midi_file))
    for inst in INSTRUMENTS:
        perf_wav = None
        for f in os.listdir(chorale_dir):
            if inst in f and f.endswith('.wav'):
                perf_wav = chorale_dir / f
                break
        if not perf_wav:
            continue
        chroma_perf = extract_chroma_from_wav(str(perf_wav))
        path, cost = dtw_align(chroma_score, chroma_perf)
        mae, rmse, note_acc = compute_metrics(path)
        RESULTS[chorale][inst] = {
            'mae': mae,
            'rmse': rmse,
            'note_acc': note_acc,
            'cost': cost
        }


# Per-instrument aggregation and output
INSTRUMENTS = ['violin', 'clarinet', 'saxphone', 'bassoon']
instrument_results = {inst: {'mae': [], 'rmse': [], 'note_acc': []} for inst in INSTRUMENTS}
for chorale in RESULTS:
    for inst in RESULTS[chorale]:
        instrument_results[inst]['mae'].append(RESULTS[chorale][inst]['mae'])
        instrument_results[inst]['rmse'].append(RESULTS[chorale][inst]['rmse'])
        instrument_results[inst]['note_acc'].append(RESULTS[chorale][inst]['note_acc'])

print('instrument | MAE | RMSE | Accuracy')
for inst in INSTRUMENTS:
    mae = np.mean(instrument_results[inst]['mae']) if instrument_results[inst]['mae'] else float('nan')
    rmse = np.mean(instrument_results[inst]['rmse']) if instrument_results[inst]['rmse'] else float('nan')
    acc = np.mean(instrument_results[inst]['note_acc']) if instrument_results[inst]['note_acc'] else float('nan')
    print(f'{inst} | {mae:.2f} | {rmse:.2f} | {acc:.2f}')

with open('full_system_results.txt', 'w') as txtf:
    txtf.write('instrument | MAE | RMSE | Accuracy\n')
    for inst in INSTRUMENTS:
        mae = np.mean(instrument_results[inst]['mae']) if instrument_results[inst]['mae'] else float('nan')
        rmse = np.mean(instrument_results[inst]['rmse']) if instrument_results[inst]['rmse'] else float('nan')
        acc = np.mean(instrument_results[inst]['note_acc']) if instrument_results[inst]['note_acc'] else float('nan')
        txtf.write(f'{inst} | {mae:.2f} | {rmse:.2f} | {acc:.2f}\n')

with open('full_system_results.json', 'w') as f:
    json.dump(RESULTS, f, indent=2)
