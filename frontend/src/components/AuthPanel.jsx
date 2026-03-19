import { useState } from "react";


function AuthPanel({ currentUser, isLoading, onLogin, onRegister, onLogout }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    const cleanedUsername = username.trim();
    const cleanedPassword = password.trim();
    if (!cleanedUsername || !cleanedPassword) {
      setError("Username and password are required.");
      return;
    }

    setError("");

    try {
      if (mode === "login") {
        await onLogin({ username: cleanedUsername, password: cleanedPassword });
      } else {
        await onRegister({ username: cleanedUsername, password: cleanedPassword });
      }
      setPassword("");
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Authentication failed."
      );
    }
  };

  if (currentUser) {
    return (
      <section className="side-card auth-panel">
        <div className="side-card-header">
          <h2>Account</h2>
          <p>Authenticated session for uploads and scoped retrieval.</p>
        </div>

        <div className="account-card">
          <span className="account-label">Signed in as</span>
          <strong>{currentUser}</strong>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={onLogout}
          disabled={isLoading}
        >
          Log Out
        </button>
      </section>
    );
  }

  return (
    <section className="side-card auth-panel">
      <div className="side-card-header">
        <h2>{mode === "login" ? "Login" : "Register"}</h2>
        <p>Sign in to upload private documents and blend them into retrieval.</p>
      </div>

      <div className="auth-toggle">
        <button
          type="button"
          className={mode === "login" ? "toggle-button active" : "toggle-button"}
          onClick={() => setMode("login")}
        >
          Login
        </button>
        <button
          type="button"
          className={mode === "register" ? "toggle-button active" : "toggle-button"}
          onClick={() => setMode("register")}
        >
          Register
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="Username"
          disabled={isLoading}
        />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
          disabled={isLoading}
        />
        <button type="submit" className="primary-button" disabled={isLoading}>
          {isLoading ? "Please wait..." : mode === "login" ? "Login" : "Create Account"}
        </button>
      </form>

      {error && <p className="inline-error">{error}</p>}
    </section>
  );
}


export default AuthPanel;
