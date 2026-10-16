import { useEffect, useRef, useState } from "react";
import "./App.css";
import Login from "./components/Login";
import useRecorder from "./hooks/useRecorder";
import {
  sendAudio,
  chat,
  speak,
  getToken,
  getUsername,
  logout,
} from "./services/api";

const SUGGESTIONS = [
  "Hello, how are you?",
  "What must users do before using the assistant?",
  "What does the assistant use for speech to text?",
];

let counter = 0;
const uid = () => `m${Date.now()}_${counter++}`;

function Bubble({ m }) {
  if (m.error) {
    return (
      <div className="row assistant">
        <div className="bubble error">⚠️ {m.error}</div>
      </div>
    );
  }
  return (
    <div className={`row ${m.role}`}>
      <div className={`bubble ${m.role} ${m.pending ? "pending" : ""}`}>
        {m.text}
        {m.voiceLoading && <div className="hint">Preparing voice...</div>}
        {m.audio && <audio src={m.audio} controls autoPlay={m.autoplay} />}
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(getToken() ? getUsername() : null);
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [voiceOn, setVoiceOn] = useState(true);
  const [input, setInput] = useState("");
  const voiceRef = useRef(true);
  const endRef = useRef(null);

  useEffect(() => {
    voiceRef.current = voiceOn;
  }, [voiceOn]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const add = (msg) => setMessages((m) => [...m, msg]);
  const update = (id, patch) =>
    setMessages((m) => m.map((x) => (x.id === id ? { ...x, ...patch } : x)));

  const handleLogout = async () => {
    await logout();
    setMessages([]);
    setUser(null);
  };

  const fail = async (e) => {
    if (e.message === "unauthorized") {
      await handleLogout();
      return;
    }
    add({ id: uid(), role: "assistant", error: e.message });
  };

  const reply = async (answer, error) => {
    const id = uid();
    if (error || !answer) {
      add({ id, role: "assistant", error: error || "Empty answer" });
      return;
    }
    add({ id, role: "assistant", text: answer });

    if (voiceRef.current) {
      update(id, { voiceLoading: true });
      try {
        const r = await speak(answer);
        update(id, { audio: r.audio_url, autoplay: true, voiceLoading: false });
      } catch (e) {
        update(id, { voiceLoading: false });
      }
    }
  };

  const sendText = async (text) => {
    const clean = text.trim();
    if (!clean || busy) return;
    setInput("");
    add({ id: uid(), role: "user", text: clean });
    setBusy(true);
    try {
      const data = await chat(clean);
      await reply(data.answer, data.error);
    } catch (e) {
      await fail(e);
    }
    setBusy(false);
  };

  const handleStop = async (blob) => {
    const userId = uid();
    add({ id: userId, role: "user", text: "Listening to you...", pending: true });
    setBusy(true);
    try {
      const data = await sendAudio(blob);
      update(userId, { text: data.transcript, pending: false });
      await reply(data.answer, data.error);
    } catch (e) {
      update(userId, { text: "(could not process audio)", pending: false });
      await fail(e);
    }
    setBusy(false);
  };

  const { recording, start, stop } = useRecorder(handleStop);

  const toggleMic = async () => {
    try {
      if (recording) stop();
      else await start();
    } catch (e) {
      add({
        id: uid(),
        role: "assistant",
        error: "Microphone not available. Please allow microphone permission.",
      });
    }
  };

  if (!user) return <Login onLogin={setUser} />;

  const status = recording
    ? "🔴 Listening... tap the button again to send"
    : busy
    ? "Thinking..."
    : "";

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="title">🎙️ Voice Assistant</div>
          <div className="sub">Hi, {user}</div>
        </div>
        <div className="actions">
          <button className="chip-btn" onClick={() => setVoiceOn(!voiceOn)}>
            {voiceOn ? "🔊 Voice on" : "🔇 Voice off"}
          </button>
          <button className="chip-btn" onClick={() => setMessages([])}>
            Clear
          </button>
          <button className="chip-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <main className="chat">
        {messages.length === 0 && (
          <div className="empty">
            <div className="big">👋</div>
            <p>Tap the mic and speak, or type your question below.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion" onClick={() => sendText(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <Bubble key={m.id} m={m} />
        ))}

        {busy && (
          <div className="row assistant">
            <div className="typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </main>

      <div className="status">{status}</div>

      <footer className="composer">
        <input
          placeholder="Type a message..."
          value={input}
          disabled={recording}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendText(input)}
        />
        <button
          className="send"
          onClick={() => sendText(input)}
          disabled={busy || recording || !input.trim()}
        >
          Send
        </button>
        <button
          className={`mic ${recording ? "recording" : ""}`}
          onClick={toggleMic}
          disabled={busy}
          title={recording ? "Stop and send" : "Speak"}
        >
          {recording ? "■" : "🎤"}
        </button>
      </footer>
    </div>
  );
}