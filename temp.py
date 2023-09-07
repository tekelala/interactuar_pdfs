import streamlit as st
import requests
import json
from langchain.chat_models import ChatAnthropic
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from io import BytesIO
from pdfminer.high_level import extract_text


def send_message(prompts):
    api_url = "https://api.anthropic.com/v1/complete"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": st.secrets["API_KEY"]
    }

    conversation = "\n\n".join([f'{item["role"]}: {item["content"]}: {item["defaultprompt"]}' for item in prompts]) + "\n\nAssistant:"
    body = {
        "prompt": conversation,
        "model": "claude-2.0",
        "max_tokens_to_sample": 100000,
        "temperature": 0,
        "stop_sequences": ["\n\nHuman:"]
    }

    # Error handling has been retained from the original code
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

    result = response.json()
    return result['completion'].strip()


st.title("Interactua con tu PDF")
st.write("¡No te quedes con la duda!")

uploaded_file = st.file_uploader("Upload a PDF", type=['pdf'])

if uploaded_file:
    with BytesIO(uploaded_file.getvalue()) as f:
        context = extract_text(f)
        st.session_state.context = context

if "prompts" not in st.session_state:
    st.session_state.prompts = []

if "new_message" not in st.session_state:
    st.session_state.new_message = False

for prompt in st.session_state.prompts:
    if prompt['role'] == "Human":
        with st.chat_message("Human", avatar="🧑‍💻"):
            st.write(prompt['content'])
    else:  # role == "Assistant"
        with st.chat_message(name="CoCreaBot", avatar="🤖"):
            st.write(prompt['content'])


if not st.session_state.new_message and 'context' in st.session_state:
    user_message = st.chat_input("Say something")
    if user_message:
        prompt_cocrea = f'''Perform the following tasks: 
                        Task 1: read and understand the uploaded document, here is the info: {st.session_state.context}
                        Task 2: answer the user's question based on the info you just ingested. This is the question: {user_message}
                        '''
        st.session_state.new_message = True
        st.session_state.prompts = [{"role": "Human", "content": user_message, "defaultprompt": prompt_cocrea}]  # Resetting prompts
        with st.spinner(text='Pensando...'):
            response_from_claude = send_message(st.session_state.prompts)
            st.session_state.prompts.append({"role": "Assistant", "content": response_from_claude, "defaultprompt": prompt_cocrea})
            st.session_state.new_message = False
            st.experimental_rerun()


if st.button('Restart'):
    st.session_state.prompts = []
    st.session_state.new_message = False
    st.experimental_rerun()
