// import PDFDropBox from "../components/PDFDropBox";
import Suggestions from "../components/suggestions";
import ResearchReport from "../components/ResearchReport.jsx";

import { useState } from "react";
// import Questions from "../components/questions";

export default function Home() {
  const [topic, setTopic] = useState("");
  const [query, setQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const handleInput = (e) => setQuery(e.target.value);
  const handleSearch = () => {
    setTopic(query);
    setQuery("");
    setHasSearched(true);
  };

  const handleEnter = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-950 flex flex-col items-center">
      {/* Hero Section */}
      <div
        className={`w-full flex flex-col items-center transition-all duration-700 ${
          hasSearched ? "pt-2" : "pt-70"
        }`}
        style={{ minHeight: hasSearched ? "0" : "40vh" }}
      >
        {!hasSearched ? (
          <h1 className="text-3xl md:text-3xl font-extrabold text-white drop-shadow mb-4 tracking-tight select-none">
            ResearchBuddy
          </h1>
        ) : (
          <>
            <h1
              className="text-xl md:text-3xl font-extrabold text-white drop-shadow mb-2 tracking-tight select-none fixed top-10 left-1/2 -translate-x-1/2 w-full text-center pt-4 z-50"
              style={{ background: "transparent" }}
            >
              {topic}
            </h1>
            <span
              className="fixed top-10 left-0 pl-6 text-2xl md:text-2xl font-extrabold select-none z-50"
              style={{ color: "#ff3399", fontFamily: "FK Grotesk, sans-serif" }}
            >
              ResearchBuddy
            </span>
          </>
        )}
        {/* Search Bar and Upload PDF */}
        {!hasSearched ? (
          <div
            className={`w-full max-w-xl px-4 z-30 flex flex-col items-center gap-4 mt-10`}
          >
            <div className="flex w-full bg-gray-800 rounded-none shadow-xl overflow-hidden border border-gray-700 transition duration-300 ease-in-out mb-2">
              <label className="flex items-center cursor-pointer px-3" title="Attach PDF">
                <input type="file" accept="application/pdf" style={{ display: 'none' }} onChange={() => {}} />
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="#ff3399" className="w-6 h-6">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-3A2.25 2.25 0 008.25 5.25V9m7.5 0H8.25m7.5 0v9A2.25 2.25 0 0113.5 20.25h-3A2.25 2.25 0 018.25 18V9m7.5 0H8.25" />
                </svg>
              </label>
              <input
                type="text"
                className="w-full px-6 py-4 text-gray-100 placeholder-gray-400 bg-transparent text-lg transition-all duration-300 ease-in-out rounded-none"
                style={{ borderColor: "#ff3399", borderWidth: "2px" }}
                placeholder="Type a topic or upload slides for research"
                onChange={handleInput}
                value={query}
                onKeyDown={handleEnter}
              />
              <button
                style={{ backgroundColor: "#ff3399", color: "#222", cursor: 'pointer' }}
                className="px-6 py-4 transition-all duration-200 font-semibold  rounded-none flex items-center justify-center group"
                onClick={handleSearch}
                aria-label="Search"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="#222"
                  className="w-6 h-6 group-hover:translate-x-1 transition-transform duration-200"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14m-7-7l7 7-7 7" />
                </svg>
              </button>
            </div>
            {/* Drag and Drop PDF Upload Box */}
            {/* <PDFDropBox /> */}
            <Suggestions
              onSuggestionClick={(suggestion) => {
                setTopic(suggestion);
                setHasSearched(true);
              }}
            />
          </div>
        ) : (
          <div className="fixed top-10 right-10 z-50 flex items-center gap-4">
            <button
              style={{ backgroundColor: '#ff3399', color: '#222', fontWeight: 700, fontFamily: 'FK Grotesk, sans-serif', fontSize: '0.85rem', padding: '0.25rem 0.6rem', cursor: 'pointer' }}
              className="rounded-md shadow-lg hover:scale-105 transition"
              onClick={() => { setHasSearched(false); setTopic(''); }}
            >
              New Thread
            </button>
          </div>
        )}
      </div>
      {/* Questions Section */}
<div
  className={`w-full flex flex-col items-center transition-all duration-700 ${
    hasSearched ? "opacity-100 pt-8 pb-10" : "opacity-0 pointer-events-none"
  } scrollbar-thin scrollbar-thumb-black scrollbar-track-gray-950`}
  style={{
    minHeight: hasSearched ? "40vh" : "0",
    maxHeight: hasSearched ? "calc(100vh - 140px)" : "0",
    overflowY: "auto",
    marginTop: hasSearched ? "120px" : "0",
  }}
>
  {topic && <ResearchReport topic={topic} />}
</div>


    </div>
  );
}
