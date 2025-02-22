# 🎮 Video Game Assistant Guide

## Overview

The Video Game Assistant is a Streamlit-based AI tool designed to help gamers quickly find solutions to in-game challenges. It retrieves data from YouTube, forums, and web guides, prioritizes sources based on RAG and provides accurate and actionable answers, including video timestamps for Youtube Sources.

## Features

1. AI-powered search for video game solutions.
2. Retrieves data from YouTube, Reddit, web guides, and other sources.
3. Extracts and summarizes key information with citations.
4. Identifies YouTube timestamps for in-game solutions.
5. Handles restricted URLs gracefully by informing users when content cannot be scraped.


## How It Works

1. Enter a video game-related question in the chat.
2. The system searches the web for relevant sources.
3. It fetches content from Reddit, YouTube, and other web pages.
4. The tool chunks and vectorizes the content using FAISS.
5. It retrieves the most relevant text and generates a summarized response.
6. If the data is restricted, it provides direct URLs for users to check manually.

## Technologies Used

1. Streamlit – Interactive UI for the assistant.
2. OpenAI API – Generates responses based on retrieved context.
3. ChromaDB – Efficient vector storage and retrieval
4. BeautifulSoup – Web scraping
5. Google Search API – Fetches relevant web sources.
6. YouTube Transcript API - To retrieve Youtube transcripts with timestamps
7. Reddit API - To retrive post, comments and replied from Reddit Discussions.

## Future Improvements
1. Support for follow-up questions. Example: If they ask, "How to complete Cornwall oil mission?" and then "What happens if I choose a different path?"
2. Scrape and embed website images. (Generally maps would be useful)