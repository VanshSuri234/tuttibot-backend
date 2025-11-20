"""
Main PQG-A2SA Pipeline
Orchestrates all modules: VIDTW → IOI-GM → NMF → Articulation
"""

import numpy as np
from .config import PQGConfig
from .features import AudioFeatures
from .score_parser import ScoreParser
from .vidtw import VIDTW
from .ioi_gm import IOIGuidedModification
from .nmf import ScoreInformedNMF
from .articulation import ArticulationRefinement
from .evaluation import Evaluator


class PQGAligner:
    """
    Complete PQG-A2SA audio-to-score alignment pipeline
    """
    
    def __init__(self, config=None):
        """
        Initialize with configuration
        
        Args:
            config: PQGConfig instance (uses defaults if None)
        """
        self.config = config or PQGConfig()
        
        # Initialize all modules
        self.audio_features = AudioFeatures(self.config)
        self.score_parser = ScoreParser()
        self.vidtw = VIDTW()
        self.ioi_gm = IOIGuidedModification(self.config)
        self.nmf = ScoreInformedNMF(self.config)
        self.articulation = ArticulationRefinement(self.config)
        self.evaluator = Evaluator(self.config.EVAL_THRESHOLDS_MS)
    
    def align(self, audio_path, midi_path, verbose=True):
        """
        Perform complete alignment pipeline
        
        Args:
            audio_path: path to ensemble audio file (WAV, MP3, etc.)
            midi_path: path to score MIDI file
            verbose: whether to print progress
        
        Returns:
            results: dict containing:
                - 'instruments': list of instrument dicts with refined notes
                - 'chord_onsets_refined': refined chord onset times
                - 'intermediate': dict with intermediate results for debugging
        """
        if verbose:
            print("\n" + "="*60)
            print("PQG-A2SA: Performance Quantification Guided Alignment")
            print("="*60)
        
        # ===== Stage 1: Feature Extraction =====
        if verbose:
            print("\n[1/6] Extracting audio features...")
        
        y, sr = self.audio_features.load_audio(audio_path)
        audio_chroma, frame_times = self.audio_features.extract_chroma_frames(y, sr)
        spectrogram = self.audio_features.compute_spectrogram(y, sr)
        
        if verbose:
            print(f"  - Audio: {len(y)/sr:.2f}s, {audio_chroma.shape[1]} frames")
        
        # ===== Stage 2: Score Parsing =====
        if verbose:
            print("\n[2/6] Parsing score...")
        
        midi_obj = self.score_parser.load_midi(midi_path)
        chords = self.score_parser.extract_chords(midi_obj)
        instruments = self.score_parser.extract_instrument_notes(midi_obj)
        score_chroma, chord_score_times = self.score_parser.get_chord_chroma_sequence(chords)
        
        if verbose:
            print(f"  - Score: {len(chords)} chords, {len(instruments)} instruments")
            for inst in instruments:
                print(f"    - {inst['name']}: {len(inst['notes'])} notes")
        
        # ===== Stage 3: VIDTW (Coarse Alignment) =====
        if verbose:
            print("\n[3/6] VIDTW: Coarse chord alignment...")
        
        # Temporal clustering
        target_clusters = int(np.ceil(self.config.K_CL * len(chords)))
        cluster_chroma, cluster_boundaries = self.audio_features.temporal_clustering(
            audio_chroma, target_clusters
        )
        
        if verbose:
            print(f"  - Clustered {audio_chroma.shape[1]} frames → {cluster_chroma.shape[1]} clusters")
        
        # DTW alignment
        cost, path, score_to_audio = self.vidtw.align(score_chroma, cluster_chroma)
        chord_onsets_preliminary = self.vidtw.get_chord_onset_times(
            score_to_audio, cluster_boundaries, frame_times
        )
        
        if verbose:
            print(f"  - DTW cost: {cost:.2f}")
            print(f"  - Preliminary chord onset times computed")
        
        # ===== Stage 4: IOI-GM (Refinement) =====
        if verbose:
            print("\n[4/6] IOI-GM: Refining tempo deviations...")
        
        chord_onsets_refined = self.ioi_gm.refine_alignment(
            chord_onsets_preliminary,
            chord_score_times,
            score_chroma,
            audio_chroma,
            frame_times
        )
        
        if verbose:
            diff = np.abs(chord_onsets_refined - chord_onsets_preliminary)
            print(f"  - Max adjustment: {diff.max()*1000:.2f} ms")
            print(f"  - Mean adjustment: {diff.mean()*1000:.2f} ms")
        
        # ===== Stage 5: Score-Informed NMF =====
        if verbose:
            print("\n[5/6] Score-informed NMF...")
        
        W, template_map = self.nmf.build_template_matrix(
            instruments, 
            spectrogram.shape[0]
        )
        
        H_init = self.nmf.initialize_activations(
            template_map,
            instruments,
            chord_onsets_refined,
            spectrogram.shape[1],
            frame_times
        )
        
        H, W_normalized = self.nmf.decompose(spectrogram, W, H_init)
        
        if verbose:
            print(f"  - Template matrix W: {W.shape}")
            print(f"  - Activation matrix H: {H.shape}")
            print(f"  - NMF iterations: {self.config.NMF_ITERATIONS}")
        
        # ===== Stage 6: Articulation Refinement =====
        if verbose:
            print("\n[6/6] Articulation-guided note refinement...")
        
        refined_instruments = []
        total_notes = 0
        
        for inst in instruments:
            inst_idx = inst['index']
            inst_activations = self.nmf.get_instrument_activations(H, template_map, inst_idx)
            
            refined_notes = self.articulation.refine_instrument_notes(
                inst,
                inst_activations,
                chord_onsets_refined,
                frame_times
            )
            
            refined_instruments.append({
                'name': inst['name'],
                'index': inst_idx,
                'notes': refined_notes,
                'original_notes': inst['notes']
            })
            
            total_notes += len(refined_notes)
            
            if verbose:
                n_staccato = sum(1 for n in refined_notes if n.get('articulation') == 'staccato')
                n_legato = sum(1 for n in refined_notes if n.get('articulation') == 'legato')
                print(f"  - {inst['name']}: {len(refined_notes)} notes "
                      f"(staccato: {n_staccato}, legato: {n_legato})")
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Alignment complete! Total notes refined: {total_notes}")
            print(f"{'='*60}\n")
        
        # Package results
        results = {
            'instruments': refined_instruments,
            'chord_onsets_refined': chord_onsets_refined,
            'chord_score_times': chord_score_times,
            'frame_times': frame_times,
            'intermediate': {
                'audio_chroma': audio_chroma,
                'score_chroma': score_chroma,
                'cluster_chroma': cluster_chroma,
                'cluster_boundaries': cluster_boundaries,
                'chord_onsets_preliminary': chord_onsets_preliminary,
                'spectrogram': spectrogram,
                'W': W_normalized,
                'H': H,
                'template_map': template_map
            }
        }
        
        return results
    
    def evaluate(self, results, ground_truth_notes_by_instrument):
        """
        Evaluate alignment results against ground truth
        
        Args:
            results: output from align()
            ground_truth_notes_by_instrument: dict mapping inst_idx -> list of ground truth notes
        
        Returns:
            evaluation_results: dict with metrics per instrument and overall
        """
        eval_results = {}
        
        for inst in results['instruments']:
            inst_idx = inst['index']
            
            if inst_idx in ground_truth_notes_by_instrument:
                predicted = inst['notes']
                ground_truth = ground_truth_notes_by_instrument[inst_idx]
                
                metrics = self.evaluator.evaluate_full(predicted, ground_truth)
                eval_results[inst['name']] = metrics
        
        # Compute overall metrics
        all_onset_errors = []
        all_offset_errors = []
        
        for metrics in eval_results.values():
            all_onset_errors.extend(metrics['onset_errors'])
            all_offset_errors.extend(metrics['offset_errors'])
        
        if all_onset_errors:
            overall_MNE = np.mean(all_onset_errors)
            overall_MFE = np.mean(all_offset_errors)
            overall_onset_rates = self.evaluator.compute_alignment_rates(
                np.array(all_onset_errors)
            )
            overall_offset_rates = self.evaluator.compute_alignment_rates(
                np.array(all_offset_errors)
            )
            
            eval_results['overall'] = {
                'MNE': overall_MNE,
                'MFE': overall_MFE,
                'onset_alignment_rates': overall_onset_rates,
                'offset_alignment_rates': overall_offset_rates,
                'n_notes': len(all_onset_errors)
            }
        
        return eval_results
