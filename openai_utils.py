import os

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text):
    """Fetches the embedding of the text."""
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding

def get_response(question):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=question,
    )
    return completion.choices[0].message