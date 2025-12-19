# Backend API Documentation

**Base URL**: `http://localhost:8000/api/v1`

## 1. Authentication

All endpoints (except `/auth/login` and `/auth/signup`) require a **Bearer Token**.

### Login
**POST** `/auth/token`
- **Content-Type**: `application/x-www-form-urlencoded`
- **Fields**:
  - `username`: Email address (e.g., `user@example.com`)
  - `password`: Secret password
- **Response**:
  ```json
  {
    "access_token": "eyJhb...",
    "token_type": "bearer"
  }
  ```
> **Frontend Note**: Store this token and send it in the header `Authorization: Bearer <token>` for all other requests.

---

## 2. Conversations

### Create Conversation
**POST** `/conversations/`
- **Description**: Starts a new chat session.
- **Request**: Empty body `{}`
- **Response**:
  ```json
  { "convo_id": "550e8400-e29b-..." }
  ```

### List Conversations
**GET** `/conversations/`
- **Description**: Returns a list of all conversation IDs owned by the user.
- **Response**:
  ```json
  { "conversations": ["550e8400...", "a1b2c3d4..."] }
  ```

### Get History
**GET** `/conversations/{convo_id}/history`
- **Description**: Fetches the chat log for valid context.
- **Response**:
  ```json
  {
    "history": [
      { "role": "user", "content": "Hello", "timestamp": "2023-..." },
      { "role": "assistant", "content": "Hi there!", "timestamp": "2023-..." }
    ]
  }
  ```

---

## 3. Chat (RAG)

### Ask Question
**POST** `/conversations/{convo_id}/ask`
- **Description**: Main interaction endpoint. Uses Hybrid Retrieval (Global + Conversation Docs).
- **Request Body**:
  ```json
  {
    "message": "What does the ISO standard say about leadership?",
    "settings": {
      "model": "llama-3.3-70b-versatile",
      "temperature": 0.2
    }
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The standard requires top management to...",
    "citations": [
      {
        "source": "ISO_9001.pdf",
        "doc": "excerpt text...",
        "chunk_id": "global_iso_0"
      },
      {
        "source": "my_notes.txt",
        "doc": "local notes...",
        "chunk_id": "convo_notes_1"
      }
    ]
  }
  ```

---

## 4. Document Management

### Upload to Conversation (Private)
**POST** `/conversations/{convo_id}/documents`
- **Description**: Uploads a file accessible **only** in this conversation.
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (Binary)
- **Response**: `{"status": "ok", "chunks_added": 12}`

### Upload to Global Knowledge Base (Public)
**POST** `/conversations/documents/global`
- **Description**: Uploads a file accessible to **ALL** users.
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file` (Binary)
- **Response**: `{"status": "ok", "chunks_added": 50}`

### List Conversation Documents
**GET** `/conversations/{convo_id}/documents`
- **Response**:
  ```json
  { "documents": ["notes.txt", "invoice.pdf"] }
  ```

### List Global Documents
**GET** `/conversations/documents/global`
- **Response**:
  ```json
  { "documents": ["ISO_9001_2015.pdf", "Company_Policy.pdf"] }
  ```

### Delete Document
**DELETE** `/conversations/{convo_id}/documents/{filename}`
- **Description**: Permanently removes a document and its vectors from the conversation.
- **Path Param**: `filename` (e.g., `notes.txt`)
- **Response**: `{"status": "deleted", "file": "notes.txt"}`
