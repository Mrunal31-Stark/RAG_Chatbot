const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getBaseUrl() {
  return API_URL.endsWith("/") ? API_URL.slice(0, -1) : API_URL;
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

  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    throw new Error(payload.error || "Failed to send message.");
  }

  return payload;
}

