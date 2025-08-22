# 🔄 **When and How Repeat Expansion Works**

## 📋 **The Complete Pipeline**

### **Stage 1: PDF → MusicXML** (Audiveris/OMR)
```
PDF scan → Audiveris → MusicXML file
```
**What happens**: Audiveris reads the visual notation and creates MusicXML
**Repeat handling**: Audiveris PRESERVES the repeat markings in XML:
```xml
<barline><repeat direction="forward"/></barline>
<barline><repeat direction="backward"/></barline>
<ending number="1" type="start"/>
<direction><direction-type><words>D.C. al Fine</words></direction-type></direction>
```
**Result**: MusicXML contains the "composer's shorthand" with repeat symbols

### **Stage 2: MusicXML → ScoreGraph** (Your current stage)
```
MusicXML → Your parser → ScoreGraph JSON
```
**This is WHERE repeat expansion happens!**

## 🎯 **Two Different Approaches**

### **❌ Current Approach** (your simple method):
```python
# Stage 2a: Raw XML parsing (what you're doing now)
tree = ET.parse(score_path)  # Reads literal XML
measures = part.findall('measure')  # Gets written measures only
# Result: Only the "sheet music notation" (compressed)
```

**What this gives you**:
- Measure 1-4: Verse
- Measure 5-8: |: Chorus :| (with repeat symbols)
- Measure 9-12: Bridge
- Total: 12 measures

### **✅ Enhanced Approach** (with repeat expansion):
```python
# Stage 2b: Smart musical parsing (what you should do)
score = pt.load_musicxml(score_path)  # Parses musical structure
expanded_part = pt.score.unfold_part_maximal(part)  # EXPANDS repeats
# Result: Full "performance timeline" (expanded)
```

**What this gives you**:
- Measure 1-4: Verse  
- Measure 5-8: Chorus (1st time)
- Measure 9-12: Bridge
- Measure 13-16: Chorus (2nd time) ← ADDED by expansion
- Total: 16 measures

## 🔧 **How Repeat Expansion Actually Works**

### **Step-by-Step Process**:

1. **Parse MusicXML structure** (both methods do this)
2. **Identify repeat markings** (only smart parsers do this):
   ```xml
   <repeat direction="forward"/>  → Start repeat here
   <repeat direction="backward"/> → Go back to start repeat
   <ending number="1"/>           → 1st time only
   <ending number="2"/>           → 2nd time only
   <words>D.C. al Fine</words>    → Go back to beginning, stop at Fine
   ```

3. **Build performance timeline** (the magic happens here):
   ```python
   # Partitura unfold_part_maximal() does:
   for repeat_section in find_repeats(part):
       for repetition in range(repeat_section.times):
           add_measures_to_timeline(repeat_section.measures)
   
   # For Da Capo/Dal Segno:
   if find_da_capo(part):
       jump_back_to_beginning()
       replay_until_fine_or_end()
   ```

4. **Generate expanded measure sequence**:
   ```
   Original XML:    [A] |: [B] :| [C] D.C. al Fine
   Expanded result: [A] [B] [C] [A] [B]
   ```

## 📊 **Comparison of Methods**

| Method | Stage | What It Does | Result |
|--------|-------|--------------|--------|
| **Audiveris** | PDF→XML | Preserves repeat symbols | XML with `<repeat>` tags |
| **Your Simple** | XML→Graph | Ignores repeat symbols | Compressed timeline |
| **Partitura Unfold** | XML→Graph | Expands repeat symbols | Full performance timeline |
| **Music21 expandRepeats** | XML→Graph | Expands repeat symbols | Full performance timeline |

## 🎵 **Real Example**

### **Original MusicXML** (from Audiveris):
```xml
<measure number="1"><!-- Verse --></measure>
<measure number="2"><!-- Verse --></measure>
<measure number="3">
  <barline><repeat direction="forward"/></barline>
  <!-- Chorus -->
</measure>
<measure number="4">
  <barline><repeat direction="backward"/></barline>
  <!-- Chorus -->
</measure>
<measure number="5"><!-- Bridge --></measure>
```

### **Your Current Simple Method** reads:
```
Measures: 1, 2, 3, 4, 5
Timeline: Verse → Chorus → Bridge (5 measures)
```

### **With Repeat Expansion** processes:
```
1. Read measures 1, 2, 3, 4, 5
2. Find repeat: measures 3-4 marked for repeat
3. Expand: 1, 2, 3, 4, 3, 4, 5
4. Renumber: 1, 2, 3, 4, 5, 6, 7
Timeline: Verse → Chorus → Chorus → Bridge (7 measures)
```

## ⚡ **Key Point**

**Repeat expansion happens DURING ScoreGraph creation**, not before:

- ❌ **NOT during PDF→XML**: Audiveris preserves repeats as symbols
- ✅ **DURING XML→ScoreGraph**: Smart parsers expand the symbols
- ❌ **NOT after ScoreGraph**: Too late, structure is already set

This is why you need to change your **Stage 2** (XML→ScoreGraph) to use the libraries' repeat expansion features!

## 🚀 **Implementation**

In your current file, the magic line is:
```python
# Instead of raw XML parsing:
expanded_part = pt.score.unfold_part_maximal(part)  # ← THIS LINE
# Or:
expanded_score = score.expandRepeats()  # ← OR THIS LINE
```

These functions do all the musical intelligence to convert "composer shorthand" into "performer timeline"!
