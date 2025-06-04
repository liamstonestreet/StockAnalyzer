import utils
from google import genai
from google.genai import types

stock_analysis_prompt = """
For the stock with this ticker: '{stock}', answer the following questions with the most recent up-to-date information to the best of your ability. Separate your answer by new lines.

- What is the current stock price?"
- What is the price-earnings ratio? Provide just the number.
- What is the current dividend? Provide just the number as a percentage.
- What is the 52-week high and low? Format your output exactly like this: "<52-week high>, <52-week low>"
- Has there been insider buying in the last 6 months? Provide "yes" or "no".
"""

suggestion_prompt = """
Consider the company with this ticker: {ticker}.
Here is a filtered covered call options chain for this company:

{options_chain}

Additionally, here are the stock fundamentals for this company:

{stock_fundamentals}

With this information, pick the best 2 to 3 contracts to sell based on delta, premium, and time to expiration. 
Explain your reasoning in plain English.
"""


system_instruction = """
You are a conservative stock options trading expert.
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
                max_output_tokens=1000,
                temperature=0.7
            )
        )
        return response.text
    
        

    