from utils import load_config
import streamlit as st
import sqlite3

config = load_config()

# Database connection and cursor management
def get_db_connection():
    return st.session_state.db_conn

def get_db_cursor(db_connection):
    return db_connection.cursor()

def get_db_connection_and_cursor():
    conn = get_db_connection()
    return conn, conn.cursor()

def close_db_connection():
    if 'db_conn' in st.session_state and st.session_state.db_conn is not None:
        st.session_state.db_conn.close()
        st.session_state.db_conn = None

# Functions for saving and loading chat messages
def save_text_message(chat_history_id, sender_type, text):
    conn, cursor = get_db_connection_and_cursor()

    cursor.execute('INSERT INTO messages (chat_history_id, sender_type, message_type, text_content) VALUES (?, ?, ?, ?)',
                   (chat_history_id, sender_type, 'text', text))

    conn.commit()

def load_messages(chat_history_id):
    conn, cursor = get_db_connection_and_cursor()

    query = "SELECT message_id, sender_type, message_type, text_content FROM messages WHERE chat_history_id = ?"
    cursor.execute(query, (chat_history_id,))

    messages = cursor.fetchall()
    chat_history = []
    for message in messages:
        message_id, sender_type, message_type, text_content = message
        chat_history.append({'message_id': message_id, 'sender_type': sender_type, 'message_type': message_type, 'content': text_content})

    return chat_history

def load_last_k_text_messages(chat_history_id, k):
    conn, cursor = get_db_connection_and_cursor()

    query = """
    SELECT message_id, sender_type, message_type, text_content
    FROM messages
    WHERE chat_history_id = ? AND message_type = 'text'
    ORDER BY message_id DESC
    LIMIT ?
    """
    cursor.execute(query, (chat_history_id, k))

    messages = cursor.fetchall()
    chat_history = []
    for message in reversed(messages):  # Reverse the order to get chronological messages
        message_id, sender_type, message_type, text_content = message
        chat_history.append({
            'message_id': message_id,
            'sender_type': sender_type,
            'message_type': message_type,
            'content': text_content
        })

    return chat_history

# Retrieve all chat history IDs
def get_all_chat_history_ids():
    conn, cursor = get_db_connection_and_cursor()

    query = "SELECT DISTINCT chat_history_id FROM messages ORDER BY chat_history_id ASC"
    cursor.execute(query)

    chat_history_ids = cursor.fetchall()
    chat_history_id_list = [item[0] for item in chat_history_ids]

    return chat_history_id_list

# Delete chat history based on chat_history_id
def delete_chat_history(chat_history_id):
    conn, cursor = get_db_connection_and_cursor()

    query = "DELETE FROM messages WHERE chat_history_id = ?"
    cursor.execute(query, (chat_history_id,))
    conn.commit()

    print(f"All entries with chat_history_id {chat_history_id} have been deleted.")

# Database initialization
def init_db():
    db_path = config["chat_sessions_database_path"]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Creating the `messages` table if it doesn't already exist
    create_messages_table = """
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_history_id TEXT NOT NULL,
        sender_type TEXT NOT NULL,
        message_type TEXT NOT NULL,
        text_content TEXT
    );
    """
    
    cursor.execute(create_messages_table)
    conn.commit()
    conn.close()

# Load last k text messages for the Ollama model
def load_last_k_text_messages_ollama(chat_history_id, k):
    conn, cursor = get_db_connection_and_cursor()

    query = """
    SELECT message_id, sender_type, message_type, text_content
    FROM messages
    WHERE chat_history_id = ? AND message_type = 'text'
    ORDER BY message_id DESC
    LIMIT ?
    """
    cursor.execute(query, (chat_history_id, k))

    messages = cursor.fetchall()
    chat_history = []
    for message in reversed(messages):  # Reverse the order to get chronological messages
        message_id, sender_type, message_type, text_content = message
        chat_history.append({
            'role': sender_type,
            'content': text_content
        })

    return chat_history

if __name__ == "__main__":
    init_db()
