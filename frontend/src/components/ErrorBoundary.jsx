import { Component } from "react";


class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : "Unexpected frontend error.",
    };
  }

  componentDidCatch(error) {
    console.error("Frontend render error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="app-shell">
          <section className="chat-card crash-card">
            <header className="chat-header">
              <div>
                <h1>Frontend Error</h1>
                <p>The UI crashed during render. Check the browser console.</p>
              </div>
            </header>
            <div className="crash-content">
              <p>{this.state.message}</p>
              <p>Restart the frontend after running `npm install` if dependencies changed.</p>
            </div>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}


export default ErrorBoundary;
