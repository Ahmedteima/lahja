from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path

from lahja import process_video

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def home():
    return {"message": "Lahja Backend Running"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    output_path = UPLOAD_DIR / f"processed_{file.filename}"

    process_video(
        video_path=file_path,
        output_path=output_path
    )

    return {
        "input_file": file.filename,
        "output_file": output_path.name,
        "status": "processing completed"
    }