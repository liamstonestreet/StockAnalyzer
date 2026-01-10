import utils
from google import genai
from google.genai import types

system_instruction = """
You are a stock options trading expert who understands prominent trading strategies.
You speak in a clear and concise manner.
"""

class LLM:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=utils.get_api_key())
        self.model = model

    def ask(self, prompt):
        contents = [prompt]
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=1700,
                temperature=0.7
            )
        )
        return response.text
    
        

    