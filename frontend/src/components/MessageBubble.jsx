import ReactMarkdown from "react-markdown";

function formatTimestamp(timestamp) {
  if (typeof timestamp !== "number") {
    return "";
  }

  try {
    return new Intl.DateTimeFormat(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(timestamp));
  } catch {
    return "";
  }
}

function MessageBubble({ message }) {
  const isAssistant = message.role === "assistant";
  const roleLabel = isAssistant ? "Assistant" : "User";
  const timestamp = formatTimestamp(message.timestamp);

  return (
    <article className={`message ${message.role}`}>
      <span className="role">{roleLabel}</span>

      <div className="message-content markdown-content">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>

      <footer className="message-footer">
        {timestamp && <span className="timestamp">{timestamp}</span>}
        {isAssistant && typeof message.retrievedChunks === "number" && (
          <span className="chunk-count">Retrieved chunks: {message.retrievedChunks}</span>
        )}
      </footer>
    </article>
  );
}

export default MessageBubble;