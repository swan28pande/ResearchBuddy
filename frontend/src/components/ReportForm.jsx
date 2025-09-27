import React, { useState } from "react";
import axios from "axios";

export default function ReportForm() {
  const [query, setQuery] = useState("");
  const [report, setReport] = useState("");
  const [pdfUrl, setPdfUrl] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setReport("");
    setPdfUrl("");
    try {
      const response = await axios.post("http://localhost:8000/api/research", { query });
      setReport(response.data.report);
      setPdfUrl(response.data.pdf_url);
    } catch (err) {
      setReport("Error: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          Research Query:
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            required
            style={{ width: "400px", margin: "0 1em" }}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Generating..." : "Generate Report"}
        </button>
      </form>
      {report && (
        <div style={{ marginTop: "2em" }}>
          <h2>Report</h2>
          <pre style={{ whiteSpace: "pre-wrap" }}>{report}</pre>
          {pdfUrl && (
            <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
              Download PDF
            </a>
          )}
        </div>
      )}
    </div>
  );
}
