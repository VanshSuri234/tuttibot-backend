#!/usr/bin/env python3
"""
Test script for Pitch Evaluation System

Quick tests to verify all components work correctly.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("Testing Imports...")
    print("=" * 60)
    
    try:
        from score_pitch_extractor import ScorePitchExtractor
        print("[OK] score_pitch_extractor imported")
    except Exception as e:
        print(f"[FAIL] score_pitch_extractor failed: {e}")
        return False
    
    try:
        from audio_pitch_extractor import AudioPitchExtractor
        print("[OK] audio_pitch_extractor imported")
    except Exception as e:
        print(f"[FAIL] audio_pitch_extractor failed: {e}")
        return False
    
    try:
        from pitch_comparator import PitchComparator
        print("[OK] pitch_comparator imported")
    except Exception as e:
        print(f"[FAIL] pitch_comparator failed: {e}")
        return False
    
    try:
        from pitch_grader import PitchGrader
        print("[OK] pitch_grader imported")
    except Exception as e:
        print(f"[FAIL] pitch_grader failed: {e}")
        return False
    
    try:
        from pitch_visualizer import PitchVisualizer
        print("[OK] pitch_visualizer imported")
    except Exception as e:
        print(f"[WARN] pitch_visualizer failed (matplotlib may not be installed): {e}")
    
    return True


def test_dependencies():
    """Test that required dependencies are installed"""
    print("\n" + "=" * 60)
    print("Testing Dependencies...")
    print("=" * 60)
    
    dependencies = {
        'music21': 'Music score parsing',
        'librosa': 'Audio pitch extraction',
        'numpy': 'Numerical operations',
        'scipy': 'Signal processing',
        'soundfile': 'Audio I/O',
        'matplotlib': 'Visualization (optional)',
        'seaborn': 'Visualization (optional)',
    }
    
    missing = []
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module:15s} - {description}")
        except ImportError:
            if module in ['matplotlib', 'seaborn']:
                print(f"⚠️  {module:15s} - {description} (optional, can continue)")
            else:
                print(f"❌ {module:15s} - {description} (REQUIRED)")
                missing.append(module)
    
    if missing:
        print(f"\n[FAIL] Missing required dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def test_score_extraction():
    """Test score pitch extraction with a simple example"""
    print("\n" + "=" * 60)
    print("Testing Score Extraction (synthetic test)...")
    print("=" * 60)
    
    try:
        from score_pitch_extractor import ScorePitchExtractor
        
        # Create extractor
        extractor = ScorePitchExtractor(reference_frequency=440.0)
        print("✅ ScorePitchExtractor created")
        
        # Test MIDI to Hz conversion
        freq = extractor.midi_to_hz(69)  # A4
        assert abs(freq - 440.0) < 0.1, f"MIDI conversion failed: {freq} != 440.0"
        print(f"✅ MIDI to Hz conversion works: MIDI 69 = {freq:.2f} Hz")
        
        # Test Hz to MIDI conversion
        midi = extractor.hz_to_midi(440.0)
        assert midi == 69, f"Hz conversion failed: {midi} != 69"
        print(f"✅ Hz to MIDI conversion works: 440 Hz = MIDI {midi}")
        
        return True
        
    except Exception as e:
        print(f"❌ Score extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_extraction():
    """Test audio pitch extraction configuration"""
    print("\n" + "=" * 60)
    print("Testing Audio Extraction (configuration test)...")
    print("=" * 60)
    
    try:
        from audio_pitch_extractor import AudioPitchExtractor
        
        # Test pYIN (CPU-friendly)
        extractor_pyin = AudioPitchExtractor(method='pyin')
        print(f"✅ pYIN extractor created (method: {extractor_pyin.method})")
        
        # Check if CREPE is available
        try:
            extractor_crepe = AudioPitchExtractor(method='crepe')
            print(f"✅ CREPE extractor available (method: {extractor_crepe.method})")
        except:
            print("⚠️  CREPE not available (optional, pYIN will be used)")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pitch_comparison():
    """Test pitch comparison logic"""
    print("\n" + "=" * 60)
    print("Testing Pitch Comparison (calculation test)...")
    print("=" * 60)
    
    try:
        from pitch_comparator import PitchComparator
        
        comparator = PitchComparator()
        
        # Test cents error calculation
        # Perfect unison
        cents = comparator.cents_error(440.0, 440.0)
        assert abs(cents) < 0.1, f"Unison failed: {cents} != 0"
        print(f"✅ Cents error (unison): {cents:.2f}¢")
        
        # Octave up (1200 cents)
        cents = comparator.cents_error(880.0, 440.0)
        assert abs(cents - 1200.0) < 1.0, f"Octave failed: {cents} != 1200"
        print(f"✅ Cents error (octave): {cents:.2f}¢")
        
        # Slightly sharp (10 cents)
        cents = comparator.cents_error(442.57, 440.0)
        assert 9.0 < cents < 11.0, f"10¢ sharp failed: {cents}"
        print(f"✅ Cents error (10¢ sharp): {cents:.2f}¢")
        
        # Slightly flat (-10 cents)
        cents = comparator.cents_error(437.52, 440.0)
        assert -11.0 < cents < -9.0, f"10¢ flat failed: {cents}"
        print(f"✅ Cents error (10¢ flat): {cents:.2f}¢")
        
        return True
        
    except Exception as e:
        print(f"❌ Pitch comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_grading():
    """Test grading logic"""
    print("\n" + "=" * 60)
    print("Testing Grading System...")
    print("=" * 60)
    
    try:
        from pitch_grader import PitchGrader
        
        grader = PitchGrader()
        
        # Test grade calculation
        test_cases = [
            (3.0, 'A+', 'Perfect'),
            (8.0, 'A', 'Excellent'),
            (15.0, 'A-', 'Very Good'),
            (22.0, 'B+', 'Good'),
            (35.0, 'C+', 'Fair'),
            (55.0, 'F', 'Failing')
        ]
        
        for mace, expected_grade, expected_desc in test_cases:
            grade, desc = grader.get_letter_grade(mace)
            score = grader.calculate_numeric_score(mace)
            
            assert grade == expected_grade, f"Grade mismatch: {grade} != {expected_grade}"
            assert desc == expected_desc, f"Description mismatch: {desc} != {expected_desc}"
            
            print(f"✅ MACE {mace:4.1f}¢ → Grade {grade:3s} ({score:5.1f}/100) - {desc}")
        
        return True
        
    except Exception as e:
        print(f"❌ Grading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 PITCH EVALUATION SYSTEM - TEST SUITE")
    print("=" * 70 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_imports()))
    results.append(("Dependency Test", test_dependencies()))
    results.append(("Score Extraction Test", test_score_extraction()))
    results.append(("Audio Extraction Test", test_audio_extraction()))
    results.append(("Pitch Comparison Test", test_pitch_comparison()))
    results.append(("Grading Test", test_grading()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} - {test_name}")
    
    print("=" * 70)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Prepare your score file (MusicXML or MIDI)")
        print("2. Prepare your audio file (WAV or MP3)")
        print("3. Run: python evaluate_pitch.py --score <file> --audio <file> --output results/")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("\nTo install missing dependencies:")
        print("  pip install -r requirements_pitch.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
