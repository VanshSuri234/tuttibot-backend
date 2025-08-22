#!/usr/bin/env python3
"""
Debug Basic Pitch - Find the exact output format
"""

from basic_pitch.inference import predict
import numpy as np

def debug_basic_pitch_output(audio_path):
    print("🔍 Debugging Basic Pitch output format...")
    
    try:
        result = predict(audio_path)
        print(f"✅ predict() succeeded")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, tuple):
            print(f"📊 Tuple length: {len(result)}")
            for i, item in enumerate(result):
                print(f"   Item {i}: type={type(item)}")
                if hasattr(item, 'shape'):
                    print(f"             shape={item.shape}")
                if hasattr(item, 'dtype'):
                    print(f"             dtype={item.dtype}")
                if isinstance(item, (list, tuple)) and len(item) < 20:
                    print(f"             content preview: {item}")
                elif isinstance(item, np.ndarray) and item.size < 20:
                    print(f"             content preview: {item}")
                elif hasattr(item, '__len__'):
                    try:
                        print(f"             length: {len(item)}")
                    except:
                        pass
        
        elif isinstance(result, dict):
            print(f"📊 Dictionary keys: {list(result.keys())}")
            for key, value in result.items():
                print(f"   {key}: type={type(value)}")
                if hasattr(value, 'shape'):
                    print(f"         shape={value.shape}")
        
        else:
            print(f"📊 Other type: {type(result)}")
            if hasattr(result, '__dict__'):
                print(f"   Attributes: {list(result.__dict__.keys())}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_basic_pitch_output("test_audio.wav")
