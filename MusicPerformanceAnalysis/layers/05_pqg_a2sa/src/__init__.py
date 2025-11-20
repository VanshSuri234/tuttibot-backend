"""
PQG-A2SA: Performance Quantification Guided Audio-to-Score Alignment
Implementation based on Lian-Cheng-Zhang (2023)
"""

__version__ = "1.0.0"
__author__ = "PQG-A2SA Implementation"

# Make imports available at package level
from .config import PQGConfig
from .features import AudioFeatures
from .score_parser import ScoreParser
from .vidtw import VIDTW
from .ioi_gm import IOIGuidedModification
from .nmf import ScoreInformedNMF
from .articulation import ArticulationRefinement
from .evaluation import Evaluator
from .pipeline import PQGAligner

__all__ = [
    'PQGConfig',
    'AudioFeatures',
    'ScoreParser',
    'VIDTW',
    'IOIGuidedModification',
    'ScoreInformedNMF',
    'ArticulationRefinement',
    'Evaluator',
    'PQGAligner'
]
