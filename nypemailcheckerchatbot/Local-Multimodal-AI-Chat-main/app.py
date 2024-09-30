import streamlit as st
from chat_api_handler import ChatAPIHandler
from utils import get_timestamp, load_config, get_avatar
from docs_handler import add_documents_to_db 
from html_templates import css
from database_operations import save_text_message, load_messages, get_all_chat_history_ids, delete_chat_history, load_last_k_text_messages_ollama, init_db
from utils import list_openai_models, list_ollama_models, command
init_db()
import sqlite3

config = load_config()

def toggle_pdf_chat():
    st.session_state.pdf_chat = True
    clear_cache()

def toggle_docx_chat():
    st.session_state.docx_chat = True
    clear_cache()

def toggle_xlsx_chat():
    st.session_state.xlsx_chat = True
    clear_cache()

def toggle_pptx_chat():
    st.session_state.pptx_chat = True
    clear_cache()

def detoggle_file_chat():
    st.session_state.pdf_chat = False
    st.session_state.docx_chat = False
    st.session_state.xlsx_chat = False
    st.session_state.pptx_chat = False

def get_session_key():
    if st.session_state.session_key == "new_session":
        st.session_state.new_session_key = get_timestamp()
        return st.session_state.new_session_key
    return st.session_state.session_key

def delete_chat_session_history():
    delete_chat_history(st.session_state.session_key)
    st.session_state.session_index_tracker = "new_session"

def clear_cache():
    st.cache_resource.clear()

def list_model_options():
    if st.session_state.endpoint_to_use == "ollama":
        ollama_options = list_ollama_models()
        if ollama_options == []:
            st.warning("No Ollama models available, please choose one from https://ollama.com/library and pull with /pull <model_name>")
        return ollama_options
    elif st.session_state.endpoint_to_use == "openai":
        return list_openai_models()

def update_model_options():
    st.session_state.model_options = list_model_options()

### Main Streamlit App ###
def main():
    st.title("NYP Email Checker Chatbot")
    st.write(css, unsafe_allow_html=True)
    
    if "db_conn" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.new_session_key = None
        st.session_state.session_index_tracker = "new_session"
        st.session_state.db_conn = sqlite3.connect(config["chat_sessions_database_path"], check_same_thread=False)
        st.session_state.endpoint_to_use = "ollama"
        st.session_state.model_options = list_model_options()
        st.session_state.model_tracker = None

    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None

    st.sidebar.title("Chat Sessions")
    chat_sessions = ["new_session"] + get_all_chat_history_ids()
    try:
        index = chat_sessions.index(st.session_state.session_index_tracker)
    except ValueError:
        st.session_state.session_index_tracker = "new_session"
        index = chat_sessions.index(st.session_state.session_index_tracker)
        clear_cache()

    st.sidebar.selectbox("Select a chat session", chat_sessions, key="session_key", index=index)
    
    api_col, model_col = st.sidebar.columns(2)
    api_col.selectbox(label="Select an API", options=["ollama", "openai"], key="endpoint_to_use", on_change=update_model_options)
    model_col.selectbox(label="Select a Model", options=st.session_state.model_options, key="model_to_use")
    
    # File uploaders for different file types with unique keys
    uploaded_pdf = st.sidebar.file_uploader("Upload a PDF file", accept_multiple_files=True, key="pdf_uploader", type=["pdf"], on_change=toggle_pdf_chat)
    uploaded_docx = st.sidebar.file_uploader("Upload a DOCX file", accept_multiple_files=True, key="docx_uploader", type=["docx"], on_change=toggle_docx_chat)
    uploaded_xlsx = st.sidebar.file_uploader("Upload an XLSX file", accept_multiple_files=True, key="xlsx_uploader", type=["xlsx"], on_change=toggle_xlsx_chat)
    uploaded_pptx = st.sidebar.file_uploader("Upload a PPTX file", accept_multiple_files=True, key="pptx_uploader", type=["pptx"], on_change=toggle_pptx_chat)

    # Processing uploaded files
    if uploaded_pdf:
        with st.spinner("Processing PDF..."):
            add_documents_to_db(uploaded_pdf, "pdf")  # Add file type argument

    if uploaded_docx:
        with st.spinner("Processing DOCX..."):
            add_documents_to_db(uploaded_docx, "docx")

    if uploaded_xlsx:
        with st.spinner("Processing XLSX..."):
            add_documents_to_db(uploaded_xlsx, "xlsx")

    if uploaded_pptx:
        with st.spinner("Processing PPTX..."):
            add_documents_to_db(uploaded_pptx, "pptx")

    # Handling user inputs
    user_input = st.chat_input("Type your message here", key="user_input")

    if user_input:
        if user_input.startswith("/"):
            response = command(user_input)
            save_text_message(get_session_key(), "user", user_input)
            save_text_message(get_session_key(), "assistant", response)
            user_input = None

        if user_input:
            llm_answer = ChatAPIHandler.chat(user_input=user_input, chat_history=load_last_k_text_messages_ollama(get_session_key(), config["chat_config"]["chat_memory_length"]))
            save_text_message(get_session_key(), "user", user_input)
            save_text_message(get_session_key(), "assistant", llm_answer)
            user_input = None

    # Display chat history
    if st.session_state.session_key != "new_session" or st.session_state.new_session_key is not None:
        chat_container = st.container()
        with chat_container:
            chat_history_messages = load_messages(get_session_key())

            for message in chat_history_messages:
                with st.chat_message(name=message["sender_type"]):
                    if message["message_type"] == "text":
                        st.write(message["content"])

        if st.session_state.session_key == "new_session" and st.session_state.new_session_key is not None:
            st.rerun()

if __name__ == "__main__":
    main()
