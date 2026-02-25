import { useMemo, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import ChatInput from "./components/ChatInput";
import ChatWindow from "./components/ChatWindow";

const SESSION_STORAGE_KEY = "rag_assistant_session_id";
const CHAT_ENDPOINT = "/api/chat";
const WELCOME_MESSAGE =
  "Ask me anything about machine learning, deep learning, NLP, or model training.";

function createMessage(role, content, options = {}) {
  return {
    id: uuidv4(),
    role,
    content,
    timestamp: Date.now(),
    retrievedChunks:
      typeof options.retrievedChunks === "number" ? options.retrievedChunks : null,
  };
}

function getOrCreateSessionId() {
  if (typeof window === "undefined") {
    return uuidv4();
  }

  const existingSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (existingSessionId) {
    return existingSessionId;
  }

  const generatedSessionId = uuidv4();
  window.localStorage.setItem(SESSION_STORAGE_KEY, generatedSessionId);
  return generatedSessionId;
}

function App() {
  const [sessionId, setSessionId] = useState(() => getOrCreateSessionId());
  const [messages, setMessages] = useState([
    createMessage("assistant", WELCOME_MESSAGE),
  ]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const shortSessionId = useMemo(() => sessionId.slice(0, 8), [sessionId]);

  const handleSend = async (userInput) => {
    if (isLoading) {
      return;
    }

    const message = userInput.trim();
    if (!message) {
      return;
    }

    setError("");
    setMessages((previous) => [...previous, createMessage("user", message)]);
    setIsLoading(true);

    try {
      const response = await fetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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

      const assistantReply =
        typeof payload.reply === "string" && payload.reply.trim()
          ? payload.reply.trim()
          : "I don't know";

      const retrievedChunks =
        typeof payload.retrievedChunks === "number" ? payload.retrievedChunks : null;

      setMessages((previous) => [
        ...previous,
        createMessage("assistant", assistantReply, { retrievedChunks }),
      ]);
    } catch (requestError) {
      const messageText =
        requestError instanceof Error
          ? requestError.message
          : "Request failed. Please try again.";
      setError(messageText);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    const newSessionId = uuidv4();
    if (typeof window !== "undefined") {
      window.localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    }

    setSessionId(newSessionId);
    setError("");
    setIsLoading(false);
    setMessages([createMessage("assistant", WELCOME_MESSAGE)]);
  };

  return (
    <main className="app-shell">
      <section className="chat-card">
        <header className="chat-header">
          <div>
            <h1>AI Learning Assistant</h1>
            <p>RAG chat interface</p>
          </div>

          <div className="chat-header-actions">
            <span className="session-pill" title={sessionId}>
              Session: {shortSessionId}
            </span>
            <button type="button" className="new-chat-button" onClick={handleNewChat}>
              New Chat
            </button>
          </div>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} />

        {error && <p className="error-banner">{error}</p>}

        <ChatInput onSend={handleSend} disabled={isLoading} />
      </section>
    </main>
  );
}

export default App;