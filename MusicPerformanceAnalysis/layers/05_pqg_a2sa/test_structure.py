"""
Simple test to verify the pipeline structure
"""

import sys
import os

# Test imports
print("Testing PQG-A2SA implementation...")
print("=" * 60)

try:
    print("✓ Importing modules from src package...")
    from src import (
        PQGConfig,
        AudioFeatures,
        ScoreParser,
        VIDTW,
        IOIGuidedModification,
        ScoreInformedNMF,
        ArticulationRefinement,
        Evaluator,
        PQGAligner
    )
    
    print("\n" + "=" * 60)
    print("✅ All modules imported successfully!")
    print("=" * 60)
    
    # Test instantiation
    print("\nTesting module instantiation...")
    config = PQGConfig()
    print(f"  Config: HOP_LENGTH={config.HOP_LENGTH}, K_CL={config.K_CL}")
    
    aligner = PQGAligner(config)
    print(f"  PQGAligner instantiated with {len(dir(aligner))} attributes")
    
    print("\n" + "=" * 60)
    print("✅ Implementation structure is valid!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Place audio (.wav) and MIDI (.mid) files in data/")
    print("  2. Run: python example.py")
    print("  3. Check results/ for output")
    print("=" * 60)
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nMake sure you've installed all dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
