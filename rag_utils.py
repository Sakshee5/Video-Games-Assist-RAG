import ast
import numpy as np
from openai_utils import get_embedding
import tiktoken
import pandas as pd

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_top_chunks(question, df, top_n=2):
    """Retrieve the top N most relevant chunks for a question."""
    try:
        df["embedding"] = df["embedding"].apply(ast.literal_eval)
    except:
        pass

    question_embedding = get_embedding(question)
    df["similarity"] = df["embedding"].apply(lambda x: cosine_similarity(question_embedding, x))
    top_chunks = df.sort_values(by="similarity", ascending=False).head(top_n)
    top_chunks = top_chunks.drop(['embedding', 'similarity'], axis=1)

    context = ""

    for _, row in top_chunks.iterrows():
        context += row['source_url'] + '\n'

        if row['title']:
            context += row['title'] + '\n'

        context += row['content_chunk'] + '\n\n'

    return context


token_per_chunk = 2000

def chunk_text(text, max_tokens=token_per_chunk):
    """Splits text into chunks with a maximum token limit."""
    enc = tiktoken.encoding_for_model("text-embedding-3-small") 
    tokens = enc.encode(text)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(enc.decode(chunk))  # Convert back to text
    
    return chunks

def chunk_and_vectorize(data):
    """Chunks large content, generates embeddings, and returns structured data."""
    processed_data = []

    for entry in data:
        source_url = entry["source_url"]
        title = entry["title"]
        content = entry["content"]

        chunks = chunk_text(content) if len(content.split()) > token_per_chunk else [content]

        for chunk in chunks:
            embedding = get_embedding(chunk)
            processed_data.append({
                "source_url": source_url,
                "title": title,
                "content_chunk": chunk,
                "embedding": embedding
            })

    # Convert to DataFrame for easy storage
    df = pd.DataFrame(processed_data)
    # df.to_excel("test.xlsx", index=False)
    
    return df