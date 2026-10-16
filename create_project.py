import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {}
KEEP_IF_EXISTS = {".env", "backend/data/documents/info.txt"}


def add(path, content):
    FILES[path] = content.lstrip("\n")


def png(size, rgb):
    raw = (b"\x00" + bytes(rgb) * size) * size

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


# ---------------------------------------------------------------- ROOT
add(".env", r'''
LLM_API_KEY=your_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
WHISPER_MODEL=base
''')

add(".gitignore", r'''
.env
venv/
node_modules/
__pycache__/
backend/media/
backend/data/vector_store/
frontend/dist/
db.sqlite3
''')

# ---------------------------------------------------------------- BACKEND CORE
add("backend/manage.py", r'''
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
''')

add("backend/config/__init__.py", "")

add("backend/config/settings.py", r'''
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "voice",
    "rag",
    "accounts",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True  # dev only

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATA_DIR = BASE_DIR / "data"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
''')

add("backend/config/urls.py", r'''
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("voice.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
''')

add("backend/config/wsgi.py", r'''
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
''')

add("backend/config/asgi.py", r'''
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()
''')

# ---------------------------------------------------------------- ACCOUNTS
add("backend/accounts/__init__.py", "")

add("backend/accounts/views.py", r'''
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or len(password) < 6:
        return Response(
            {"error": "Username required and password must be at least 6 characters"},
            status=400,
        )
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    user = authenticate(
        username=request.data.get("username", "").strip(),
        password=request.data.get("password", ""),
    )
    if not user:
        return Response({"error": "Invalid username or password"}, status=400)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["POST"])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response({"message": "Logged out"})
''')

add("backend/accounts/urls.py", r'''
from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register),
    path("login/", views.login),
    path("logout/", views.logout),
]
''')

# ---------------------------------------------------------------- VOICE
add("backend/voice/__init__.py", "")
add("backend/voice/services/__init__.py", "")

add("backend/voice/services/stt_service.py", r'''
import os

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            os.getenv("WHISPER_MODEL", "base"),
            device="cpu",
            compute_type="int8",
        )
    return _model


def transcribe(audio_path: str) -> str:
    segments, _ = _get_model().transcribe(audio_path)
    return " ".join(seg.text.strip() for seg in segments).strip()
''')

add("backend/voice/services/tts_service.py", r'''
import uuid

from django.conf import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from kittentts import KittenTTS
        _model = KittenTTS("KittenML/kitten-tts-nano-0.1")
    return _model


def synthesize(text: str) -> str:
    import soundfile as sf

    audio = _get_model().generate(text, voice="expr-voice-2-f")
    filename = f"{uuid.uuid4().hex}.wav"
    path = settings.MEDIA_ROOT / filename
    settings.MEDIA_ROOT.mkdir(exist_ok=True)
    sf.write(str(path), audio, 24000)
    return f"{settings.MEDIA_URL}{filename}"
''')

add("backend/voice/views.py", r'''
import os
import tempfile

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .services.stt_service import transcribe
from .services.tts_service import synthesize
from rag.pipeline import answer


@api_view(["POST"])
@parser_classes([MultiPartParser])
def voice_chat(request):
    audio = request.FILES.get("audio")
    if not audio:
        return Response({"error": "No audio"}, status=400)

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        for chunk in audio.chunks():
            tmp.write(chunk)
        path = tmp.name

    try:
        text = transcribe(path)
    finally:
        os.remove(path)

    if not text:
        return Response({"error": "Could not understand audio"}, status=400)

    reply = answer(text)
    audio_url = synthesize(reply)

    return Response({
        "transcript": text,
        "answer": reply,
        "audio_url": request.build_absolute_uri(audio_url),
    })
''')

add("backend/voice/urls.py", r'''
from django.urls import path
from . import views

urlpatterns = [
    path("voice/", views.voice_chat),
]
''')

# ---------------------------------------------------------------- RAG
add("backend/rag/__init__.py", "")

add("backend/rag/embeddings.py", r'''
_model = None


def embed(texts):
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts, normalize_embeddings=True).astype("float32")
''')

add("backend/rag/ingest.py", r'''
import json

from django.conf import settings

from .embeddings import embed


def chunk_text(text, size=150, overlap=30):
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step)]


def run():
    import faiss

    docs_dir = settings.DATA_DIR / "documents"
    chunks = []
    for f in docs_dir.glob("*.txt"):
        chunks += chunk_text(f.read_text(encoding="utf-8"))

    if not chunks:
        print("No .txt files found in data/documents/")
        return

    vectors = embed(chunks)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    store = settings.DATA_DIR / "vector_store"
    store.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(store / "index.faiss"))
    (store / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    print(f"Ingested {len(chunks)} chunks")
''')

