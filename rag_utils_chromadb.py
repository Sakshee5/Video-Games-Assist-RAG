import chromadb
import tiktoken
from openai_utils import get_embedding

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # Persistent storage

# Create (or get) a collection for game sources
collection = chroma_client.get_or_create_collection(name="game_sources")

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
    """Chunks large content, generates embeddings, and stores them in ChromaDB."""
    for entry in data:
        source_url = entry["source_url"]
        title = entry["title"]
        content = entry["content"]

        # Split content into chunks
        chunks = chunk_text(content) if len(content.split()) > token_per_chunk else [content]

        for idx, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)

            # Store in ChromaDB
            collection.add(
                ids=[f"{source_url}_{idx}"],  # Unique ID for each chunk
                embeddings=[embedding],
                metadatas=[{"source_url": source_url, "title": title, "content_chunk": chunk}]
            )


def retrieve_top_chunks(question, top_n=2):
    """Retrieve top N most relevant chunks for a question from ChromaDB."""
    question_embedding = get_embedding(question)

    # Query ChromaDB for similar embeddings
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_n  # Retrieve top N matches
    )

    # Extract relevant information
    context = ""
    for i in range(len(results["ids"][0])):  # Loop through returned results
        source_url = results["metadatas"][0][i]["source_url"]
        title = results["metadatas"][0][i]["title"]
        content_chunk = results["metadatas"][0][i]["content_chunk"]

        context += source_url + '\n'
        if title:
            context += title + '\n'
        context += content_chunk + '\n\n'

    return context


