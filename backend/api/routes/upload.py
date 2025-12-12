import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file to the server.
    Returns the file_id and filename.
    """
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video.")

    # Generate unique ID
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    saved_filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / saved_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "saved_path": str(file_path),
        "message": "Upload successful"
    }
