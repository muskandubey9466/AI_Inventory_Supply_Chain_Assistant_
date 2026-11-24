
import os
import pandas as pd

from dotenv import load_dotenv
from google import genai


load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


def ask_inventory_ai(df, question):

    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY missing. Please configure your .env file."
        )

    if df is None or df.empty:
        raise ValueError("Please upload a valid inventory dataset.")

    client = genai.Client(
        api_key=API_KEY
    )

    # Limit context size for large datasets
    sample = df.head(100).copy()

    dataset_context = sample.to_string(
        index=False,
        max_cols=30
    )

    prompt = f"""
You are an expert AI Inventory and Supply Chain Assistant.

Analyze the uploaded inventory dataset and answer the user's question.

IMPORTANT RULES:

1. Use only information supported by the uploaded dataset.
2. Do not invent missing values.
3. Clearly mention when information is unavailable.
4. Give practical inventory recommendations.
5. Explain stock risks and replenishment opportunities.
6. Use tables and bullet points where helpful.
7. Do not claim to predict future demand without historical demand data.

DATASET COLUMNS:
{list(df.columns)}

TOTAL DATASET ROWS:
{len(df)}

DATASET SAMPLE:
{dataset_context}

USER QUESTION:
{question}

Provide a clear, professional business-oriented answer.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text
