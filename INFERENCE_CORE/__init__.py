"""
Inference Core Layer
====================

Bridge between feature extraction layers and Grading Layer.
Collects, processes, and formats data for performance grading.

Author: TuttiBot Team
Version: 1.0
"""

from .inference_core import InferenceCore
from .data_collector import DataCollector

__all__ = ['InferenceCore', 'DataCollector']
