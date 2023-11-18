# Importing required packages
import streamlit as st
import openai
import uuid
import time
import pandas as pd
import io
import re
import base64
from openai import OpenAI
import mimetypes


# Initialize OpenAI client
client = OpenAI()

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "assistant_id" not in st.session_state:
    assistant = client.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])

if "messages" not in st.session_state:
    messages = {}
    
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id
else:
    thread = client.beta.threads.retrieve(st.session_state["thread_id"])


def render_responses(threadid,prompt):
    messages = client.beta.threads.messages.list(threadid)
    # if prompt:
    #     messages.data.append({"content": [{"text": {"value": prompt}}]})
    return messages

def get_response(prompt: str):
    message = client.beta.threads.messages.create(
        thread.id, role="user", content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    with st.spinner("Running assistant..."):
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            st.toast(f"Run status: {run.status}")
            time.sleep(1)
    
    # messages = render_responses(thread.id, prompt)
    messages = client.beta.threads.messages.list(thread.id)

    return messages


prompt = st.chat_input("Say something to the bot (nice) 2f  - fff")
 
if prompt:
    messages = get_response(prompt)
    for m in reversed(messages.data):
        st.write(m.content[0].text.value)

