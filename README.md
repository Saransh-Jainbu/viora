<!-- 
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload
-->
# Viora

Viora is an AI-powered document intelligence platform that allows users to upload documents and interact with them through natural language queries. It combines modern web technologies with LLMs and vector search to deliver contextual, accurate responses.

---

## Features

- Upload and process documents  
- Semantic search using vector embeddings (ChromaDB)  
- AI-powered responses using LLMs (OpenAI / Ollama)  
- Secure authentication with Firebase  
- Real-time chat interface  
- Context-aware responses (no hallucination design)  

---

## Tech Stack

### Frontend
- Next.js
- Tailwind CSS
- TypeScript

### Backend
- FastAPI
- Firebase Admin SDK (Auth)
- ChromaDB (Vector DB)
- OpenAI / Ollama (LLMs)

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/viora.git
cd viora
```

### 2. Frontend Setup
```bash
npm install
```

### 3. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a .env file inside the /backend folder:
```bash
OPENAI_API_KEY=your_openai_api_key
OLLAMA_BASE_URL=http://localhost:11434

# Firebase Admin
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-client-email
```

## Run backend server

```bash
# In backend folder
uvicorn main:app --reload
```

## Run frontend

```bash
npm run dev
```


