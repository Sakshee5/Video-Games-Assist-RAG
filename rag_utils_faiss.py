import faiss
import numpy as np
import tiktoken
import pickle
import os
from openai_utils import get_embedding

# Configurations
token_per_chunk = 2000
faiss_index_path = "faiss_index.bin"
metadata_path = "faiss_metadata.pkl"
embedding_dim = 1536
chunk_overlap = 100  # Overlapping tokens for better context retention

# Initialize FAISS index
index = faiss.IndexFlatIP(embedding_dim)  # Using cosine similarity
index = faiss.IndexIDMap(index)  # Enables mapping embeddings to metadata IDs

# Load metadata
if os.path.exists(metadata_path):
    with open(metadata_path, "rb") as f:
        metadata_store = pickle.load(f)
else:
    metadata_store = {}

# Load FAISS index
if os.path.exists(faiss_index_path):
    index = faiss.read_index(faiss_index_path)

def reset_metadata_and_index():
    """Reset metadata and FAISS index."""
    global metadata_store, index
    metadata_store = {}
    index = faiss.IndexFlatIP(embedding_dim)
    index = faiss.IndexIDMap(index)

    # Save empty structures
    faiss.write_index(index, faiss_index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata_store, f)
    print("Metadata and index have been reset.")

def chunk_text(text, max_tokens=token_per_chunk, overlap=chunk_overlap):
    """Splits text into overlapping chunks with a token limit."""
    enc = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = enc.encode(text)
    
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i : i + max_tokens]
        chunks.append(enc.decode(chunk))
        i += max_tokens - overlap  # Overlap for better retention
    
    return chunks

def chunk_and_vectorize(data):
    """Chunks content, generates embeddings, and stores them in FAISS."""
    global index

    new_embeddings = []
    new_ids = []
    new_metadata = {}

    current_id = len(metadata_store)  # Start from existing metadata count

    for entry in data:
        source_url = entry["source_url"]
        title = entry["title"]
        content = entry["content"]

        # Split content into chunks
        chunks = chunk_text(content) if len(content.split()) > token_per_chunk else [content]

        for chunk in chunks:
            embedding = get_embedding(chunk)
            embedding_np = np.array([embedding], dtype=np.float32)

            # Normalize embedding for cosine similarity
            faiss.normalize_L2(embedding_np)

            new_embeddings.append(embedding_np)
            new_ids.append(current_id)

            # Store metadata
            new_metadata[current_id] = {
                "source_url": source_url,
                "title": title,
                "content_chunk": chunk
            }

            current_id += 1

    # Add to FAISS index
    if new_embeddings:
        index.add_with_ids(np.vstack(new_embeddings), np.array(new_ids))

    # Update metadata storage
    metadata_store.update(new_metadata)

    # Save FAISS index & metadata
    faiss.write_index(index, faiss_index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata_store, f)

def retrieve_top_chunks(question, top_n=2):
    """Retrieve top N most relevant chunks for a given query."""
    global index
    if index.ntotal == 0:
        return "No data available in the index. Please add some content first."
    
    question_embedding = get_embedding(question)
    question_np = np.array([question_embedding], dtype=np.float32)

    # Normalize for cosine similarity search
    faiss.normalize_L2(question_np)

    # Search FAISS for nearest neighbors
    distances, indices = index.search(question_np, top_n)

    # Extract relevant information
    results = []
    for i in range(top_n):
        idx = indices[0][i]
        if idx in metadata_store:
            source_url = metadata_store[idx]["source_url"]
            title = metadata_store[idx]["title"]
            content_chunk = metadata_store[idx]["content_chunk"]
            results.append(f"{source_url}\n{title}\n{content_chunk}\n\n")

    return "\n".join(results)
