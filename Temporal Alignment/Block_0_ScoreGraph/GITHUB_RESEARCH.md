# GitHub Research: Repeat Handling Solutions

## ✅ **Key Findings**

### 1. **Partitura Library** (CPJKU/partitura)
**EXCELLENT repeat support** - has robust unfold functionality:

```python
import partitura as pt

# Load and expand repeats automatically
score = pt.load_musicxml("audiveris_file.musicxml")
part = score.parts[0]

# Key functions found:
expanded_part = pt.score.unfold_part_maximal(part)  # ✅ HANDLES ALL REPEATS!
```

**Features discovered:**
- ✅ **`unfold_part_maximal()`** - Expands ALL repeat structures
- ✅ **Handles volta brackets** (1st/2nd endings)
- ✅ **Da Capo/Dal Segno** support
- ✅ **Nested repeats** supported
- ✅ **Grace note filtering** - `ignore_invisible_objects=True`
- ✅ **Tied note handling** in import
- ✅ **Tuplet support** with correct timing

### 2. **Music21 Library** (cuthbertLab/music21)
**EXCELLENT repeat support** - comprehensive expander:

```python
from music21 import converter

# Load and expand repeats
score = converter.parse("audiveris_file.musicxml")
expanded = score.expandRepeats()  # ✅ BUILT-IN REPEAT EXPANSION!

# Or use Expander directly:
from music21 import repeat
expander = repeat.Expander(score.parts[0])
expanded_part = expander.process()
```

**Features discovered:**
- ✅ **`expandRepeats()`** method on all streams
- ✅ **`repeat.Expander`** class for advanced control
- ✅ **Volta brackets** (RepeatBracket spanners)
- ✅ **Da Capo/Dal Segno/Fine/Coda** support
- ✅ **Nested repeat validation**
- ✅ **Grace note handling** in parser
- ✅ **Tuplet expansion** support

## 🚀 **Enhanced Implementation**

Your current methods are **missing the key function calls**! Here's what you should do:

### Option 1: Use Partitura with Unfold (RECOMMENDED)
```python
def build_scoregraph_partitura_unfold(score_path, meta_path, seg_path=None):
    """Enhanced partitura version with repeat expansion"""
    import partitura as pt
    
    # Load with repeat expansion!
    score = pt.load_musicxml(score_path)
    part = score.parts[0]
    
    # ✅ EXPAND ALL REPEATS
    expanded_part = pt.score.unfold_part_maximal(part)
    
    # Now build scoregraph from expanded part
    # ... rest of implementation
```

### Option 2: Use Music21 with expandRepeats() 
```python
def build_scoregraph_music21_expanded(score_path, meta_path, seg_path=None):
    """Enhanced music21 version with repeat expansion"""
    from music21 import converter
    
    # Load and expand repeats in one step!
    score = converter.parse(score_path)
    expanded_score = score.expandRepeats()  # ✅ MAGIC HAPPENS HERE
    
    # Now build scoregraph from expanded score
    # ... rest of implementation
```

## 📊 **Critical Issue with Your Current Code**

Your current implementations are **parsing the raw MusicXML** without expanding repeats. This means:

❌ **Simple method**: Only sees literal measures (missing repeated sections)
❌ **Music21 method**: Has `expandRepeats()` but you're NOT calling it!
❌ **Pretty-MIDI method**: MIDI doesn't contain repeat information

## 🔧 **Fix for Your Code**

The fix is simple - just add ONE LINE to your music21 method:

```python
# BEFORE (your current code):
score = converter.parse(score_path)
measures = part.getElementsByClass(stream.Measure)  # ❌ Raw measures

# AFTER (corrected):
score = converter.parse(score_path)
expanded_score = score.expandRepeats()  # ✅ ADD THIS LINE!
measures = expanded_score.parts[0].getElementsByClass(stream.Measure)
```

## 📋 **Repository Evidence**

### From Partitura Tests:
- `test_unfold_volta()` - Tests 1st/2nd endings
- `test_unfold_dacapo()` - Tests Da Capo expansion  
- `test_unfold_complex()` - Tests nested repeats
- `unfold_part_maximal()` function available

### From Music21 Tests:
- `expandRepeats()` method tested extensively
- `repeat.Expander` class with `process()` method
- Handles volta brackets, da capo, dal segno, fine, coda
- Test files show complex repeat scenarios working

## ⚡ **Quick Fix Implementation**

Let me create the corrected version of your code that actually uses the repeat expansion...