add("backend/rag/management/__init__.py", "")
add("backend/rag/management/commands/__init__.py", "")
add("backend/rag/management/commands/ingest.py", r'''
from django.core.management.base import BaseCommand

from rag.ingest import run


class Command(BaseCommand):
    help = "Build the FAISS index from data/documents/*.txt"

    def handle(self, *args, **options):
        run()
''')

add("backend/rag/retriever.py", r'''
import json

from django.conf import settings

from .embeddings import embed

_index = None
_chunks = None


def _load():
    global _index, _chunks
    if _index is None:
        import faiss
        store = settings.DATA_DIR / "vector_store"
        _index = faiss.read_index(str(store / "index.faiss"))
        _chunks = json.loads((store / "chunks.json").read_text(encoding="utf-8"))


def search(query, k=3):
    _load()
    _, ids = _index.search(embed([query]), k)
    return [_chunks[i] for i in ids[0] if i != -1]
''')

add("backend/rag/llm.py", r'''
import os

_client = None


def ask(system_prompt, user_prompt):
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
    resp = _client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content.strip()
''')

add("backend/rag/pipeline.py", r'''
from .retriever import search
from .llm import ask

SYSTEM = (
    "You are a voice assistant. Answer using only the context given. "
    "Keep answers short (1-3 sentences) and plain text, since they will be spoken aloud. "
    "If the answer is not in the context, say you don't know."
)


def answer(question: str) -> str:
    context = "\n\n".join(search(question))
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    return ask(SYSTEM, prompt)
''')

add("backend/data/documents/info.txt", r'''
This is a Voice Assistant project built with a React PWA frontend and a Django backend.
The assistant listens to your voice using Whisper speech to text.
It searches the project documents using FAISS and sentence transformer embeddings.
An LLM then writes a short answer from the retrieved text.
Finally KittenTTS converts the answer into speech and plays it in the browser.
Users must register and login before they can use the voice assistant.
''')

# ---------------------------------------------------------------- FRONTEND
add("frontend/package.json", r'''
{
  "name": "voice-assistant-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.0"
  }
}
''')

add("frontend/vite.config.js", r'''
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
''')

add("frontend/index.html", r'''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="manifest" href="/manifest.json" />
    <meta name="theme-color" content="#1e88e5" />
    <title>Voice Assistant</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''')

add("frontend/public/manifest.json", r'''
{
  "name": "Voice Assistant",
  "short_name": "VoiceAI",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1e88e5",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
''')

add("frontend/public/service-worker.js", r'''
const CACHE = "voice-assistant-v1";
const ASSETS = ["/", "/index.html", "/manifest.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || e.request.url.includes("/api/")) return;
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request))
  );
});
''')

add("frontend/src/main.jsx", r'''
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js");
  });
}
''')

add("frontend/src/services/api.js", r'''
const API_URL = "http://127.0.0.1:8000/api";

export const getToken = () => localStorage.getItem("token");
export const getUsername = () => localStorage.getItem("username");

export const saveSession = (token, username) => {
  localStorage.setItem("token", token);
  localStorage.setItem("username", username);
};

export const clearSession = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
};

async function authRequest(path, username, password) {
  const res = await fetch(`${API_URL}/auth/${path}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

export const login = (username, password) => authRequest("login", username, password);
export const register = (username, password) => authRequest("register", username, password);

export async function logout() {
  try {
    await fetch(`${API_URL}/auth/logout/`, {
      method: "POST",
      headers: { Authorization: `Token ${getToken()}` },
    });
  } catch (e) {}
  clearSession();
}

export async function sendAudio(blob) {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");

  const res = await fetch(`${API_URL}/voice/`, {
    method: "POST",
    headers: { Authorization: `Token ${getToken()}` },
    body: form,
  });

  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}
''')

add("frontend/src/hooks/useRecorder.js", r'''
import { useRef, useState } from "react";

export default function useRecorder(onStop) {
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];

    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      onStop(new Blob(chunksRef.current, { type: "audio/webm" }));
    };

    recorder.start();
    recorderRef.current = recorder;
    setRecording(true);
  };

  const stop = () => {
    recorderRef.current?.stop();
    setRecording(false);
  };

  return { recording, start, stop };
}
''')

