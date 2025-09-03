#!/usr/bin/env python3
"""
TuttiBot v02 - Quick Installation Test
Verifies that all required packages are installed and working
"""

import sys
import importlib

def test_import(package_name, display_name=None):
    """Test if a package can be imported"""
    if display_name is None:
        display_name = package_name
    
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"✅ {display_name}: {version}")
        return True
    except ImportError as e:
        print(f"❌ {display_name}: Failed - {e}")
        return False

def main():
    print("🔍 TuttiBot v02 - Installation Verification")
    print("=" * 50)
    print(f"Python: {sys.version}")
    print("=" * 50)
    
    # Core packages
    print("\n📊 Core Packages:")
    test_import('numpy', 'NumPy')
    test_import('scipy', 'SciPy') 
    test_import('pandas', 'Pandas')
    test_import('matplotlib', 'Matplotlib')
    
    # Audio processing
    print("\n🎵 Audio Processing:")
    test_import('librosa', 'Librosa')
    test_import('soundfile', 'SoundFile')
    test_import('audioread', 'AudioRead')
    
    # Music processing  
    print("\n🎼 Music Processing:")
    test_import('music21', 'Music21')
    test_import('pretty_midi', 'Pretty MIDI')
    test_import('mido', 'Mido')
    
    # ML frameworks
    print("\n🤖 ML Frameworks:")
    tf_ok = test_import('tensorflow', 'TensorFlow')
    torch_ok = test_import('torch', 'PyTorch')
    
    # GPU status
    if tf_ok:
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            print(f"   TensorFlow GPUs: {len(gpus)}")
        except:
            print("   TensorFlow GPU check failed")
    
    if torch_ok:
        try:
            import torch
            print(f"   PyTorch CUDA: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"   CUDA devices: {torch.cuda.device_count()}")
        except:
            print("   PyTorch CUDA check failed")
    
    # PDF processing
    print("\n📄 PDF Processing:")
    test_import('pdf2image', 'PDF2Image')
    test_import('oemer', 'Oemer')
    
    # System tools
    print("\n🖥️ System Tools:")
    test_import('psutil', 'PSUtil')
    
    # TuttiBot modules
    print("\n🤖 TuttiBot Modules:")
    sys.path.append('.')
    
    try:
        from gpu_manager import GPUManager
        print("✅ GPU Manager: Available")
    except Exception as e:
        print(f"❌ GPU Manager: {e}")
    
    # Test pipeline blocks
    sys.path.append('Temporal Alignment/Block_0_ScoreGraph')
    sys.path.append('Temporal Alignment/Block_1_AMT')
    sys.path.append('Temporal Alignment/Block_2_SymbolicAlignment')
    
    try:
        from build_scoregraph_with_repeats import build_scoregraph
        print("✅ Block 0 (ScoreGraph): Available")
    except Exception as e:
        print(f"❌ Block 0 (ScoreGraph): {e}")
    
    try:
        from transcribe_audio_fixed import transcribe_audio_basic_pitch
        print("✅ Block 1 (AMT): Available")
    except Exception as e:
        print(f"❌ Block 1 (AMT): {e}")
    
    try:
        from align_symbolic_enhanced import EnhancedSymbolicAligner
        print("✅ Block 2 (Alignment): Available")
    except Exception as e:
        print(f"❌ Block 2 (Alignment): {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Installation verification complete!")
    print("\nReady to run:")
    print("python main_v02_fixed.py --musicxml test.musicxml --audio twinkle_full.wav")

if __name__ == "__main__":
    main()
