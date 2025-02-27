from openai_utils import get_response
from api_utils import fetch_reddit_comments, extract_youtube_transcript, fetch_page_content, search_web
from rag_utils_faiss import retrieve_top_chunks, chunk_and_vectorize, reset_metadata_and_index

import streamlit as st

with st.sidebar:
    st.header("🎮 Game Assistant Guide")
    
    st.write(
        "Welcome to the Video Game Assistant! This tool helps you find quick answers for video games by retrieving data from YouTube, forums, and guides."
    )

    st.subheader("⚡ How It Works")
    st.write(
        "- **Ask any question** related to any video games.\n"
        "- The assistant searches for **relevant gameplay info**.\n"
        "- If available, it provides **exact video timestamps** or summarizes key solutions.\n"
        "- Sources include **YouTube, web sources, forums, and guides**."
    )

    st.subheader("🎯 Example Questions")
    st.write(
        "- *How do i do the cornwall oil mission in RDR2?*\n"
        "- *How to complete mission of saving Sean from Blackwater without getting killed by bounty hunters in RDR2?*\n"
        "- *How to open chest with eyes in Hogwarts Legacy?*\n"
        "- *Where to find precursor artifact in voyagers of Nera?*"
    )

    st.info("Try asking a question in the chat!")
    st.error("Disclaimer: A random non-game based question will also work but the prompts have been curated for Video Game Questions..")

    st.divider()

    st.subheader("📚 Data Sources")
    st.write(
        "- **YouTube walkthroughs & guides** (retrieved via API & search)\n"
        "- **Reddit discussions & gaming forums**\n"
        "- **Game wikis and online guides**"
    )

    st.subheader("🔄 Pipeline")
    st.write(
        "1. **User Input**: Player asks a game-related question.\n"
        "2. **Web Scraping & Retrieval**: Searches YouTube, Reddit, and forums for relevant content. Top 10 URLs are scraped.\n"
        "3. **Text Processing**: Extracts key text from videos (timestamps), forums, and guides.\n"
        "4. **FAISS Vector Search**: Stores processed text embeddings for quick retrieval.\n"
        "5. **LLM Response Generation**: Uses OpenAI language model to summarize and provide a direct answer.\n"
        "6. **Final Output**: Displays the best response with sources (including video timestamps if available)."
    )

    st.subheader("🤖 Model & Tech Stack")
    st.write(
        "- **Embedding Model**: `text-embedding-3-small` by OpenAI\n"
        "- **Vector Database**: `FAISS` for efficient similarity search\n"
        "- **LLM**: OpenAI `gpt-4o-mini` for answer generation\n"
        "- **Scraping**: `BeautifulSoup` and `Requests`, `YouTube Transcript API`, `Praw` Reddit API for content retrieval\n"
        "- **Deployment**: Streamlit for frontend, Python backend"
    )
st.header("🎮 Video Game Assist")


sys_prompt = """You are an expert Video Game Assistant.

Your job is to help users solve challenges they encounter in these games by providing clear, actionable answers based only on context provided."""


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": sys_prompt}]

# Display chat messages from session state
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User input
if user_input := st.chat_input("Ask a question..."):
    urls = search_web(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(f"{user_input}")

    with st.chat_message("assistant"):
        restricted_urls = []
        try:
            with st.spinner("Searching the Web for relevant sources..."):
                data_frm_the_web = []
                for url in urls:
                    if "reddit.com" in url:
                        print("\nFetching from Reddit:", url)
                        extracted_data = fetch_reddit_comments(url)

                    elif "youtube.com" in url:
                        print("\nFetching from Youtube:", url)
                        extracted_data = extract_youtube_transcript(url)

                    else:
                        print("\nScraping website:", url)
                        extracted_data = fetch_page_content(url)

                    title, content, restricted = extracted_data['title'], extracted_data['content'], extracted_data["restricted"]

                    if restricted:
                        restricted_urls.append(url)
                    else:
                        data_frm_the_web.append({
                            "source_url": url,
                            "title": title,
                            "content": content
                        })

            
            with st.spinner("Processsing collected data and Generating Response..."):
                chunk_and_vectorize(data_frm_the_web)
                context = retrieve_top_chunks(user_input)
                reset_metadata_and_index()

                with st.expander("URLs scraped.."):
                    st.write(urls)

                with st.expander("Relevant Context Retrieved.."):
                    st.write(context)

                user_prompt = f"""Possibly Relevant URLs that could not be scraped (if any):
------------------------------
{restricted_urls}

Context from Scraped URLS:
------------------------------
{context}

Based on the context provided above, summarize the solution in 1-3 sentences. Always provide source links AS-IS. Incase context contains YouTube Video content with embedded timestamps, also provide the exact timestamp (e.g., 3:45 - 5:10) where the youtuber explains the solution and what it is.

If the provided context does not contain enough information to answer the question, clearly state that and provide the user possible Relevant URLs that could not be scraped to check manually. Ensure the answer is nicely structured and presented for ease of reading and understanding.

Question: 
------------------------------
{user_input}"""

                # Generate a response using the context
                response_message = get_response(
                    [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )

                st.markdown(response_message.content)
                st.session_state.messages.append({"role": "assistant", "content": response_message.content})

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
