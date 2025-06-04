import utils
import json
import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import random

prompt1 = """

For the stock {stock}, answer the following questions with the most recent up-to-date information to the best of your ability. Separate your answer by new lines:

- What is the high, average and low price? Format your output exactly like this: "<high>, <average>, <low>"
- What is the price-earnings ratio? Provide just the number.
- What is the current dividend? Provide just the number as a percentage.
- What is the 52-week high and low? Format your output exactly like this: "<52-week high>, <52-week low>"
- What is the market capitalization? Provide just the number.
- What is the beta? Provide just the number.
- What is the volume? Provide just the number.
- What is the average volume? Provide just the number.
- What is the market cap? Provide just the number.
- What is the market cap to sales ratio? Provide just the number.
- What is the price-to-sales ratio? Provide just the number.
- What is the price-to-book ratio? Provide just the number.
"""

prompt2 = """

"""

prompt2 = """

"""

system_instruction = """
you are a helpful assistant.. Your outputs should contain nothing more than what the prompts ask for. 
"""

class LLM:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=utils.get_api_key())
        self.model = model
        self.image_output_dir = "outputs/image"
        self.text_output_dir = "outputs/script"

    def generate_response(self, prompt):
        contents = [prompt]
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.7
            )
        )
        return response.text
    
        

    