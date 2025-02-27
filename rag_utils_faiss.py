import faiss
import numpy as np
import tiktoken
from openai_utils import get_embedding
import pickle
import os

# Set parameters
token_per_chunk = 2000
faiss_index_path = "faiss_index.bin"
metadata_path = "faiss_metadata.pkl"

embedding_dim = 1536 
index = faiss.IndexFlatIP(embedding_dim)

# Load metadata storage
if os.path.exists(metadata_path):
    with open(metadata_path, "rb") as f:
        metadata_store = pickle.load(f)
else:
    metadata_store = {}

# Load FAISS index if it exists
if os.path.exists(faiss_index_path):
    index = faiss.read_index(faiss_index_path)


def reset_metadata_and_index():
    """Reset the metadata store and FAISS index."""
    global metadata_store, index
    metadata_store = {}
    index = faiss.IndexFlatL2(embedding_dim)
    
    # Save empty structures
    faiss.write_index(index, faiss_index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata_store, f)
    print("Metadata and index have been reset.")

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
    """Chunks content, generates embeddings, and stores them in FAISS."""
    global index

    for entry in data:
        source_url = entry["source_url"]
        title = entry["title"]
        content = entry["content"]

        # Split content into chunks
        chunks = chunk_text(content) if len(content.split()) > token_per_chunk else [content]

        for idx, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            embedding_np = np.array([embedding], dtype=np.float32)

            # Store in FAISS
            index.add(embedding_np)

            # Save metadata
            metadata_store[len(metadata_store)] = {
                "source_url": source_url,
                "title": title,
                "content_chunk": chunk
            }

    # Save FAISS index & metadata
    faiss.write_index(index, faiss_index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata_store, f)

def retrieve_top_chunks(question, top_n=2):
    """Retrieve top N most relevant chunks for a question using FAISS."""
    global index
    if index.ntotal == 0:
        return "No data available in the index. Please add some content first."
    
    question_embedding = get_embedding(question)
    question_np = np.array([question_embedding], dtype=np.float32)

    # Search FAISS for nearest neighbors
    distances, indices = index.search(question_np, top_n)

    # Extract relevant information
    context = ""
    for i in range(top_n):
        idx = indices[0][i]
        if idx in metadata_store:
            source_url = metadata_store[idx]["source_url"]
            title = metadata_store[idx]["title"]
            content_chunk = metadata_store[idx]["content_chunk"]

            context += f"{source_url}\n"
            if title:
                context += f"{title}\n"
            context += f"{content_chunk}\n\n"

    return context
