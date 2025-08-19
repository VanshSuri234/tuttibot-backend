
Temporal Alignment Roadmap — Block-by-Block (Python, CPU-only)

Date: 2025-08-18

Purpose
This document defines a complete, practical pipeline to compute temporal alignment between a live/recorded performance (audio WAV) and a written score (MusicXML/MIDI). It is organized into Blocks. For each block, you get: What/Why, Inputs, Outputs, and exact repositories (full links). You can hand this to an AI/coder and instruct them to implement the blocks one by one, verifying outputs before moving on.

Starting Inputs
• Performance (audio): perf.wav (mono/stereo, 44.1 kHz, noise-reduced, normalized) + segmentation.json (sections, cadences/fermatas/phrase ends if available).
• Score (notation): score.musicxml (from PDF→MusicXML) or score.mid + score_meta.json (note extraction, key/time signature, tuning Hz, etc.).

Goal
Produce a dense time map linking score beats → performance seconds, plus derived tempo and phase curves. This is the “complete temporal alignment”.

==================================================
Block 0 — Build the ScoreGraph (score timeline, score-only)
==================================================
What / Why
Parse MusicXML/MIDI and create a canonical, linearized score timeline with bars, beats, and node durations. This is the fixed target that audio (expressive timing) will be aligned to. Expanding repeats/voltas here avoids ambiguity later.

Inputs
• score.musicxml (or score.mid)
• score_meta.json (meter, key, tuning Hz, optional fermatas/cadences)
• (optional) segmentation.json (if it also includes structural cues)

Outputs (files)
• scoregraph.json with:
  - bars: list of bars with time signatures and downbeat absolute beat
  - nodes: list of nodes with fields: id, bar, beat, abs_beat, D_beats, flags
  - tempo_marks, key_signature, tuning_hz
  - maps: definitions for (bar,beat) ↔ abs_beat

Repos (use these links)
• Partitura (MusicXML/MIDI I/O & alignment utilities)
  https://github.com/CPJKU/partitura
• Docs / tutorials
  https://partitura.readthedocs.io/en/latest/Tutorial/notebook.html
  https://cpjku.github.io/partitura_tutorial/

Validation Task for Coder
Load MusicXML, expand repeats/voltas to a linear order, construct (bar,beat)↔abs_beat maps, compute D_beats, attach flags (fermatas/cadences) from XML or JSONs, and save scoregraph.json. Print the first 10 nodes to verify.

==================================================
Block 1 — AMT: Audio → Symbolic (MIDI) for the performance
==================================================
What / Why
Convert the performance audio into symbolic note events (onset/offset in seconds, MIDI pitches, velocities) so you can do symbolic↔symbolic alignment. Choose a transcriber based on your instrument; all below run locally on CPU.

Options (pick one; can compare two)
• Basic Pitch (general instruments; easy):
  https://github.com/spotify/basic-pitch
  Demo: https://basicpitch.spotify.com/
• Onsets & Frames (piano-focused):
  https://github.com/magenta/magenta/blob/master/magenta/models/onsets_frames_transcription/README.md
• Omnizart (multi-instrument toolbox):
  https://github.com/Music-and-Culture-Technology-Lab/omnizart
  Docs: https://music-and-culture-technology-lab.github.io/omnizart-doc/

Inputs
• perf.wav (44.1 kHz, mono/stereo)

Outputs (files)
• perf.mid (transcribed MIDI)
• perf_notes.json (optional: array of {"pitch","onset_sec","offset_sec","velocity"})

Validation Task
Run AMT on perf.wav, create perf.mid; list the first 20 events sorted by onset; check that tuning roughly matches score_meta.json["tuning_hz"] (±10 cents).

==================================================
Block 2 — Symbolic ↔ Symbolic Alignment (score vs. transcribed performance)
==================================================
What / Why
Align score (MusicXML/MIDI) to performance (MIDI from AMT) at the note level to get precise correspondences, then convert to a dense time map: (score_abs_beat → perf_time_sec). This alignment serves as your ground truth for temporal alignment.

Repos (use these links)
• Parangonar (symbolic alignment; offline/online; uses Partitura I/O)
  https://github.com/sildater/parangonar
