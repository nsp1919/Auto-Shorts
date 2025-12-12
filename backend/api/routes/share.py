from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.social_media import social_manager

router = APIRouter()

class InstaShareRequest(BaseModel):
    video_path: str
    caption: str
    username: str = None
    password: str = None

@router.post("/instagram")
async def share_instagram(request: InstaShareRequest):
    """
    Share video to Instagram.
    """
    # Verify path exists
    # request.video_path comes from frontend, usually absolute path from previous response
    
    result = social_manager.upload_to_instagram(
        request.video_path, 
        request.caption,
        request.username,
        request.password
    )
    
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))
