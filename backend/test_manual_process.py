
import sys
import os
import json
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(r"c:\Users\nsp19\Downloads\Auto Post\backend")
sys.path.append(str(backend_path))

try:
    from services.video_processing import video_processor
    from services.transcription import transcriber
    from services.analysis import analyzer

    # Input File (from your uploads listing)
    # Switched to the smaller 'viral short' file for speed testing
    input_filename = "6fd54193-ae28-408a-9597-26656bf52bae.mp4"
    input_path = backend_path / "uploads" / input_filename
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        exit(1)

    print(f"1. Processing File: {input_filename}")
    
    # 1. Extract Audio
    print("   Extracting audio...")
    audio_path = video_processor.extract_audio(str(input_path))
    print(f"   Audio: {audio_path}")

    # 2. Transcribe
    print("   Transcribing (Language: te)...")
    transcript = transcriber.transcribe_audio(audio_path, language="te")
    text = transcript.get("text", "")
    segments = transcript.get("segments", [])
    print(f"   Transcription done. Length: {len(text)} chars. Segments: {len(segments)}")

    # 3. Analyze
    print("   Analyzing with Gemini...")
    moments = analyzer.analyze_transcript(text, segments, duration=60)
    
    # Backfill Logic (same as in process.py)
    num_shorts = 3
    if len(moments) < num_shorts:
        print(f"   AI returned {len(moments)} clips. Backfilling to {num_shorts}...")
        heuristic_moments = analyzer.detect_high_energy_moments(str(input_path), num_clips=num_shorts*2, clip_duration=60)
        
        def is_overlapping(new_m, existing_ms, threshold=10):
            for ex in existing_ms:
                if abs(new_m["start"] - ex["start"]) < threshold: return True
            return False

        added = 0
        for hm in heuristic_moments:
            if added >= (num_shorts - len(moments)): break
            if not is_overlapping(hm, moments):
                hm["reason"] = "Heuristic Backfill"
                moments.append(hm)
                added += 1
        moments.sort(key=lambda x: x["start"])

    print(f"   Total Clips to Generate: {len(moments)}")

    # 4. Cut
    for i, moment in enumerate(moments):
        print(f"   Cutting Clip {i+1}...")
        output_path = video_processor.output_dir / f"MANUAL_TEST_{i+1}.mp4"
        srt_path = video_processor.output_dir / f"MANUAL_TEST_{i+1}.srt"
        
        subtitle_arg = None
        if segments:
            video_processor.generate_word_level_srt(segments, str(srt_path), start_offset=moment["start"])
            subtitle_arg = str(srt_path)
            
        final_path = video_processor.cut_video(
            video_path=str(input_path),
            start_time=moment["start"],
            end_time=moment["end"],
            output_path=str(output_path),
            subtitle_path=subtitle_arg,
            style_name="Classic" # Testing Classic/Telugu font
        )
        print(f"   Clip {i+1} saved: {final_path}")

    print("MANUAL PROCESSING COMPLETE.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    # Also print stack trace
    import traceback
    traceback.print_exc()
