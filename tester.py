import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

key =os.getenv("OPEN_AI_KEY")
client = OpenAI(api_key=key)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "explain 2d kinematics in great detail",
        }
    ],
    model="o1-preview",
)

prompt = (chat_completion.choices[0].message.content)

code = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt + "explain all of this using manim to create visualtions for each concept with transition frm each concept to another using clear and precise drawing and texts that do not overlap."
        }
    ],
    model="o1-preview"
)

print(code.choices[0].message.content)