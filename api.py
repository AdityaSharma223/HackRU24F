from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

class QueryRequest(BaseModel):  # Define a request model
    question: str
    image_url: str


@app.post("/video")
def query_AI(query: QueryRequest):  # Use the model as a parameter
    feed_AI(query.question)
    output_file = r"C:\Users\loorj\OneDrive\Documents\FastAPI_Testing\FastAPI\videos\1080p60\Video.mp4"
    output_dir = r"C:\Users\loorj\OneDrive\Documents\FastAPI_Testing\FastAPI"
    
    config.media_dir = output_dir # Set output directory for media files
    config.output_file = "Video.mp4"
    config.disable_caching = True
    scene = SimilarTriangles()  # Create an instance of your scene
    scene.render()
    return FileResponse(output_file)

def feed_AI(question):
    print(f"ChatGTP Recieved: {question}")

    #python -m uvicorn main:app --reload
    #python -m