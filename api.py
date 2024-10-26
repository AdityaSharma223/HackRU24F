from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import base64
import os
from manim import *

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
async def query_AI(question: str = Form(...), image_file: UploadFile = File(...)):
    image_path = f"temp_{image_file.filename}"
    with open(image_path, "wb") as buffer:
        buffer.write(await image_file.read())
    base64_image = encode_image(image_path)
    video = feed_AI(question, image_path)
    #os.remove(image_path)
    return FileResponse(video)
    # Return a video file based on the question and image if needed

def feed_AI(question, image_b64):
    print(f"ChatGTP Recieved: {question} and {image_b64}")
    return None
