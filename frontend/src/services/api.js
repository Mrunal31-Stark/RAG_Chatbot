const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";


function getBaseUrl() {
  return API_URL.endsWith("/") ? API_URL.slice(0, -1) : API_URL;
}


async function parseResponse(response) {
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }

  return payload;
}


export async function sendChatMessage({ sessionId, message }) {
  const response = await fetch(`${getBaseUrl()}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sessionId,
      message,
    }),
  });

  return parseResponse(response);
}


export async function registerUser({ username, password }) {
  const response = await fetch(`${getBaseUrl()}/api/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  return parseResponse(response);
}


export async function loginUser({ username, password }) {
  const response = await fetch(`${getBaseUrl()}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  return parseResponse(response);
}


export async function uploadDocument({ sessionId, file }) {
  const formData = new FormData();
  formData.append("sessionId", sessionId);
  formData.append("file", file);

  const response = await fetch(`${getBaseUrl()}/api/upload`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(response);
}


export async function getSessionDebugInfo(sessionId) {
  const response = await fetch(
    `${getBaseUrl()}/api/debug/session/${encodeURIComponent(sessionId)}`
  );

  return parseResponse(response);
}
