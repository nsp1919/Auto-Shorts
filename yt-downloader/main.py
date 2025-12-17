from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import yt_dlp
import tempfile
import os
import shutil

app = FastAPI(title="YT-DLP Microservice")

@app.get("/download")
def download_youtube(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL required")

    tmp_dir = tempfile.mkdtemp()
    
    # Clean up title to be safe for filenames
    outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "mp4/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        # Robust network options for various hosting providers
        "force_ipv4": True,
        "socket_timeout": 30,
    }

    try:
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # Generator to stream file and delete temp dir afterwards
        def iterfile():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(1024 * 1024): # 1MB chunks
                        yield chunk
            finally:
                # Cleanup after streaming is done
                try:
                    shutil.rmtree(tmp_dir)
                except Exception as e:
                    print(f"Error cleaning up {tmp_dir}: {e}")

        filename = os.path.basename(file_path)
        
        # Determine media type based on extension
        media_type = "video/mp4"
        if filename.endswith(".webm"):
            media_type = "video/webm"
        elif filename.endswith(".mkv"):
            media_type = "video/x-matroska"

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except Exception as e:
        # Cleanup on error if temp dir exists
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "downloader-service-running"}
