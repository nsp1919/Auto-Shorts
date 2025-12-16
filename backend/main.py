from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import upload, process

app = FastAPI(title="Auto Shorts Maker API", version="1.0.0")

# CORS Configuration
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(process.router, prefix="/api/process", tags=["Process"])
from api.routes import share, rocket
app.include_router(share.router, prefix="/api/share", tags=["Share"])
app.include_router(rocket.router, prefix="/api/rocket", tags=["Rocket Share"])


# Serve Processed Videos
app.mount("/static", StaticFiles(directory="processed"), name="static")

@app.get("/")
def read_root():
    return {"message": "Auto Shorts Maker API is running"}
