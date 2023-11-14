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
st.sidebar.image("https://thevalley.es/lms/i/logow.png")
st.sidebar.divider()
#st.sidebar.markdown("Por Pedro Aragón", unsafe_allow_html=True)
st.sidebar.markdown("Analiza un archivo de datos:")

# Initialize session state for the uploader key
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# File uploader for CSV, XLS, XLSX
uploaded_file = st.sidebar.file_uploader("", type=["csv", "xls", "json"], key=f'file_uploader_{st.session_state.uploader_key}')

if uploaded_file is not None:
    # Determine the file type
    file_type = uploaded_file.type

    try:
        file_stream = uploaded_file.getvalue()
        file_response = client.files.create(file=file_stream, purpose='assistants')
        st.session_state.file_id = file_response.id
        st.session_state.file_name = uploaded_file.name

        st.sidebar.success(f"Archivo subido. File ID: {file_response.id}")
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Default for unknown types
    
        # Create download button
        st.sidebar.download_button(
            label="Descargar fichero subido",
            data=file_stream,
            file_name=uploaded_file.name,
            mime=mime_type
        )

        # Reset the uploader by changing the key
        st.session_state.uploader_key += 1
       
    except Exception as e:
        st.error(f"An error occurred: {e}")
        
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
            with st.chat_message(message.role):

                for content_part in message.content:
                    # Handle text content
                    if hasattr(content_part, 'text') and content_part.text:
                        message_text = content_part.text.value
                        pattern = r'\[.*?\]\(sandbox:.*?\)'
                        message_text = re.sub(pattern, '', message_text)
                        st.markdown(message_text)
                        #st.write("Msg:", message)

                        # Check for and display image from annotations
                        if content_part.text.annotations:
                            for annotation in content_part.text.annotations:
                                if hasattr(annotation, 'file_path') and annotation.file_path:
                                    file_id = annotation.file_path.file_id
                                    # Retrieve the image content using the file ID
                                    file_name = client.files.retrieve(file_id).filename #eg. /mnt/data/archivo.json
                                    response = client.files.with_raw_response.retrieve_content(file_id)
                                    if response.status_code == 200:
                                        b64_image = base64.b64encode(response.content).decode()
                                    
                                        # Guess the MIME type of the file based on its extension
                                        mime_type, _ = mimetypes.guess_type(file_name)
                                        if mime_type is None:
                                            mime_type = "application/octet-stream"  # Default for unknown types
                                    
                                        # Extract just the filename from the path
                                        filename = file_name.split('/')[-1]
                                    
                                        # Create a download button with the correct MIME type and filename
                                        href = f'<a style="border: 1px solid white;background: white; color: black; padding: 0.4em 0.8em; border-radius: 1em;" href="data:{mime_type};base64,{b64_image}" download="{filename}">Descargar {filename}</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                    else:
                                        st.error("Failed to retrieve file")
                                    
                    # Handle direct image content
                    if hasattr(content_part, 'image') and content_part.image:
                        image_url = content_part.image.url
                        st.write("IMG API Response:", content_part.image)
                # Check for image file and retrieve the file ID
                    if hasattr(content_part, 'image_file') and content_part.image_file:
                        image_file_id = content_part.image_file.file_id
                        # Retrieve the image content using the file ID
                        response = client.files.with_raw_response.retrieve_content(image_file_id)
                        if response.status_code == 200:
                            st.image(response.content)
                        else:
                            st.error("Failed to retrieve image")

# Chat input and message creation with file ID
if prompt := st.chat_input("How can I help you?"):

    if "file_id" in st.session_state and "file_name" in st.session_state:
        prompt = "Renombra el archivo " + str(st.session_state.file_id) + " por " + str(st.session_state.file_name) + ". " + prompt
    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }
    with st.chat_message('user'):
        st.write(prompt)
        
    # Include file ID in the request if available
    if "file_id" in st.session_state:
        message_data["file_ids"] = [st.session_state.file_id]
        st.session_state.pop('file_id')
    
    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )

    if st.session_state.retry_error < 3:
        time.sleep(1)
        st.rerun()

# Handle run status
# Handle run status
if hasattr(st.session_state.run, 'status'):
    
    # Show a loading spinner while processing
    if st.session_state.retry_error < 3:
        st.session_state.retry_error += 1
        st.experimental_rerun()
    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if st.session_state.retry_error < 3:
                st.write("Run failed, retrying ......")
                st.experimental_rerun()
            else:
                st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")
    elif st.session_state.run.status != "completed":
        with st.spinner(text='In progress'):
            st.session_state.run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread.id,
                run_id=st.session_state.run.id,
            )
            if st.session_state.retry_error < 3:
                st.experimental_rerun()


