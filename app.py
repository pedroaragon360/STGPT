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

# Your chosen model
MODEL = "gpt-4-1106-preview"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

# Set up the page
st.set_page_config(page_title="Asistente")

st.markdown('<div id="logoth" style="z-index: 9999999; background: url(https://thevalley.es/lms/i/logow.png);  width: 200px;  height: 27px;  position: fixed;  background-repeat: no-repeat;  background-size: auto 100%;  top: 1.1em;  left: 1em;"></div>', unsafe_allow_html=True)

#st.sidebar.markdown("Por Pedro Aragón", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Conversación", "Sube un fichero"])

st.markdown('<style>[data-baseweb=tab-list] {   position: fixed !important; top: 0.5em;   left: 11em;   z-index: 9999999; } [data-testid=stToolbar]{ top:-10em } </style>', unsafe_allow_html=True)

# Initialize session state for the uploader key
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

with tab1:
    with st.chat_message('assistant'):
        st.write('¡Hola! Soy el asistente GPT de The Valley, ¿cómo te puedo ayudar?')

# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
    st.session_state.assistant = assistant

st.write(assistant)

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
else:
    thread = client.beta.threads.retrieve(st.session_state["thread_id"])
st.write(thread)

def get_response(prompt: str):
    message = client.beta.threads.messages.create(
        thread.id, role="user", content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id
    )
    st.write(run)

    with st.spinner("Running assistant..."):
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            st.toast(f"Run status: {run.status}", icon="hourglass")
            time.sleep(1)

    messages = client.beta.threads.messages.list(thread.id)
    return messages


prompt = st.chat_input("Say something to the bot")

if prompt:
    messages = get_response(prompt)
    for m in messages.data:
        print(m)
    st.write(messages.data[0].content[0].text.value)

