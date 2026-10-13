# mobile-software-project
# 🎙️ Voice Assistant (RAG + PWA)

A voice-based assistant that listens to your question, finds the answer in your own documents, and speaks the reply back.

**Flow:** Mic → Whisper (speech-to-text) → FAISS retrieval → LLM → KittenTTS (text-to-speech) → Audio reply

---

## ✨ Features

- Push-to-talk voice input from the browser
- Speech-to-text with Whisper (`faster-whisper`)
- Retrieval-Augmented Generation over your own `.txt` documents
- Works with any OpenAI-compatible LLM (OpenAI, Ollama, etc.)
- Lightweight text-to-speech with KittenTTS
- Installable Progressive Web App (PWA)

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite), PWA |
| Backend | Django, Django REST Framework |
| STT | faster-whisper |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector DB | FAISS |
| LLM | OpenAI-compatible API |
| TTS | KittenTTS |

---

## 📁 Project Structure

```
voice-assistant/
├── frontend/              # React PWA
│   ├── public/            # manifest.json, service-worker.js, icons/
│   └── src/
│       ├── components/    # MicButton, TranscriptBox, AudioPlayer
│       ├── hooks/         # useRecorder.js
│       ├── services/      # api.js
│       └── App.jsx
├── backend/               # Django project
│   ├── config/            # settings, urls, wsgi
│   ├── voice/             # API view + STT/TTS services
│   ├── rag/               # ingest, embeddings, retriever, llm, pipeline
│   └── data/
│       ├── documents/     # your source .txt files
│       └── vector_store/  # generated FAISS index
├── .env
└── README.md
```

---

## ✅ Prerequisites

- Python 3.10+
- Node.js 18+
- Git
- ffmpeg and espeak-ng

```bash
# Ubuntu / Debian
sudo apt install ffmpeg espeak-ng

# macOS
brew install ffmpeg espeak-ng

# Windows: install ffmpeg and espeak-ng manually and add them to PATH
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/voice-assistant.git
cd voice-assistant
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment variables

Create a `.env` file in the project root:

```env
LLM_API_KEY=your_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
WHISPER_MODEL=base
```

Using a local LLM with Ollama instead:

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
WHISPER_MODEL=base
```

### 4. Add your documents and build the index

Put `.txt` files in `backend/data/documents/`, then run:

```bash
python manage.py shell -c "from rag.ingest import run; run()"
```

Re-run this command whenever you add or change documents.

### 5. Frontend setup

```bash
cd ../frontend
npm install
```

---

## ▶️ Running the App

**Terminal 1: Backend**

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2: Frontend**

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**, allow microphone access, and tap the mic button.

> Microphone access only works on `localhost` or over HTTPS.

---

## 🔌 API

### `POST /api/voice/`

Send recorded audio and receive the transcript, answer, and spoken reply.

**Request:** `multipart/form-data` with an `audio` file (webm)

```bash
curl -X POST -F "audio=@test.webm" http://127.0.0.1:8000/api/voice/
```

**Response:**

```json
{
  "transcript": "What is your refund policy?",
  "answer": "Refunds are available within 30 days of purchase.",
  "audio_url": "http://127.0.0.1:8000/media/abc123.wav"
}
```

---

## 📱 Installing as a PWA

1. Build and serve the frontend:
```bash
   cd frontend
   npm run build
   npm run preview
```
2. To test on a phone, expose both apps over HTTPS (for example `ngrok http 5173`) and update `API_URL` in `frontend/src/services/api.js`.
3. Use your browser's "Install app" / "Add to Home Screen" option.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| Mic not working | Use `localhost` or HTTPS and allow browser permission |
| `ffmpeg not found` | Install ffmpeg and make sure it is on PATH |
| TTS errors | Install `espeak-ng` and reinstall KittenTTS from its GitHub README |
| "No such file: index.faiss" | Run the ingest command (Installation step 4) |
| CORS errors | Check `corsheaders` is installed and added to `MIDDLEWARE` |
| Empty or wrong answers | Add more relevant `.txt` content and re-run ingest |

---

## 🔒 Notes

- `CORS_ALLOW_ALL_ORIGINS = True` is for development only. Restrict origins in production.
- Never commit your `.env` file. Add it to `.gitignore`.

Suggested `.gitignore`:

```gitignore
.env
venv/
node_modules/
__pycache__/
backend/media/
backend/data/vector_store/
frontend/dist/
db.sqlite3
```

---

## 🗺️ Roadmap

- [ ] Support PDF and DOCX ingestion
- [ ] Streaming responses
- [ ] Conversation history
- [ ] Voice activity detection (auto stop)
- [ ] Deployment guide (Docker)

---

## 📄 License

MIT License. Free to use and modify.
