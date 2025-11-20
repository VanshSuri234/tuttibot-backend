#!/usr/bin/env python3
"""
Example usage of PQG-A2SA pipeline
"""

from src.pipeline import PQGAligner
from src.config import PQGConfig


def main():
    """
    Example: align an audio performance to its score
    """
    # Configuration
    config = PQGConfig()
    
    # Initialize aligner
    aligner = PQGAligner(config)
    
    # Paths to your data
    audio_path = "data/example_performance.wav"
    midi_path = "data/example_score.mid"
    
    print("Starting PQG-A2SA alignment...")
    print(f"Audio: {audio_path}")
    print(f"Score: {midi_path}")
    
    # Run alignment
    results = aligner.align(audio_path, midi_path, verbose=True)
    
    # Access results
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    for inst in results['instruments']:
        print(f"\n{inst['name']}:")
        print(f"  Total notes: {len(inst['notes'])}")
        
        # Show first few refined notes
        for i, note in enumerate(inst['notes'][:5]):
            print(f"  Note {i+1}: pitch={note['pitch']}, "
                  f"onset={note['onset']:.3f}s, "
                  f"offset={note['offset']:.3f}s, "
                  f"articulation={note.get('articulation', 'N/A')}")
        
        if len(inst['notes']) > 5:
            print(f"  ... and {len(inst['notes'])-5} more notes")
    
    # Save results (optional)
    import json
    import numpy as np
    
    # Convert numpy arrays to lists for JSON serialization
    output = {
        'instruments': []
    }
    
    for inst in results['instruments']:
        output['instruments'].append({
            'name': inst['name'],
            'notes': inst['notes']
        })
    
    with open('results/alignment_output.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "="*60)
    print("Results saved to results/alignment_output.json")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
