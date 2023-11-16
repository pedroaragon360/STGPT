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


if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state["thread_id"] = thread.id
else:
    thread = client.beta.threads.retrieve(st.session_state["thread_id"])


def ts_to_str(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def gen_file_name(f):
    return f"{f.filename} ({ts_to_str(f.created_at)}: {f.id})"


select_file_tab, upload_file_tab = st.columns(2)

with select_file_tab:
    uploaded_files = client.files.list(purpose="assistants")
    selected_files = st.multiselect(
        "Select uploaded files", [gen_file_name(f) for f in uploaded_files]
    )

with upload_file_tab:
    uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "docx", "md"])
    if uploaded_file is not None:
        st.info("File uploaded successfully, now parsing...")
        file = client.files.create(file=uploaded_file, purpose="assistants")
        st.info(
            f"File parsed successfully, file id is {file.id}. now creating assistant..."
        )


if not uploaded_file and not selected_files:
    st.error("Please upload a file or select a file to continue")
    st.stop()
file_ids = [f.id for f in uploaded_files if gen_file_name(f) in selected_files]
if uploaded_file:
    file_ids.append(file.id)
print(selected_files, file_ids)


def get_response(prompt: str):
    client.beta.assistants.update(
        assistant_id=assistant.id,
        file_ids=file_ids,
    )
    message = client.beta.threads.messages.create(
        thread.id, role="user", content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Please address the user as Jane Doe. The user has a premium account.",
    )

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