add("frontend/src/components/MicButton.jsx", r'''
export default function MicButton({ recording, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        width: 90,
        height: 90,
        borderRadius: "50%",
        border: "none",
        fontSize: 32,
        color: "#fff",
        background: recording ? "#e53935" : "#1e88e5",
      }}
    >
      {recording ? "■" : "🎤"}
    </button>
  );
}
''')

add("frontend/src/components/TranscriptBox.jsx", r'''
export default function TranscriptBox({ transcript, answer }) {
  if (!transcript) return null;
  return (
    <div style={{ marginTop: 24, textAlign: "left" }}>
      <p><b>You:</b> {transcript}</p>
      <p><b>Assistant:</b> {answer}</p>
    </div>
  );
}
''')

add("frontend/src/components/AudioPlayer.jsx", r'''
export default function AudioPlayer({ src }) {
  if (!src) return null;
  return <audio src={src} controls autoPlay style={{ marginTop: 16 }} />;
}
''')

add("frontend/src/components/Login.jsx", r'''
import { useState } from "react";
import { login, register, saveSession } from "../services/api";

export default function Login({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      const fn = isRegister ? register : login;
      const data = await fn(username, password);
      saveSession(data.token, data.username);
      onLogin(data.username);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const input = {
    display: "block",
    width: "100%",
    padding: 10,
    marginBottom: 12,
    boxSizing: "border-box",
    fontSize: 16,
  };

  return (
    <div style={{ maxWidth: 320, margin: "80px auto", textAlign: "center" }}>
      <h2>Voice Assistant</h2>
      <h3>{isRegister ? "Create account" : "Login"}</h3>

      <input
        style={input}
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        style={input}
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
      />

      {error && <p style={{ color: "#e53935" }}>{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          width: "100%",
          padding: 10,
          fontSize: 16,
          background: "#1e88e5",
          color: "#fff",
          border: "none",
          borderRadius: 4,
        }}
      >
        {loading ? "Please wait..." : isRegister ? "Register" : "Login"}
      </button>

      <p
        style={{ cursor: "pointer", color: "#1e88e5" }}
        onClick={() => {
          setIsRegister(!isRegister);
          setError("");
        }}
      >
        {isRegister ? "Already have an account? Login" : "New user? Register"}
      </p>
    </div>
  );
}
''')

add("frontend/src/App.jsx", r'''
import { useState } from "react";
import Login from "./components/Login";
import MicButton from "./components/MicButton";
import TranscriptBox from "./components/TranscriptBox";
import AudioPlayer from "./components/AudioPlayer";
import useRecorder from "./hooks/useRecorder";
import { sendAudio, getToken, getUsername, logout } from "./services/api";

export default function App() {
  const [user, setUser] = useState(getToken() ? getUsername() : null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleLogout = async () => {
    await logout();
    setResult(null);
    setUser(null);
  };

  const handleStop = async (blob) => {
    setLoading(true);
    try {
      setResult(await sendAudio(blob));
    } catch (e) {
      if (e.message === "unauthorized") {
        await handleLogout();
      } else {
        alert("Something went wrong");
      }
    }
    setLoading(false);
  };

  const { recording, start, stop } = useRecorder(handleStop);

  if (!user) return <Login onLogin={setUser} />;

  return (
    <div style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span>Hi, {user}</span>
        <button onClick={handleLogout}>Logout</button>
      </div>

      <h2>Voice Assistant</h2>
      <MicButton
        recording={recording}
        disabled={loading}
        onClick={recording ? stop : start}
      />
      <p>{loading ? "Thinking..." : recording ? "Listening..." : "Tap to speak"}</p>
      <TranscriptBox transcript={result?.transcript} answer={result?.answer} />
      <AudioPlayer src={result?.audio_url} />
    </div>
  );
}
''')

# ---------------------------------------------------------------- WRITE
for rel, content in FILES.items():
    target = ROOT / rel
    if rel in KEEP_IF_EXISTS and target.exists():
        print("kept   ", rel)
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print("created", rel)

for d in ["backend/data/vector_store", "backend/media"]:
    (ROOT / d).mkdir(parents=True, exist_ok=True)

icons = ROOT / "frontend/public/icons"
icons.mkdir(parents=True, exist_ok=True)
(icons / "icon-192.png").write_bytes(png(192, (30, 136, 229)))
(icons / "icon-512.png").write_bytes(png(512, (30, 136, 229)))
print("created icons")
print("\nDONE. Now follow Step 2 onwards.")