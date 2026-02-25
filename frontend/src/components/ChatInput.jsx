import { useState } from "react";

function ChatInput({ onSend, disabled }) {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    const message = inputValue.trim();
    if (!message || disabled) {
      return;
    }

    setInputValue("");
    await onSend(message);
  };

  return (
    <form className="chat-input-row" onSubmit={handleSubmit}>
      <input
        type="text"
        value={inputValue}
        onChange={(event) => setInputValue(event.target.value)}
        placeholder="Type your question..."
        disabled={disabled}
        aria-label="User message"
      />
      <button type="submit" disabled={disabled || !inputValue.trim()}>
        {disabled ? "Sending..." : "Send"}
      </button>
    </form>
  );
}

export default ChatInput;