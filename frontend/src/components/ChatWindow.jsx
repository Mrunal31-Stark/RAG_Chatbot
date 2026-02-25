import { useEffect, useRef } from "react";

import MessageBubble from "./MessageBubble";

function ChatWindow({ messages, isLoading }) {
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  return (
    <section className="message-list" aria-live="polite">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isLoading && (
        <article className="message assistant loading">
          <span className="role">Assistant</span>
          <p className="loading-text">
            <span className="spinner" aria-hidden="true" />
            <span>Typing...</span>
          </p>
        </article>
      )}

      <div ref={endOfMessagesRef} />
    </section>
  );
}

export default ChatWindow;