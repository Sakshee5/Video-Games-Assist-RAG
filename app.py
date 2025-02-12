from openai_utils import get_response

import streamlit as st

with st.sidebar:
    st.header("🎮 Game Assistant Guide")
    
    st.write(
        "Welcome to the Open-World Game Assistant! This tool helps you find quick answers for open-world games by retrieving data from YouTube, forums, and guides."
    )

    st.subheader("⚡ How It Works")
    st.write(
        "- **Ask any question** related to open-world games.\n"
        "- The assistant searches for **relevant gameplay info**.\n"
        "- If available, it provides **exact video timestamps** or summarizes key solutions.\n"
        "- Sources include **YouTube, web sources, forums, and guides**."
    )

    st.subheader("🎯 Example Questions")
    st.write(
        "- *Where do I find the best armor in Elden Ring?*\n"
        "- *How do I solve the temple puzzle in Zelda TOTK?*\n"
        "- *Fastest way to level up in Skyrim?*"
    )

    st.info("Try asking a question in the chat!")

st.header("🎮 Open-World Game Assist")


sys_prompt = """
You are an expert Video Game Assistant specializing in open-world games. 
You provide dynamic, real-time help by retrieving relevant information from YouTube, forums, and discussion threads.

How to Respond:
1. YouTube Video Answers
   - If a solution is available in a YouTube video, provide the **exact timestamp range** (e.g., 3:45 - 5:10) so the user can watch it directly.  
   - Also include a short summary in text of the solution. The user can either use this directly or watch the video incase things arent clear.

2. Forum & Discussion Insights 
   - If the context comes from gaming forums or discussions, extract key information and provide the user with a structured, succinct response.  
   - Ensure to include the source link for reference.

3. Unavailable Sources (list will be provided) - Use only when above resources are not sufficient to answer the user query.
   - If some sources could not be accessed** (e.g., due to website restrictions), list them for the user.  
   - Inform them that these sources might be useful, but scraping was not possible due to anti-scraping laws.

If the provided context **does not** contain enough information to answer the question, clearly state that and suggest checking the external sources.
"""


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": sys_prompt}]


# Display chat messages from session state
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.text(message["content"])

# User input
if user_input := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.text(f"{user_input}")

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching the Web for relevant sources..."):
                data_frm_the_web = "" # will add logic to get context later
            
            with st.spinner("Processsing collected data and Generating Response..."):
                context = "" # will add logic to get context later

                # Generate a response using the context
                response_message = get_response(
                    [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": f"Context: {context}\n\nQuestion: {user_input}"},
                    ]
                )

                st.text(response_message.content)
                st.session_state.messages.append({"role": "assistant", "content": response_message.content})

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