• Parangonada (alignment checking / datasets; optional)
  https://github.com/sildater/parangonada
• Partitura (to read/write MATCH files and note arrays)
  https://github.com/CPJKU/partitura

Inputs
• score.musicxml (or score.mid)
• scoregraph.json (from Block 0)
• perf.mid (from Block 1)

Outputs (files)
• alignment.match (standard Match format: note↔note links)
• time_map.json — dense list of pairs:
  {"method":"Parangonar.DualDTWNoteMatcher","path":[[score_abs_beat,perf_time_sec],...],"hop_sec":0.01}

Validation Task
1) Run Parangonar’s offline matcher (e.g., DualDTWNoteMatcher) → produce alignment.match.
2) Convert MATCH to time_map.json using scoregraph.json’s (bar,beat)↔abs_beat map and performance note times.
3) Plot 30 random matched notes to confirm they land near the right bars/beats.

==================================================
Block 3 — Derive tempo & phase from the time map (for grading / tolerance)
==================================================
What / Why
Compute tempo curve (BPM over performance time) and in-node phase φ (0..1 within each node/beat) using D_beats from the ScoreGraph. These signals drive rubato-tolerant tracking rules and give analytics (ahead/behind timing).

Repos
• Partitura (metric utilities / note arrays)
  https://github.com/CPJKU/partitura
  Docs: https://partitura.readthedocs.io/en/latest/Tutorial/notebook.html

Inputs
• time_map.json (from Block 2)
• scoregraph.json (from Block 0)

Outputs (files)
• tempo_curve.csv (columns: abs_beat,bpm)
• phase_curve.csv (columns: abs_beat,phi)
• (optional) diagnostics.png (tempo vs. abs_beat plot)

Validation Task
Recompute the tempo curve two ways (finite differences on the time map vs. note IOIs from MATCH); the curves should agree within a few BPM except at boundaries.

==================================================
Block 4 (optional) — Beat & Downbeat from audio
==================================================
What / Why
Extract beat and downbeat times from the performance audio for diagnostics, visualizations, and to gate re-locks on strong downbeats.

Options
• BeatNet — CRNN + particle filter/DBN; one call gives beat & downbeat times; offline or streaming; CPU-friendly.
  https://github.com/mjhydri/BeatNet
• madmom — RNN → DBN tracker with classic ~100 fps activations and tracked beat/downbeat times.
  https://github.com/CPJKU/madmom

Inputs
• perf.wav (44.1 kHz)

Outputs (files)
• beats.json: [{"t":12.345,"downbeat":1}, {"t":13.625,"downbeat":0}, ...]
• (optional) activations.h5 (madmom’s ~100 fps probs)

Validation Task
Overlay beats.json on the time_map and check that downbeats align near bar downbeats from scoregraph.json. Report average deviation in ms and in beats.

==================================================
Block 5 (optional) — Online (real-time) follower prototype, CPU-only
==================================================
What / Why
If/when you need streaming position estimates, use Matchmaker to run online time warping (OTW) for audio or an HMM follower for MIDI. It returns current score position in beats per frame; can simulate real-time from a file. No GPU, no external API.

Repos
• Matchmaker (Python library for real-time music alignment)
  https://github.com/pymatchmaker/matchmaker
• Docs
  https://pymatchmaker.readthedocs.io/

Inputs
• score.musicxml (or score.mid)
• perf.wav (simulated streaming) or an actual audio/MIDI stream

Outputs (files)
• online_trace.csv: time_sec,score_abs_beat,bar,beat,conf

Validation Task
Run in “simulated live” mode on perf.wav and compare the online path to time_map.json. Compute mean absolute error in beats; add a simple re-lock rule when error > threshold.

==================================================
Block 6 (optional) — Rubato tolerance + auto re-lock logic
==================================================
What / Why
Use segmentation.json (cadences/fermatas/phrase ends) to define a per-beat tolerance mask R(b)∈[0,1]. Where R is high, gently widen timing variance (e.g., allow lower OTW slope or higher tempo process noise). When confidence drops, perform a local, coarse DTW on the last few seconds to re-seed the follower. For the coarse DTW, reuse SyncToolbox at low resolution.

