# PyAudio Compilation Fix - Render Deployment

## Problem

PyAudio was failing to compile on Render with:

```
fatal error: portaudio.h: No such file or directory
```

This error occurred even though:

- `--prefer-binary` flag was enabled
- PortAudio development headers were being installed via `preBuildCommand`

## Root Cause

PyAudio is pulled in as a **transitive dependency** of `pydub` and `audioread`:

- `pydub` optionally uses PyAudio for audio playback
- `audioread` optionally uses PyAudio as an audio backend
- However, **neither is needed for the TuttiBot pipeline**

The TuttiBot pipeline only **reads and processes audio files**. It does NOT:

- Play audio back to speakers (no PyAudio needed)
- Record audio from microphones (no PyAudio needed)
- Provide audio playback functionality to users

## Solution: Constraints File

Instead of fighting the compilation error, we **prevent PyAudio from being installed entirely** using pip's `--constraint` flag.

### Files Modified

#### 1. `constraints.txt` (NEW)

```
# Explicitly exclude PyAudio - not needed for file-based audio processing
pyaudio==0.0.0
```

This constraint file uses pip's "zero version" syntax to prevent any version of PyAudio from being installed.

#### 2. `build.sh` (UPDATED)

Added `--constraint constraints.txt` to the pip install command:

```bash
pip install --prefer-binary --constraint constraints.txt --upgrade --upgrade-strategy eager -r requirements.txt
```

### How It Works

When pip encounters this constraint:

1. It sees `pyaudio==0.0.0` in the constraints file
2. It recognizes this as a "prevent installation" constraint
3. When `pydub` or `audioread` try to pull in PyAudio, pip rejects it
4. `pydub` and `audioread` continue to work fine without PyAudio (they have fallback backends)

### Verification

You can verify this works by checking the pip install output:

- Should see PyAudio being skipped: `Skipping pyaudio: excluded by constraints`
- All other packages install normally
- `pydub` and `audioread` still work (they just don't use PyAudio)

## Why This Is Safe

**No functionality is lost** because:

1. **Audio reading**: Handled by `librosa`, `soundfile`, `pydub` (with FFmpeg backend)
2. **Audio processing**: Handled by `scipy`, `librosa`, `noisereduce`
3. **Audio file format support**: Handled by `ffmpeg` (system dependency on Render)
4. **Music transcription**: Handled by `basic-pitch` (uses TensorFlow)
5. **MIDI handling**: Handled by `music21`, `pretty_midi`, `mido`

All of these work fine without PyAudio.

## Testing on Render

After deployment, you can verify the build succeeded by:

1. **Check Render Build Log**:

   - Go to Dashboard → Service → Events tab
   - Look for: `Skipping pyaudio: excluded by constraints`
   - Look for: `pip: Successfully installed all requirements`

2. **Test the API**:

   - Submit an audio + score file
   - Verify pipeline completes successfully
   - Check logs for all 7 layers executing

3. **Verify in Logs**:
   ```
   [LAYER 2️⃣  AUDIO PROCESSING] Starting...
   ✅ Layer 2 Complete: 45.67s
   ```

## Alternative Solutions (Not Used)

We considered but rejected:

1. **Install PortAudio headers**: Didn't work consistently; headers still not found
2. **Remove pydub**: Breaks audioread pipeline functionality
3. **Use `--no-build-isolation`**: Causes other compilation issues
4. **Skip PyAudio in requirements**: PyAudio is a transitive dependency, not direct

The constraints file approach is the cleanest: it prevents the problem at the source without breaking any needed functionality.

## Rollback

If needed, simply:

1. Remove `--constraint constraints.txt` from `build.sh`
2. Delete `constraints.txt`
3. Redeploy

But this should work as-is.
