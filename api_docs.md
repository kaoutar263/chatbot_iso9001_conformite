# ISO 9001 Chatbot API Documentation

**Base URL (Auth)**: `http://127.0.0.1:8000/api/v1/auth`
**Base URL (Conversations)**: `http://127.0.0.1:8000/api/v1/conversations`

## Authentication

All endpoints (except Signup/Login) require a JWT Bearer Token.

**POST** `/auth/signup`
*   Create a new account.
*   Body: `{"email": "user@example.com", "password": "password123"}`

**POST** `/auth/token`
*   Login to get an access token.
*   **Important**: This endpoint requires **Form Data**, not JSON.
*   **Postman Setup**:
    1.  Go to **Body** tab.
    2.  Select **`x-www-form-urlencoded`**.
    3.  **Key**: `username` (MUST be exactly "username"), **Value**: `user@example.com`
    4.  **Key**: `password`, **Value**: `password123`
*   Response: `{"access_token": "...", "token_type": "bearer"}`

**Using the Token:**
Add header `Authorization: Bearer <your_token>` to all subsequent requests.

## Core Endpoint: Ask Question (RAG)

**POST** `/{convo_id}/ask`

This is the main endpoint used to interact with the chatbot. It performs the vector search and LLM generation.

### Request Body (`application/json`)
```json
{
  "message": "What are the requirements for leadership?",
  "settings": {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.2
  }
}
```
*   `message` (required): The user's question.
*   `settings` (optional): Configuration object. Can be omitted.
    *   `model`: Generic name of LLM model. Defaults to `llama-3.3-70b-versatile`.

### Response Body (`application/json`)
```json
{
  "answer": "Title 5.1 Leadership and commitment states that...",
  "citations": [
    {
      "source": "ISO_9001_V_2015.pdf",
      "doc": "Top management shall demonstrate leadership...",
      "chunk_id": "ISO_9001_V_2015_42"
    }
  ]
}
```

---

## Conversation Management

**POST** `/`
*   Creates a new conversation session.
*   **Response**: `{"convo_id": "uuid..."}`

**GET** `/`
*   Lists active conversation IDs.
*   **Response**: `{"conversations": ["uuid-1", ...]}`

**GET** `/{convo_id}/history`
*   *Implementation Pending (Redis)*
*   Returns the chat history for a session.

---

## Document Management

### Upload Document (Private Knowledge Base)

**POST** `/{convo_id}/documents`

Uploads a PDF to be used *only* within this specific conversation context.

**Postman Setup:**
1.  **Method**: `POST`
2.  **URL**: `http://127.0.0.1:8000/api/v1/conversations/{id}/documents`
3.  **Body Tab**: Select `form-data`.
4.  **Key**: `file` (Change generic type "Text" to "File" on the right side of the key field).
5.  **Value**: Select your `.pdf` file.

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/conversations/{id}/documents" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

**Response**:
```json
{
  "status": "ok",
  "chunks_added": 15
}
```

### List Documents

**GET** `/{convo_id}/documents`
*   Lists documents attached to a conversation.

**DELETE** `/{convo_id}/documents/{doc_id}`
*   Removes a document.
