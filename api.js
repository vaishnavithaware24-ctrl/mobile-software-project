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

async function post(path, options) {
  const res = await fetch(`${API_URL}/${path}/`, {
    method: "POST",
    ...options,
    headers: { ...(options.headers || {}), Authorization: `Token ${getToken()}` },
  });

  if (res.status === 401) throw new Error("unauthorized");

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Server error");
  return data;
}

export function sendAudio(blob) {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  return post("voice", { body: form });
}

export function chat(text) {
  return post("chat", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function speak(text) {
  return post("speak", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}