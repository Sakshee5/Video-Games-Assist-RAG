import requests
import os

from bs4 import BeautifulSoup
from readability import Document
import praw
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from pytube import YouTube

from dotenv import load_dotenv
load_dotenv()

# Load API credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "test"
API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")


def search_web(query, num_results=3):
    """Fetches top search results for a given query."""
    
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={SEARCH_ENGINE_ID}"

    # For YouTube
    search_url_youtube = f"https://www.googleapis.com/customsearch/v1?q={query} site:youtube.com&key={API_KEY}&cx={SEARCH_ENGINE_ID}"

    response = requests.get(search_url)
    response_youtube = requests.get(search_url_youtube)
    
    if response.status_code == 200:
        results = response.json()
        urls = [item["link"] for item in results.get("items", [])[:num_results]]
    else:
        print("Failed to fetch search results.")

    if response_youtube.status_code == 200:
        results = response_youtube.json()
        youtube_urls = [item["link"] for item in results.get("items", [])[:num_results]]
    else:
        print("Failed to fetch YouTube search results.")

    return urls + youtube_urls

    

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)


def fetch_reddit_comments(post_url, num_comments=5):
    """Fetches the main post + top comments from a Reddit thread."""
    submission = reddit.submission(url=post_url)

    # Extract main post
    post_data = {
        "title": submission.title,
        "content": submission.selftext,
    }

    # Extract top N comments (sorted by upvotes)
    submission.comments.replace_more(limit=0)  # Remove "load more comments" placeholders
    for top_comment in submission.comments[:num_comments]:
        post_data["content"] += f"\n{top_comment.body}"

    return post_data

def extract_youtube_transcript(video_url):
    """Extracts the transcript and timestamps from a YouTube video URL."""
    # Extract video ID from URL
    parsed_url = urlparse(video_url)
    video_id = parse_qs(parsed_url.query).get("v", [None])[0]

    try:
        yt = YouTube(video_url)
        title = yt.title
        print(f"The title of the video is: {title}")
    except Exception as e:
        title = str(e)
        print(f"An error occurred: {e}")

    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        content = ""
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        for metadata in transcript:
            content += f"{metadata['text']} (start: {metadata['start']}, duration: {metadata['duration']})\n" 

        return {
            "title": title,
            "content": content
            }
    
    except Exception as e:
        return {"error": str(e)}

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
            "content": extracted.strip() if extracted else "Content could not be extracted.",
        }

    except requests.exceptions.RequestException as e:
        return {"title": "", "content": str(e)}

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
