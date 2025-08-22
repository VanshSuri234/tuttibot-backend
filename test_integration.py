#!/usr/bin/env python3
"""
Test script for TuttiBot v02 main_v02_fixed.py integration
This script validates that all imports work correctly and the pipeline can be instantiated.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test temporal alignment block imports
        sys.path.append(str(current_dir / "Temporal Alignment" / "Block_0_ScoreGraph"))
        sys.path.append(str(current_dir / "Temporal Alignment" / "Block_1_AMT"))
        sys.path.append(str(current_dir / "Temporal Alignment" / "Block_2_SymbolicAlignment"))
        
        from build_scoregraph_with_repeats import build_scoregraph
        print("✅ Block 0 import successful")
        
        from transcribe_audio_enhanced import transcribe_audio_enhanced
        print("✅ Block 1 import successful")
        
        from align_symbolic_enhanced import EnhancedSymbolicAligner
        print("✅ Block 2 import successful")
        
        # Test main script import
        from main_v02_fixed import setup_logging, create_output_structure
        print("✅ Main script functions import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of imported modules"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test output directory creation
        from main_v02_fixed import create_output_structure
        test_output = create_output_structure("./test_output")
        print(f"✅ Output directory creation: {test_output}")
        
        # Test Enhanced Aligner instantiation
        from align_symbolic_enhanced import EnhancedSymbolicAligner
        aligner = EnhancedSymbolicAligner()
        print("✅ Enhanced Aligner instantiation successful")
        
        # Clean up test directory
        import shutil
        if os.path.exists("./test_output"):
            shutil.rmtree("./test_output")
            print("✅ Test cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def check_dependencies():
    """Check that all required dependencies are available"""
    print("\n🧪 Checking dependencies...")
    
    required_deps = [
        'numpy', 'scipy', 'pandas', 'librosa', 'soundfile',
        'music21', 'pretty_midi', 'mido', 'matplotlib', 'tqdm'
    ]
    
    missing_deps = []
    
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirement_v02.txt")
        return False
    
    print("\n✅ All dependencies available")
    return True

def main():
    print("🎼 TuttiBot v02 Integration Test")
    print("=" * 40)
    
    # Run tests
    imports_ok = test_imports()
    deps_ok = check_dependencies()
    func_ok = test_basic_functionality() if imports_ok else False
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"   Functionality: {'✅ PASS' if func_ok else '❌ FAIL'}")
    
    if all([imports_ok, deps_ok, func_ok]):
        print("\n🎉 All tests passed! TuttiBot v02 integration is ready.")
        print("\nUsage:")
        print("python main_v02_fixed.py --musicxml path/to/score.xml --audio path/to/audio.wav")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
