from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from services.analysis import analyzer
import json

router = APIRouter()

class RocketRequest(BaseModel):
    clip_path: str  # Path to the video clip
    clip_title: str = ""  # Optional title hint
    clip_reason: str = ""  # Why this clip is interesting
    video_context: str = ""  # Transcript or context from the video

@router.post("/generate")
async def generate_rocket_content(request: RocketRequest):
    """
    Generate viral captions, hashtags, and descriptions for a video clip.
    Uses AI to analyze the video context and create engaging social media content.
    """
    
    # Try to load transcript if video_context not provided
    video_context = request.video_context
    if not video_context and request.clip_path:
        # Try to find transcript from file_id
        try:
            clip_path = Path(request.clip_path)
            file_id = clip_path.stem.split('_short_')[0] if '_short_' in clip_path.stem else clip_path.stem
            transcript_path = Path("processed") / f"{file_id}_transcript.json"
            
            if transcript_path.exists():
                with open(transcript_path, "r", encoding="utf-8") as f:
                    segments = json.load(f)
                    # Extract text from segments
                    video_context = " ".join([seg.get("text", "") for seg in segments[:50]])
        except Exception as e:
            print(f"Could not load transcript: {e}")
    
    # Generate viral content using AI
    result = analyzer.generate_viral_content(
        video_context=video_context,
        clip_title=request.clip_title,
        clip_reason=request.clip_reason
    )
    
    return {
        "success": True,
        "content": result
    }
