# ISO 9001 RAG Chatbot

A conversation-based RAG (Retrieval Augmented Generation) chatbot for ISO 9001 compliance, featuring Per-Conversation scoped documents and User Authentication.

## Features
- **RAG**: Queries ISO 9001 documents + user uploaded files.
- **Conversational**: Maintains history per session (stored in SQLite).
- **Isolation**: Uploaded documents are private to the conversation.
- **Security**: JWT Authentication (Signup/Login) for all endpoints.

## Installation

1. **Prerequisites**: Python 3.10+ installed.
2. **Environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. **Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Environment Variables**:
   *   The Groq API key is currently configured in `app/api/conversations.py`.
   *   Secrets for JWT are in `app/auth.py`.

## Data Ingestion (Global Knowledge)

Before running the app, ingest the base ISO documents:
```powershell
python -m app.ingestion
```

## Running the Server

```powershell
python run.py
```
The API will start at `http://127.0.0.1:8000`.

## Testing the API (Authentication Required)

All conversation endpoints are protected. You must authenticate first.

### 1. Signup
**POST** `http://127.0.0.1:8000/api/v1/auth/signup`
```json
{
    "email": "user@example.com",
    "password": "securePass123"
}
```

### 2. Login (Get Token)
**POST** `http://127.0.0.1:8000/api/v1/auth/token`
*   Form Data: `username=user@example.com`, `password=securePass123`
*   **Response**: `{"access_token": "ey...", ...}`

### 3. Use the Chatbot
Add the header `Authorization: Bearer <your_access_token>` to all requests.

*   **Create Conversation**: `POST /api/v1/conversations/`
*   **Ask Question**: `POST /api/v1/conversations/{id}/ask`
    ```json
    { "message": "What is the scope of ISO 9001?" }
    ```
*   **Upload Document**: `POST /api/v1/conversations/{id}/documents`

For full API documentation, see `api_docs.md`.