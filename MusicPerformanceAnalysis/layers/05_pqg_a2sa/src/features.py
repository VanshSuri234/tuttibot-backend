"""
Audio feature extraction module
- CQT-based chroma extraction
- Frame generation with ~23ms hop
- Temporal clustering for VIDTW
"""

import numpy as np
import librosa
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import normalize
from .config import PQGConfig


class AudioFeatures:
    """Extract audio features for PQG-A2SA pipeline"""
    
    def __init__(self, config=None):
        self.config = config or PQGConfig()
    
    def load_audio(self, audio_path):
        """Load audio file and return waveform"""
        y, sr = librosa.load(audio_path, sr=self.config.SAMPLE_RATE)
        return y, sr
    
    def extract_chroma_frames(self, y, sr=None):
        """
        Extract CQT-based chroma features per frame
        
        Returns:
            chroma: (12, n_frames) array of L2-normalized chroma
            times: (n_frames,) array of frame times in seconds
        """
        sr = sr or self.config.SAMPLE_RATE
        
        # Compute CQT
        C = np.abs(librosa.cqt(
            y, 
            sr=sr,
            hop_length=self.config.HOP_LENGTH,
            fmin=self.config.FMIN,
            n_bins=self.config.N_BINS,
            bins_per_octave=self.config.BINS_PER_OCTAVE
        ))
        
        # Aggregate to chroma (pitch classes)
        chroma = librosa.feature.chroma_cqt(
            C=C,
            sr=sr,
            hop_length=self.config.HOP_LENGTH,
            n_chroma=self.config.N_CHROMA
        )
        
        # L2 normalize each frame
        chroma = normalize(chroma, axis=0, norm='l2')
        
        # Frame times
        times = librosa.frames_to_time(
            np.arange(chroma.shape[1]),
            sr=sr,
            hop_length=self.config.HOP_LENGTH
        )
        
        return chroma, times
    
    def temporal_clustering(self, chroma, target_clusters):
        """
        Temporally-constrained agglomerative clustering
        Merges only ADJACENT frames to preserve time order
        
        Args:
            chroma: (12, n_frames) array
            target_clusters: desired number of clusters (L_cluster)
        
        Returns:
            cluster_chromas: (12, target_clusters) averaged chroma per cluster
            cluster_boundaries: (target_clusters + 1,) frame indices [start, end)
        """
        n_frames = chroma.shape[1]
        
        if target_clusters >= n_frames:
            # No clustering needed
            return chroma, np.arange(n_frames + 1)
        
        # Initialize: each frame is its own cluster
        clusters = [[i] for i in range(n_frames)]
        cluster_chromas_list = [chroma[:, i] for i in range(n_frames)]
        
        # Greedy merging of adjacent clusters
        while len(clusters) > target_clusters:
            # Compute pairwise distances between adjacent clusters
            min_dist = float('inf')
            min_idx = -1
            
            for i in range(len(clusters) - 1):
                dist = euclidean(cluster_chromas_list[i], cluster_chromas_list[i + 1])
                if dist < min_dist:
                    min_dist = dist
                    min_idx = i
            
            # Merge clusters at min_idx and min_idx+1
            merged_frames = clusters[min_idx] + clusters[min_idx + 1]
            merged_chroma = np.mean(chroma[:, merged_frames], axis=1)
            merged_chroma = merged_chroma / (np.linalg.norm(merged_chroma) + 1e-8)
            
            # Update lists
            clusters[min_idx] = merged_frames
            cluster_chromas_list[min_idx] = merged_chroma
            
            del clusters[min_idx + 1]
            del cluster_chromas_list[min_idx + 1]
        
        # Build output arrays
        cluster_chromas = np.column_stack(cluster_chromas_list)
        
        # Boundaries: start frame of each cluster + final end
        boundaries = np.array([cluster[0] for cluster in clusters] + [n_frames])
        
        return cluster_chromas, boundaries
    
    def compute_spectrogram(self, y, sr=None, log_compress=True):
        """
        Compute magnitude spectrogram with optional log compression
        
        Args:
            y: audio waveform
            sr: sample rate
            log_compress: if True, apply V = log(1 + |STFT|^gamma)
        
        Returns:
            V: magnitude spectrogram (n_bins, n_frames)
        """
        sr = sr or self.config.SAMPLE_RATE
        
        # STFT
        D = librosa.stft(
            y,
            n_fft=self.config.FRAME_SIZE,
            hop_length=self.config.HOP_LENGTH
        )
        
        V = np.abs(D)
        
        if log_compress:
            V = np.log1p(V ** self.config.NMF_GAMMA)
        
        return V
