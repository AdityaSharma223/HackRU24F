from openai import OpenAI
import subprocess
import os
import re
from dotenv import load_dotenv
import json
import time
import logging
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define post_process_latex function here
def post_process_latex(manim_code):
    # Fix common LaTeX errors
    manim_code = manim_code.replace(r'\f\frac', r'\frac')
    manim_code = manim_code.replace(r'\\frac', r'\frac')
    # Add more replacements if needed
    return manim_code

class ManimVisualization(BaseModel):
    manim_code: str
    description: str

def generate_manim_visualization(query, output_folder='./output_videos'):
    start_time = time.time()

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    logging.info(f"Starting visualization generation for query: {query}")

    logging.info("Querying o1-preview model...")
    o1_start_time = time.time()
    o1_response = client.chat.completions.create(
        model="o1-preview",
        messages=[
            {
                "role": "user",
                "content": f"""
Generate Manim code (Community Edition v0.17.0+) to visualize: "{query}"

Requirements:
0. LaTeX: Use single backslash for commands, e.g., \frac{{num}}{{den}} for fractions.
1. Use latest Manim syntax (e.g., 'Create' instead of 'ShowCreation').
2. Structure: Intro, Problem Statement, Visualization, Explanation, Conclusion.
3. Use MathTex for math, Text for regular text. No $ symbols in MathTex.
4. Only use LaTeX from: amsmath, amssymb, mathtools, physics, xcolor.
5. Ensure readability: proper spacing, consistent fonts, colors. Make sure all the text other than the title has a font size of 24.
6. Use smooth animations and transitions.
7. Code must be clean, well-commented, and organized.
8. Make sure that the render is zoomed out so that all the text is in the frame and can be seen.
9. Have multiple scenes that are rendered and cleared before next scene comes on. Dont accept user input, instead merge all the scenes into one video.

LaTeX Examples:
- Correct: r"\frac{{a}}{{b}}"
- Incorrect: r"\f\frac{{a}}{{b}}" or r"\\frac{{a}}{{b}}"

Example structure:
```python
from manim import *

class ConceptVisualization(Scene):
    def construct(self):
        # Introduction
        title = Text("Concept Title")
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))

        # Problem Statement
        problem = Text("Problem description")
        self.play(Write(problem))

        # Visualization
        # (Add relevant visual elements and animations)

        # Explanation
        explanation = MathTex(r"E = mc^2")
        self.play(Write(explanation))

        # Conclusion
        conclusion = Text("Key takeaways")
        self.play(Write(conclusion))

        self.wait(2)
```

Provide only a JSON response with:
- manim_code: Complete Manim code as a string
- description: Brief description of the visualization

No additional text or explanations outside the JSON structure.
"""
            }
        ]
    )
    o1_end_time = time.time()
    logging.info(
        f"o1-preview model response received in {o1_end_time - o1_start_time:.2f} seconds")

    o1_content = o1_response.choices[0].message.content

    o1_log_filename = os.path.join(output_folder, 'o1_response_log.json')
    with open(o1_log_filename, 'w') as f:
        json.dump(o1_response.model_dump(), f, indent=2)
    logging.info(f"o1 response logged to {o1_log_filename}")

    logging.info("Parsing o1 response with gpt-4o-mini...")
    parse_start_time = time.time()
    parse_response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"Given the following data, format it with the given response format: {o1_content}"
            }
        ],
        response_format=ManimVisualization,
    )
    parse_end_time = time.time()
    logging.info(
        f"gpt-4o-mini parsing completed in {parse_end_time - parse_start_time:.2f} seconds")

    parse_log_filename = os.path.join(output_folder, 'parse_response_log.json')
    with open(parse_log_filename, 'w') as f:
        json.dump(parse_response.model_dump(), f, indent=2)
    logging.info(f"Parse response logged to {parse_log_filename}")

    parsed_data = parse_response.choices[0].message.parsed
    manim_code = parsed_data.manim_code
    manim_code = post_process_latex(manim_code)
    description = parsed_data.description

    manim_code_filename = os.path.join(
        output_folder, 'generated_manim_code.py')
    with open(manim_code_filename, 'w') as f:
        f.write(manim_code)
    logging.info(f"Manim code saved to {manim_code_filename}")

    logging.info("Executing Manim code...")
    manim_start_time = time.time()
    try:
        result = subprocess.run(
            ['manim', '-pqh', manim_code_filename],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("Manim output:")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Manim: {e}")
        logging.error("Manim error output:")
        # Changed from e.output to e.stderr for more specific error output
        logging.error(e.stderr)
        logging.error("Check the generated Manim code for potential errors.")

        # Attempt to fix common LaTeX errors
        with open(manim_code_filename, 'r') as f:
            manim_code = f.read()

        # Add more replacements here based on common errors
        manim_code = manim_code.replace('rac{', r'\frac{')

        # Save the corrected code
        with open(manim_code_filename, 'w') as f:
            f.write(manim_code)

        logging.info(
            "Attempted to fix LaTeX errors. Retrying Manim execution...")

        # Retry Manim execution
        try:
            result = subprocess.run(
                ['manim', '-pqh', manim_code_filename],
                check=True,
                capture_output=True,
                text=True
            )
            logging.info("Manim output after correction:")
            logging.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running Manim after correction: {e}")
            logging.error("Manim error output after correction:")
            logging.error(e.stderr)
            return

    manim_end_time = time.time()
    logging.info(f"Manim execution completed in {manim_end_time - manim_start_time:.2f} seconds")

    # Step 5: Move the generated video to the output folder
    class_name_match = re.search(r'class\s+(\w+)\(Scene\):', manim_code)
    if class_name_match:
        class_name = class_name_match.group(1)
        media_dir = os.path.join('media', 'videos', os.path.splitext(
            os.path.basename(manim_code_filename))[0])
        video_found = False
        for root, dirs, files in os.walk(media_dir):
            for file in files:
                if file == f'{class_name}.mp4':
                    video_path = os.path.join(root, file)
                    output_video_path = os.path.join(
                        output_folder, f'{class_name}.mp4')
                    os.rename(video_path, output_video_path)
                    video_found = True
                    logging.info(f"Video file moved to {output_video_path}")
                    break
            if video_found:
                break
        if not video_found:
            logging.warning(f"Video file for class '{class_name}' not found.")
    else:
        logging.error("Could not find the class name in the Manim code.")

    # Save the description
    description_filename = os.path.join(
        output_folder, 'visualization_description.txt')
    with open(description_filename, 'w') as f:
        f.write(description)
    logging.info(f"Visualization description saved to {description_filename}")

    end_time = time.time()
    total_time = end_time - start_time
    logging.info(f"Manim visualization process completed in {total_time:.2f} seconds")


# Example usage
generate_manim_visualization(
    "Explain 1D motion in physics")
