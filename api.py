from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import base64
from manim import *
import os
import video

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@app.post("/video")
async def query_AI(question: str = Form(...), image_file: UploadFile = File(None)):
    if image_file:
        image_path = f"temp_{image_file.filename}"
        with open(image_path, "wb") as buffer:
            buffer.write(await image_file.read())
        base64_image = encode_image(image_path)
    file_id = video.generate_manim_visualization(question)
    current_directory = os.path.dirname(os.path.abspath(__file__))
    output_video_path = os.path.join(current_directory, 'output_videos', f'{file_id}.mp4')
    print(output_video_path)
    #os.remove(image_path)
    return FileResponse(output_video_path)
