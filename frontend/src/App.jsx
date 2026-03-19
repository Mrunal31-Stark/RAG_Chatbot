import { useState } from "react";
import { v4 as uuidv4 } from "uuid";

import AuthPanel from "./components/AuthPanel";
import ChatInput from "./components/ChatInput";
import ChatWindow from "./components/ChatWindow";
import UploadPanel from "./components/UploadPanel";
import {
  loginUser,
  registerUser,
  sendChatMessage,
  uploadDocument,
} from "./services/api";


const SESSION_STORAGE_KEY = "rag_assistant_session_id";
const USERNAME_STORAGE_KEY = "rag_assistant_username";
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


function getStoredSessionId() {
  if (typeof window === "undefined") {
    return uuidv4();
  }

  try {
    const existingSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (existingSessionId) {
      return existingSessionId;
    }

    const generatedSessionId = uuidv4();
    window.localStorage.setItem(SESSION_STORAGE_KEY, generatedSessionId);
    return generatedSessionId;
  } catch {
    return uuidv4();
  }
}


function getStoredUsername() {
  if (typeof window === "undefined") {
    return "";
  }

  try {
    return window.localStorage.getItem(USERNAME_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}


function App() {
  const [sessionId, setSessionId] = useState(() => getStoredSessionId());
  const [currentUser, setCurrentUser] = useState(() => getStoredUsername());
  const [messages, setMessages] = useState([createMessage("assistant", WELCOME_MESSAGE)]);
  const [error, setError] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  const [isUploadLoading, setIsUploadLoading] = useState(false);

  const isBusy = isChatLoading || isAuthLoading || isUploadLoading;

  const persistSession = (nextSessionId, username = "") => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.setItem(SESSION_STORAGE_KEY, nextSessionId);
      if (username) {
        window.localStorage.setItem(USERNAME_STORAGE_KEY, username);
      } else {
        window.localStorage.removeItem(USERNAME_STORAGE_KEY);
      }
    } catch {
      // Ignore storage failures so the app still renders in restricted browsers.
    }
  };

  const resetConversation = (message = WELCOME_MESSAGE) => {
    setMessages([createMessage("assistant", message)]);
    setError("");
  };

  const handleAuthSuccess = (payload, actionLabel) => {
    const nextSessionId = payload.sessionId;
    const username = payload.username || "";

    setSessionId(nextSessionId);
    setCurrentUser(username);
    persistSession(nextSessionId, username);
    resetConversation(
      `${actionLabel} successful. Your private uploads will now be included in retrieval.`
    );
  };

  const handleLogin = async ({ username, password }) => {
    setIsAuthLoading(true);
    try {
      const payload = await loginUser({ username, password });
      handleAuthSuccess(payload, "Login");
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleRegister = async ({ username, password }) => {
    setIsAuthLoading(true);
    try {
      const payload = await registerUser({ username, password });
      handleAuthSuccess(payload, "Registration");
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleLogout = () => {
    const guestSessionId = uuidv4();
    setCurrentUser("");
    setSessionId(guestSessionId);
    persistSession(guestSessionId, "");
    resetConversation("Logged out. You can continue chatting as a guest.");
  };

  const handleSend = async (userInput) => {
    if (isChatLoading) {
      return;
    }

    const message = userInput.trim();
    if (!message) {
      return;
    }

    setError("");
    setMessages((previous) => [...previous, createMessage("user", message)]);
    setIsChatLoading(true);

    try {
      const payload = await sendChatMessage({ sessionId, message });
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
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Request failed. Please try again."
      );
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleUpload = async (file) => {
    setIsUploadLoading(true);
    try {
      return await uploadDocument({ sessionId, file });
    } finally {
      setIsUploadLoading(false);
    }
  };

  const handleNewChat = () => {
    if (!currentUser) {
      const guestSessionId = uuidv4();
      setSessionId(guestSessionId);
      persistSession(guestSessionId, "");
    }
    resetConversation(WELCOME_MESSAGE);
  };

  return (
    <main className="app-shell">
      <section className="workspace-grid">
        <aside className="sidebar">
          <AuthPanel
            currentUser={currentUser}
            isLoading={isAuthLoading}
            onLogin={handleLogin}
            onRegister={handleRegister}
            onLogout={handleLogout}
          />
          <UploadPanel
            currentUser={currentUser}
            isLoading={isUploadLoading}
            onUpload={handleUpload}
          />
        </aside>

        <section className="chat-card">
          <header className="chat-header">
            <div>
              <h1>AI Learning Assistant</h1>
              <p>Global RAG + private user document retrieval</p>
            </div>

            <div className="chat-header-actions">
              <span className="session-pill" title={sessionId}>
                {currentUser ? `User: ${currentUser}` : "Guest Session"}
              </span>
              <button
                type="button"
                className="new-chat-button"
                onClick={handleNewChat}
                disabled={isBusy}
              >
                New Chat
              </button>
            </div>
          </header>

          <ChatWindow messages={messages} isLoading={isChatLoading} />

          {error && <p className="error-banner">{error}</p>}

          <ChatInput onSend={handleSend} disabled={isBusy} />
        </section>
      </section>
    </main>
  );
}


export default App;
