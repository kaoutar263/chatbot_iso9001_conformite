# How It Works: ISO 9001 RAG Chatbot

This document explains the architecture, data flow, and security mechanisms of the chatbot.

## 1. High-Level Architecture

The system is a **Retrieval-Augmented Generation (RAG)** application built with FastAPI. It combines vector search (ChromaDB) with a Large Language Model (Groq Llama 3) to answer questions based on ISO 9001 standards and user-uploaded documents.

```mermaid
graph TD
    User[User / React App] -->|HTTPS + JWT| API[FastAPI Server]
    API -->|Auth Check| DB[(SQLite: Users/Chat History)]
    API -->|Vector Search| Chroma[(ChromaDB: ISO Docs)]
    API -->|Context + Query| LLM[Groq API (Llama 3)]
    Chroma -->|Relevant Chunks| API
    LLM -->|Answer| API
    API -->|Response| User
```

## 2. Key Components

### A. Authentication & Security
*   **Method**: OAuth2 with Password Flow (Bearer Tokens).
*   **Encryption**: Passwords are hashed using `bcrypt` before storage.
*   **JWT**: Stateless authentication. The token contains the `user_id` and is required for all conversation endpoints.
*   **Isolation**: Every conversation and document is tagged with a `user_id` in SQLite and a `scope` in ChromaDB. User A cannot access User B's data.

### B. The RAG Pipeline
When you ask a question (`/ask`), the following happens:
1.  **Input Processing**: The API receives your question and the conversation ID.
2.  **Vector Search**: It queries ChromaDB for the top 3 most relevant text chunks.
    *   *Filter*: It specifically looks for chunks that are either **Global** (ISO 9001 Standard) or **Scoped** to your current conversation (your uploaded PDFs).
3.  **Memory retrieval**: It fetches the last 6 messages of history from SQLite to provide context (e.g., resolving "it" or "that").
4.  **Prompt Engineering**: A system prompt is constructed:
    > "You are an ISO expert. Answer based ONLY on this context: [Chunks]..."
5.  **Generation**: The prompt + history + question are sent to the Groq API (Llama-3.3-70b).
6.  **Response**: The answer and the source citations are returned to you.

### C. Database Schema (SQLite)
We use `chat.db` for relational data:
*   **Users**: `id` (UUID), `email`, `hashed_password`.
*   **Conversations**: `id`, `user_id` (FK), `created_at`.
*   **Messages**: `id`, `conversation_id` (FK), `role` (user/assistant), `content`, `timestamp`.

### D. Document Storage (ChromaDB)
We use a Vector Database to understand the *meaning* of text.
*   **Collection**: `iso_docs`
*   **Metadata**: Each chunk has `source` (filename) and `scope` (either "global" or the conversation UUID).

## 3. Project Structure

*   **`app/main.py`**: Entry point. Sets up the FastAPI app and routes.
*   **`app/api/auth.py`**: Handles Signup and Login.
*   **`app/api/conversations.py`**: The core logic. Handles RAG, uploads, and chat.
*   **`app/database.py`**: SQLite connection logic.
*   **`app/ingestion.py`**: Script to parse the base ISO 9001 PDF and load it into ChromaDB as "global" knowledge.
*   **`app/utils.py`**: Shared PDF text extraction logic.

## 4. Workflows

### Ingestion (Setup)
Run `python -m app.ingestion`. This reads `ISO_9001.pdf`, splits it into chunks, calculates vectors (embeddings), and saves them to `./data/chroma_db`.

### User Flow
1.  **Signup**: User creates account -> Saved to SQLite.
2.  **Login**: User sends credentials -> Receives JWT.
3.  **Chat**: User sends token + question -> Server validates token -> Runs RAG -> Returns answer.
