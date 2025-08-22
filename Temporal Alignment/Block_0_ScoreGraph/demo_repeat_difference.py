import xml.etree.ElementTree as ET

def demo_repeat_difference():
    """Demo showing difference between literal XML vs. musician performance"""
    
    # Sample MusicXML with repeats (simplified)
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise>
  <part id="P1">
    <measure number="1">
      <attributes><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <!-- A section -->
    </measure>
    <measure number="2">
      <!-- A section continues -->
    </measure>
    <measure number="3">
      <barline location="left"><repeat direction="forward"/></barline>
      <!-- B section starts, with repeat -->
    </measure>
    <measure number="4">
      <barline location="right"><repeat direction="backward"/></barline>
      <!-- B section ends, go back to measure 3 -->
    </measure>
    <measure number="5">
      <!-- C section -->
    </measure>
    <measure number="6">
      <direction><direction-type><words>D.C. al Fine</words></direction-type></direction>
      <!-- Go back to beginning, stop at Fine -->
    </measure>
  </part>
</score-partwise>"""
    
    print("🎼 **SHEET MUSIC NOTATION** (what composer wrote):")
    print("Measure 1-2: A section")
    print("Measure 3-4: |: B section :| (repeat bracket)")  
    print("Measure 5-6: C section, D.C. al Fine")
    print("📊 Total written measures: 6")
    print()
    
    print("🎵 **MUSICIAN PERFORMANCE** (how it's actually played):")
    print("1st time through: A → B → C → (see D.C., go back)")
    print("2nd time through: A → B → (stop at Fine)")
    print("Full performance: A-A-B-B-C-A-B")
    print("📊 Total performed measures: 10")
    print()
    
    print("⚠️ **YOUR CURRENT SIMPLE METHOD**:")
    print("- Reads literal XML: measures 1, 2, 3, 4, 5, 6")
    print("- Creates timeline: 6 measures → 24 beats")
    print("- ❌ IGNORES: Repeat brackets, D.C. al Fine")
    print("- Result: 60% of actual performance!")
    print()
    
    print("✅ **WITH REPEAT EXPANSION**:")
    print("- Processes repeats: expands |: :| and D.C. al Fine")
    print("- Creates timeline: A-B-C-A-B → 10 measures → 40 beats")
    print("- ✅ INCLUDES: All repetitions as musician plays")
    print("- Result: 100% of actual performance!")
    print()
    
    print("🎯 **WHY THIS MATTERS FOR TEMPORAL ALIGNMENT**:")
    print("Audio recording contains: A-B-C-A-B (full performance)")
    print("Your current score timeline: A-B-C (partial)")
    print("→ Alignment fails after first repeat!")
    print()
    print("With expanded timeline: A-B-C-A-B (matches audio)")
    print("→ Perfect alignment throughout entire piece!")

if __name__ == "__main__":
    demo_repeat_difference()
