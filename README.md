# Stocks Analyzer

A program that analyzes stocks and recommends covered calls with fine-tuned parameters (strike price, expiration date, etc).

## Installation Guide
1. Ensure Python 3.13.4 is used.
2. Install requirements.txt using `pip install -r requirements.txt`
3. Run `streamlit run Home.py` to run the streamlit.

## Notes
- `keys.txt` contains only the Gemini API key.
- `main.py` and `llm.py` were used previously to produce LLM opinions on how to make optimal covered call decisions.

## TODO
- Implement Shadow Premium feature.
- Fix safety calculation to be more accurate. (i.e. it says it's safe when strike << market)``