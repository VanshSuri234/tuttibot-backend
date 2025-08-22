# Analysis: Handling Audiveris PDF→XML Conversion Issues

## Current Implementation Limitations

### 1. **Repeated Notes/Measures** 
❌ **NOT HANDLED** - Current implementations don't process:
- `<repeat>` elements in MusicXML
- `<ending>` elements (1st/2nd time endings)
- Da Capo (D.C.) / Dal Segno (D.S.) markings
- Volta brackets

### 2. **Common Audiveris Issues NOT Addressed**:
- **Grace notes** misinterpreted as regular notes
- **Tied notes** across measures (split durations)
- **Tuplets** (triplets, quintuplets) with incorrect timing
- **Multi-voice parts** (overlapping notes in same measure)
- **Chord symbols** parsed as separate notes
- **Ornaments** (trills, mordents) creating extra notes
- **Beam grouping errors** affecting rhythm
- **Time signature changes** mid-score
- **Key signature changes** 
- **Clef changes** affecting note interpretation
- **Pickup measures** (anacrusis)
- **Irregular measure lengths**

## Solution: Enhanced Implementation

The current implementations are **basic timeline builders** that create a simple beat grid, but they don't handle the complex musical structures that Audiveris often generates from PDF scans.

Here's what we need to add:

### For Repeated Sections:
```python
# Handle repeat markings
if measure.find('.//repeat[@direction="forward"]') is not None:
    repeat_start = bar_num
if measure.find('.//repeat[@direction="backward"]') is not None:
    # Expand the repeated section
    expand_repeated_measures(repeat_start, bar_num)

# Handle endings (1st/2nd time)
ending = measure.find('.//ending')
if ending is not None:
    ending_type = ending.get('type')  # start, stop, discontinue
    ending_number = ending.get('number')  # 1, 2, etc.
```

### For Note-Level Issues:
```python
# Filter out grace notes (they don't affect beat timing)
notes = [n for n in measure.findall('.//note') 
         if n.find('grace') is None]

# Handle tied notes (combine durations)
for note in notes:
    tie = note.find('.//tie')
    if tie and tie.get('type') == 'start':
        # Find the tied note and combine durations
        pass

# Handle tuplets (adjust timing)
tuplet = note.find('.//tuplet')
if tuplet:
    actual_notes = int(tuplet.get('actual-notes', '3'))
    normal_notes = int(tuplet.get('normal-notes', '2'))
    duration *= (normal_notes / actual_notes)
```

## Recommended Enhanced Approach

Let me create an improved version that handles these issues...
