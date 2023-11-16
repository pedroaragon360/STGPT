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
    st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
    st.session_state.thread = client.beta.threads.create(
        metadata={'session_id': st.session_state.session_id}
    )

# Display chat messages
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":

    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with tab1:
                with st.chat_message(message.role):
                    for content_part in message.content:                                    
                    #if steps.tools[0].type == 'code_interpreter':
                        # Handle text content
                        if hasattr(content_part, 'text') and content_part.text:
                            message_text = content_part.text.value
                            st.markdown(message_text)

# Chat input and message creation with file ID
if prompt := st.chat_input("How can I help you?"):
    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }
    with tab1:
        with st.chat_message('user'):
            st.markdown(prompt)
        
    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    #st.write('<img src="https://thevalley.es/lms/i/load.gif" height="28px"> Pensando...' if st.session_state.run.status == 'queued' else '', unsafe_allow_html=True)

