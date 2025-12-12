from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from services.downloader import downloader
from services.video_processing import video_processor, STYLE_MAP
from services.transcription import transcriber
from services.analysis import analyzer
import os
import json
import re


router = APIRouter()

class ProcessRequest(BaseModel):
    file_id: str = None # Optional if video_url is provided
    video_path: str = None # Optional if video_url is provided
    video_url: str = None 
    num_shorts: int = 4
    caption_style: str = "Classic"
    clip_duration: int = 60
    language: str = "en"
    processing_start_time: float = None
    processing_end_time: float = None
    custom_color: str = None # Expected format: #RRGGBB
    custom_bg_color: str = None # Expected format: #RRGGBB
    custom_size: int = None

@router.post("/")
async def process_video(request: ProcessRequest):
    """
    Trigger full video processing pipeline:
    1. Download (if URL) or Use Local File.
    2. Extract Audio.
    3. Transcribe Audio (Whisper or Local).
    4. Analyze for best moments (Heuristic or LLM).
    5. Cut/Crop the best clips with Captions.
    """
    
    # Handle URL Input
    if request.video_url:
        try:
            print(f"Downloading from URL: {request.video_url}")
            request.video_path = downloader.download_video(request.video_url)
            request.file_id = Path(request.video_path).stem
        except Exception as e:
             raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

    if not request.video_path or not Path(request.video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # DEBUG LOGGING CONSTANT
    DEBUG_LOG_FILE = "debug_process_log.txt"
    def log_debug(msg):
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")

    log_debug(f"--- START PROCESSING {request.file_id} ---")

    # 0. Pre-process: Trim source video if needed
    if request.processing_start_time is not None or request.processing_end_time is not None:
        try:
            log_debug(f"Trimming source video: {request.video_path} ({request.processing_start_time}-{request.processing_end_time})")
            trimmed_path = video_processor.output_dir / f"{request.file_id}_trimmed.mp4"
            
            # Default to 0 start if only end provided is rare, but handle it
            start = request.processing_start_time if request.processing_start_time else 0.0
            
            # If no end time, just start until end
            # ffmpeg -ss start -i input ...
            
            # Use cut_video reusing logic without cropping?
            # Or dedicated trim method. Let's make a simple trim call.
            # Using cut_video might force 9:16 crop which we might NOT want yet?
            # Actually, extract_audio and transcribe usually happen on the FULL video.
            # If we trim now, we should perform audio extract on the TRIMMED video.
            
            # We need a new simple trim function or modify cut_video to optional crop.
            # For now, let's call a new method `trim_video_source` in video_processor.
            # But since I can't edit multiple files in one turn easily if I didn't plan it...
            # I'll add `trim_video_source` to video_processor next.
            
            # Assuming it exists or I will add it.
            request.video_path = video_processor.trim_source_video(
                request.video_path, 
                trimmed_path, 
                start, 
                request.processing_end_time
            )
            log_debug(f"Trimmed video saved to: {request.video_path}")
            
        except Exception as e:
            log_debug(f"Trimming failed: {e}")
            print(f"Trimming failed: {e}")
            # Do NOT fail, just proceed with full video? OR fail?
            # Better to fail if user explicitly asked for trim.
            raise HTTPException(status_code=500, detail=f"Failed to trim video: {str(e)}")


    # 1. Extract Audio
    try:
        audio_path = video_processor.extract_audio(request.video_path)
        log_debug(f"Audio extracted: {audio_path}")
    except Exception as e:
        log_debug(f"Audio extraction failed: {e}")
        print(f"Audio extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Audio extraction failed")


    # 2. Transcribe
    transcript = None
    try:
        print(f"Starting transcription... (Language: {request.language})")
        log_debug(f"Starting transcription for {audio_path} (Language: {request.language})")
        transcript = transcriber.transcribe_audio(audio_path, language=request.language)
        
        if transcript:
             log_debug(f"Transcription result: {len(transcript.get('text', ''))} chars")
             if not transcript.get("text", "").strip():
                 log_debug("Transcription returned empty text.")
                 raise Exception("Transcription returned empty text.")
             log_debug(f"Segments count: {len(transcript.get('segments', []))}")
        else:
             log_debug("Transcription returned None.")
             raise Exception("Transcription returned None.")

    except Exception as e:
        log_debug(f"Transcription failed entirely: {e}")
        print(f"Transcription failed entirely: {e}")
        # Log to file to debug
        with open("error_log.txt", "a") as f:
            f.write(f"Transcription Error (Lang: {request.language}): {str(e)}\n")
        # Proceed with transcript = None

    # 3. Analyze
    moments = []
    segments = []
    
    # Use LLM analysis if transcript is available
    if transcript:
        # Normalize transcript object
        if isinstance(transcript, dict):
            text = transcript.get("text", "")
            segments = transcript.get("segments", [])
        else:
            # Assume it's an OpenAI object
            text = getattr(transcript, "text", "")
            segments = getattr(transcript, "segments", [])

        print(f"Transcript length: {len(text)}. Analysis...")
        log_debug(f"Analyzing {len(text)} chars with LLM...")
        moments = analyzer.analyze_transcript(text, segments, duration=request.clip_duration)
        log_debug(f"LLM returned {len(moments)} moments.")
    
    # Save transcript for regeneration
    if transcript:
        try:
             transcript_path = video_processor.output_dir / f"{request.file_id}_transcript.json"
             with open(transcript_path, "w", encoding="utf-8") as f:
                 json.dump(segments, f, ensure_ascii=False)
             log_debug(f"Transcript saved to {transcript_path}")
        except Exception as e:
             log_debug(f"Failed to save transcript: {e}")
             print(f"Failed to save transcript: {e}")

    
    # Fallback if AI fails (empty list) -> use heuristic
    if not moments:
        log_debug("Using heuristic fallback.")
        print("AI analysis failed or returned no clips. Using heuristic fallback.")
        # Pass user preferences to fallback logic
        moments = analyzer.detect_high_energy_moments(
            request.video_path, 
            num_clips=request.num_shorts, 
            clip_duration=request.clip_duration
        )

    # Apply limit or backfill based on user request
    if len(moments) > request.num_shorts:
        moments = moments[:request.num_shorts]
    elif len(moments) < request.num_shorts:
        print(f"AI returned {len(moments)} clips, but user requested {request.num_shorts}. Backfilling...")
        log_debug(f"Backfilling from {len(moments)} to {request.num_shorts}")
        
        needed = request.num_shorts - len(moments)
        
        # Get purely heuristic moments
        heuristic_moments = analyzer.detect_high_energy_moments(
            request.video_path, 
            num_clips=request.num_shorts * 2, # Ask for more to find non-overlapping
            clip_duration=request.clip_duration
        )
        
        # Filter out overlaps
        def is_overlapping(new_m, existing_ms, threshold=10):
            for ex in existing_ms:
                # Check if start time is within 'threshold' seconds of existing
                if abs(new_m["start"] - ex["start"]) < threshold:
                    return True
            return False
            
        added_count = 0
        for hm in heuristic_moments:
            if added_count >= needed:
                break
            
            if not is_overlapping(hm, moments):
                hm["reason"] = "Heuristic Backfill"
                moments.append(hm)
                added_count += 1
                
        # Sort by start time to keep logical order (optional, but nice)
        moments.sort(key=lambda x: x["start"])

    generated_clips = []
    
    # 4. Cut Clips
    for i, moment in enumerate(moments):
        output_path = video_processor.output_dir / f"{request.file_id}_short_{i+1}.mp4"
        srt_path = video_processor.output_dir / f"{request.file_id}_short_{i+1}.srt"
        
        log_debug(f"Processing Clip {i}: {moment['start']}-{moment['end']}")
        
        try:
            # Generate SRT if we have segments (Even if we used Heuristic analysis!)
            # Crucial Fix: Use segments for captions even if 'moments' came from 'detect_high_energy_moments'
            subtitle_arg = None
            if segments:
                try:
                    log_debug(f"Generating SRT to {srt_path}")
                    video_processor.generate_word_level_srt(   
                        segments, 
                        str(srt_path), 
                        start_offset=moment["start"]
                    )
                    subtitle_arg = str(srt_path)
                    log_debug(f"SRT generated. Exists? {Path(srt_path).exists()}")
                except Exception as e:
                    print(f"SRT generation failed for clip {i}: {e}")
                    log_debug(f"SRT generation failed: {e}")

            # Construct Style String if custom options are present
            base_style = STYLE_MAP.get(request.caption_style, STYLE_MAP["Classic"])
            final_style = base_style

            if request.custom_color:
                # Convert #RRGGBB to &HBBGGRR&
                hex_color = request.custom_color.lstrip('#')
                if len(hex_color) == 6:
                    r = hex_color[0:2]
                    g = hex_color[2:4]
                    b = hex_color[4:6]
                    ass_color = f"&H{b}{g}{r}&" 
                    # Replace PrimaryColour
                    final_style = re.sub(r"PrimaryColour=&H[0-9A-Fa-f]+&", f"PrimaryColour={ass_color}", final_style)

            if request.custom_bg_color:
                # If BG Color is provided, switch to Box style logic (simplified)
                hex_bg = request.custom_bg_color.lstrip('#')
                if len(hex_bg) == 6:
                    r = hex_bg[0:2]
                    g = hex_bg[2:4]
                    b = hex_bg[4:6]
                    ass_bg_color = f"&H{b}{g}{r}&"
                    
                    # Force BorderStyle=3
                    final_style = re.sub(r"BorderStyle=\d+", "BorderStyle=3", final_style)
                    final_style = re.sub(r"Shadow=\d+", "Shadow=0", final_style)
                    final_style = re.sub(r"OutlineColour=&H[0-9A-Fa-f]+&", f"OutlineColour={ass_bg_color}", final_style)

            if request.custom_size:
                final_style = re.sub(r"Fontsize=\d+", f"Fontsize={request.custom_size}", final_style)

            # Cut and Resize to Vertical with Captions
            log_debug(f"Cutting video (Subtitles: {subtitle_arg})")
            final_path = video_processor.cut_video(
                video_path=request.video_path,
                start_time=moment["start"],
                end_time=moment["end"],
                output_path=str(output_path),
                subtitle_path=subtitle_arg,
                style_name=request.caption_style,
                force_style_string=final_style
            )
            
            # Clean up SRT file
            if subtitle_arg and Path(subtitle_arg).exists():
                try:
                    # os.remove(subtitle_arg) # Disabled for debugging
                    pass
                except:
                    pass
            
            generated_clips.append({
                "path": str(final_path),
                "url": f"/static/{Path(final_path).name}",
                "reason": moment.get("reason", "AI Selected"),
                "start": moment["start"],
                "end": moment["end"],
                "title": moment.get("title", f"Clip {i+1}"),
                "description": moment.get("description", ""),
                "hashtags": moment.get("hashtags", [])
            })
            
        except Exception as e:
            print(f"Error processing clip {i}: {str(e)}")
            log_debug(f"Error processing clip {i}: {e}")
            pass

    return {
        "status": "completed",
        "original_file": request.file_id,
        "transcript": transcript if transcript else "No Transcript Available",
        "clips": generated_clips
    }


class RegenerateRequest(BaseModel):
    file_id: str
    start_time: float
    end_time: float
    caption_style: str = "Classic"
    custom_color: str = None # Expected format: #RRGGBB
    custom_bg_color: str = None # Expected format: #RRGGBB
    custom_size: int = None

@router.post("/regenerate")
async def regenerate_video(request: RegenerateRequest):
    print(f"Regenerating {request.file_id} [{request.start_time}-{request.end_time}] Style: {request.caption_style}")
    
    # 1. Load Transcript
    transcript_path = video_processor.output_dir / f"{request.file_id}_transcript.json"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript file not found. Cannot regenerate.")
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        segments = json.load(f)
    
    # 2. Generate SRT
    # Use a unique suffix for regen to avoid caching/overwriting issues?
    # Or just use "regen" prefix?
    import time
    ts = int(time.time())
    output_filename = f"{request.file_id}_regen_{ts}.mp4"
    output_path = video_processor.output_dir / output_filename
    srt_path = video_processor.output_dir / f"{request.file_id}_regen_{ts}.srt"
    
    try:
        video_processor.generate_word_level_srt(segments, str(srt_path), start_offset=request.start_time)
    except Exception as e:
        print(f"Error generating SRT: {e}")
        raise HTTPException(status_code=500, detail="SRT generation failed")

    # 3. Construct Style String
    base_style = STYLE_MAP.get(request.caption_style, STYLE_MAP["Classic"])
    final_style = base_style

    if request.custom_color:
        # Convert #RRGGBB to &HBBGGRR&
        # Strip #
        hex_color = request.custom_color.lstrip('#')
        if len(hex_color) == 6:
            r = hex_color[0:2]
            g = hex_color[2:4]
            b = hex_color[4:6]
            ass_color = f"&H{b}{g}{r}&" 
            # Replace PrimaryColour
            final_style = re.sub(r"PrimaryColour=&H[0-9A-Fa-f]+&", f"PrimaryColour={ass_color}", final_style)

    if request.custom_bg_color:
        # If BG Color is provided, we switch to Box style (BorderStyle=3)
        # Convert #RRGGBB to &HBBGGRR&
        hex_bg = request.custom_bg_color.lstrip('#')
        if len(hex_bg) == 6:
            r = hex_bg[0:2]
            g = hex_bg[2:4]
            b = hex_bg[4:6]
            ass_bg_color = f"&H{b}{g}{r}&"
            
            # Force BorderStyle=3
            final_style = re.sub(r"BorderStyle=\d+", "BorderStyle=3", final_style)
            # Set Shadow=0 to avoid weird look with box
            final_style = re.sub(r"Shadow=\d+", "Shadow=0", final_style)
            # Use OutlineColour for Box Background color in ASS with BorderStyle=3
            # Or use BackColour? FFmpeg usually maps OutlineColour to box color for BorderStyle=3
            # Let's replace OutlineColour with our custom BG color
            final_style = re.sub(r"OutlineColour=&H[0-9A-Fa-f]+&", f"OutlineColour={ass_bg_color}", final_style)

    if request.custom_size:
        # Replace Fontsize
        final_style = re.sub(r"Fontsize=\d+", f"Fontsize={request.custom_size}", final_style)

    print(f"Final Style String: {final_style}")

    # 4. Cut Video
    # We need to find the original video path?
    # We assume it is in uploads with {file_id}.mp4? Or we need to look it up.
    # The processed/ directory has clips, but we need source.
    # We can try to guess or search in uploads.
    video_path = Path("uploads") / f"{request.file_id}.mp4"  # Default assumption
    if not video_path.exists():
        # Try to find any extension
        found = list(Path("uploads").glob(f"{request.file_id}.*"))
        if found:
            video_path = found[0]
        else:
            raise HTTPException(status_code=404, detail="Original video file not found")

    try:
        final_path = video_processor.cut_video(
            video_path=str(video_path),
            start_time=request.start_time,
            end_time=request.end_time,
            output_path=str(output_path),
            subtitle_path=str(srt_path),
            style_name=request.caption_style, # Ignored if force_style_string is passed
            force_style_string=final_style
        )
        
        # Cleanup SRT
        try:
            # os.remove(str(srt_path))
            pass
        except:
            pass
            
        return {
            "status": "completed",
            "url": f"/static/{output_filename}",
            "path": str(final_path)
        }

    except Exception as e:
        print(f"Regeneration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")
