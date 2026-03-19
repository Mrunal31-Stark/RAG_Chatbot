import { useState } from "react";


function UploadPanel({ currentUser, isLoading, onUpload }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file) {
      setError("Choose a PDF or text file first.");
      return;
    }

    setError("");
    setStatus("Uploading and indexing document...");

    try {
      const payload = await onUpload(file);
      setStatus(payload.message || "Document uploaded successfully.");
      setFile(null);
      event.currentTarget.reset();
    } catch (requestError) {
      setStatus("");
      setError(requestError instanceof Error ? requestError.message : "Upload failed.");
    }
  };

  return (
    <section className="side-card upload-panel">
      <div className="side-card-header">
        <h2>Document Upload</h2>
        <p>
          Upload PDF or text files to add user-specific context on top of the shared
          knowledge base.
        </p>
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf,.txt,.md,text/plain,application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          disabled={!currentUser || isLoading}
        />
        <button
          type="submit"
          className="primary-button"
          disabled={!currentUser || isLoading || !file}
        >
          {isLoading ? "Working..." : "Upload Document"}
        </button>
      </form>

      {!currentUser && (
        <p className="helper-text">Login or register to enable private document uploads.</p>
      )}
      {status && <p className="upload-status success">{status}</p>}
      {error && <p className="upload-status error">{error}</p>}
    </section>
  );
}


export default UploadPanel;