Repos
• SyncToolbox (efficient DTW; good for quick relocks)
  https://github.com/meinardmueller/synctoolbox
• DTW API
  https://meinardmueller.github.io/synctoolbox/build/html/dtw.html

Inputs
• segmentation.json, beats.json (optional), online_trace.csv (if streaming)

Outputs
• online_trace_stabilized.csv (with fewer large jumps; “re-locks” near downbeats)

Validation Task
Inject synthetic pauses/jumps in a test run; verify re-lock occurs within ≤2 bars, preferably on a downbeat.

==================================================
Data Flow Summary
==================================================
score.musicxml/.mid + score_meta.json
    └─▶ Block 0: ScoreGraph  ──▶ scoregraph.json

perf.wav ──▶ Block 1: AMT ──▶ perf.mid

(scoregraph.json, score.musicxml/.mid) + perf.mid
    └─▶ Block 2: Symbolic Alignment (Parangonar)
          └─▶ alignment.match + time_map.json
                  └─▶ Block 3: tempo_curve.csv, phase_curve.csv

perf.wav ──▶ (optional) Block 4: BeatNet/madmom ──▶ beats.json

(score, perf.wav or stream)
    └─▶ (optional) Block 5: Matchmaker (online)
          └─▶ online_trace.csv
(online_trace.csv + beats.json + segmentation.json)
    └─▶ (optional) Block 6: Rubato tolerance + relock
          └─▶ online_trace_stabilized.csv

==================================================
File formats & shapes
==================================================
• scoregraph.json
  - bars[i].time_sig: "n/d", bars[i].downbeat_abs_beat: float
  - nodes[k]: {id, bar:int, beat:float, abs_beat:float, D_beats:float, flags:[...] }
  - mapping helpers documented in comments

• perf.mid
  Standard MIDI; optionally export perf_notes.json (flat list):
  {"notes":[{"pitch":64,"onset_sec":12.345,"offset_sec":12.825,"velocity":72}, ...]}

• alignment.match
  Standard MATCH format (Partitura can read/write). Contains note-to-note links + timings.

• time_map.json
  Dense pairs at a uniform hop:
  {"method":"Parangonar.DualDTWNoteMatcher","hop_sec":0.01,"path":[[0.00,0.12],[0.01,0.125], ...]}

• tempo_curve.csv
  abs_beat,bpm

• phase_curve.csv
  abs_beat,phi where phi = (position inside node/beat)/D_beats

• beats.json
  [{"t":12.345,"downbeat":1}, ...]

• online_trace.csv
  time_sec,score_abs_beat,bar,beat,conf

==================================================
Why these choices
==================================================
• Symbolic alignment (after AMT) gives note-accurate correspondences and is robust to rubato and small errors; Parangonar is purpose-built and integrates with Partitura.
• Matchmaker is a modern, CPU-friendly real-time follower that outputs current beat position; it uses Partitura to define beats internally, matching the ScoreGraph concept.
• BeatNet/madmom are optional for audio-side beats; they help with re-locks and QA but are not required to produce the offline time map.
• SyncToolbox gives a fast, reliable DTW implementation for audio↔score fallback or quick re-lock checks.

==================================================
Checklist to give to a coder/AI
==================================================
1) Implement Block 0 (build_scoregraph.py): Partitura → scoregraph.json (+ print 10 nodes).
2) Implement Block 1 (transcribe_audio.py): AMT → perf.mid (+ list 20 events).
3) Implement Block 2 (align_symbolic.py): Parangonar → alignment.match + time_map.json (+ plot 30 matches).
4) Implement Block 3 (derive_curves.py): → tempo_curve.csv + phase_curve.csv (+ diagnostics).
5) (Optional) Block 4 (estimate_beats.py): BeatNet/madmom → beats.json (+ overlay vs time_map).
6) (Optional) Block 5 (follow_online_sim.py): Matchmaker → online_trace.csv (+ compare to time_map). 
7) (Optional) Block 6 (tolerance_and_relock.py): SyncToolbox-driven relocks → online_trace_stabilized.csv.
