## TuttiBot v02 - Final Dependency Analysis & Solution

### Root Cause Identified ✅

The core conflict is:
- **Python 3.12**: Only supports TensorFlow >= 2.16.0
- **Basic Pitch 0.4.0**: Requires TensorFlow < 2.15.1
- **Result**: Impossible to satisfy both requirements simultaneously

### Tested Solutions ❌

1. **Python 3.13 + TensorFlow 2.20**: Basic Pitch incompatible
2. **Python 3.10 + TensorFlow 2.12**: Python 3.10 not available on system  
3. **Python 3.12 + TensorFlow 2.16+**: Basic Pitch incompatible

### Recommended Solution ✅

**Option 1: Use Python 3.11 (Best Compatibility)**
```bash
# Install Python 3.11 (if available)
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create environment
python3.11 -m venv tuttibot_stable_env
source tuttibot_stable_env/bin/activate

# Install compatible versions
pip install tensorflow==2.14.0
pip install basic-pitch==0.3.3
pip install "numpy>=1.24,<2.0"
# ... other dependencies
```

**Option 2: Use tflite-runtime Instead of Full TensorFlow**
```bash
# Use the current Python 3.12 environment
python3.12 -m venv tuttibot_lite_env
source tuttibot_lite_env/bin/activate

# Install Basic Pitch with tflite-runtime only
pip install basic-pitch[tflite]
pip install onnxruntime
pip install librosa music21 
# ... other non-tensorflow dependencies
```

**Option 3: Use Alternative AMT Library**
Replace Basic Pitch with a more modern alternative:
- **librosa + onset detection**: Built-in Python, more flexible
- **madmom**: Advanced audio analysis, better maintained
- **essentia**: Real-time audio analysis

### Immediate Action Plan

Given the system constraints (Python 3.12 only), I recommend:

1. **Install Python 3.11** (preferred)
   ```bash
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```

2. **OR use the alternative AMT approach** (fallback)
   - Skip Basic Pitch entirely
   - Use librosa for onset detection + pitch estimation
   - Implement a simple but working solution

### Working Requirements for Python 3.11

```txt
# Python 3.11 Compatible Stack
tensorflow==2.14.0
basic-pitch==0.3.3
numpy>=1.24.0,<2.0.0
librosa>=0.10.0
scipy>=1.10.0
onnxruntime>=1.15.0
music21>=9.0.0
matplotlib>=3.7.0
pandas>=2.0.0
```

### Alternative AMT Implementation

If Python 3.11 is not available, here's a working librosa-based solution:

```python
import librosa
import numpy as np

def simple_amt_transcription(audio_path):
    # Load audio
    y, sr = librosa.load(audio_path)
    
    # Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    
    # Pitch tracking
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, fmin=librosa.note_to_hz('C2'), 
        fmax=librosa.note_to_hz('C7')
    )
    
    # Convert to MIDI notes
    notes = []
    for i, onset_time in enumerate(onset_frames[:-1]):
        offset_time = onset_frames[i + 1]
        
        # Find average pitch in this segment
        start_frame = librosa.time_to_frames(onset_time, sr=sr)
        end_frame = librosa.time_to_frames(offset_time, sr=sr)
        
        segment_f0 = f0[start_frame:end_frame]
        valid_f0 = segment_f0[~np.isnan(segment_f0)]
        
        if len(valid_f0) > 0:
            avg_freq = np.median(valid_f0)
            midi_note = librosa.hz_to_midi(avg_freq)
            
            notes.append({
                'onset_time': onset_time,
                'offset_time': offset_time,
                'pitch_midi': int(np.round(midi_note)),
                'pitch_hz': avg_freq
            })
    
    return notes
```

### Next Steps

1. **Try installing Python 3.11**: `sudo apt install python3.11 python3.11-venv`
2. **If successful**: Use the Python 3.11 compatible requirements
3. **If not available**: Implement the librosa-based AMT fallback
4. **Test the complete pipeline**: Ensure GPU compatibility is maintained

### Updated Setup Instructions

I'll create an adaptive setup script that:
1. Checks for Python 3.11 availability
2. Falls back to Python 3.12 with alternative AMT
3. Provides clear error messages and next steps
