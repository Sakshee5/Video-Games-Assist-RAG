import requests
import os
from bs4 import BeautifulSoup
from readability import Document
import praw
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import pickle

from dotenv import load_dotenv
load_dotenv()

# Load API credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "test"
API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

metadata_path = "faiss_metadata.pkl"

# Load metadata storage
if os.path.exists(metadata_path):
    with open(metadata_path, "rb") as f:
        metadata_store = pickle.load(f)
else:
    metadata_store = {}

def check_existing_sources(url):
    """Check if a URL is already stored in FAISS metadata."""
    if any(meta["source_url"] == url for meta in metadata_store.values()):
        print(f"Skipping {url}, already extracted and embedded.")
        return None
    else:
        return url

    
def search_web(query, num_results=5):
    """Fetches top search results for a given query."""
    
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={SEARCH_ENGINE_ID}"

    response = requests.get(search_url)
    urls = []
    if response.status_code == 200:
        results = response.json()
        for item in results.get("items", [])[:num_results]:
            url = item["link"]
            if check_existing_sources(url):
                urls.append(url)
    else:
        print("Failed to fetch search results.")

    return urls

    

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)


def fetch_reddit_comments(post_url):
    """Fetches the main post + all comments from a Reddit thread into a single 'content' field."""
    try:
        submission = reddit.submission(url=post_url)

        # Start with the post title and content
        content = f"{submission.selftext}\n\nComments:\n"

        # Extract all comments (sorted by upvotes)
        submission.comments.replace_more(limit=None)  # Fetch all nested comments

        def extract_comments(comment, depth=0):
            """Recursively fetch all comments while preserving indentation."""
            nonlocal content
            indentation = "  " * depth  # Indent replies for readability
            content += f"{indentation}- {comment.body}\n"

            for reply in comment.replies:
                extract_comments(reply, depth + 1)  # Recursively fetch replies

        for top_comment in submission.comments:
            extract_comments(top_comment)  # Start extracting from top-level comments

        return {
            "title": submission.title,
            "content": content,
            "restricted": ""
        }

    except Exception as e:
        return {"title" : "", "content": str(e), "restricted" : post_url}

def format_timestamp(seconds):
    """Convert seconds into MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def extract_youtube_transcript(video_url):
    """Extracts the transcript with timestamps in MM:SS format from a YouTube video URL."""
    # Extract video ID from URL
    parsed_url = urlparse(video_url)
    video_id = parse_qs(parsed_url.query).get("v", [None])[0]

    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        content = ""
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        for metadata in transcript:
            start_time = format_timestamp(metadata['start'])
            end_time = format_timestamp(metadata['start'] + metadata['duration'])
            content += f"{metadata['text']} ({start_time} - {end_time})\n"

        return {"title" : "", "content": content, "restricted" : ""}
    
    except Exception as e:
        return {"title" : "", "content": str(e), "restricted" : video_url}

def fetch_page_content(url):
    """Scrapes the given URL and extracts clean text content along with metadata."""
    headers = {"User-Agent": "Mozilla/5.0"} 
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        extracted = soup.get_text()

        return {
            "title": Document(response.text).title(),
            "content": extracted.strip(),
            "restricted": ""
        }

    except requests.exceptions.RequestException as e:
        return {"title" : "", "content": str(e), "restricted" : url}

if __name__ == "__main__":
    urls = search_web("Where to find gold bars in RDR2?")
    for url in urls:
        if "reddit.com" in url:
            print("\nFetching from Reddit:", url)
            reddit_data = fetch_reddit_comments(url)
            print(reddit_data)

        elif "youtube.com" in url:
            print("\nFetching from Youtube:", url)
            youtube_data = extract_youtube_transcript(url)
            print(youtube_data)

        else:
            print("\nScraping website:", url)
            web_data = fetch_page_content(url)
            print(web_data)
