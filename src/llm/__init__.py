import os
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()


MODEL_NAME = os.environ.get("MODEL_NAME")

CLIENT = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE_URL"),
)
