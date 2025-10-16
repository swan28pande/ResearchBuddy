import { useEffect, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

const ResearchReport = ({ topic }) => {
  const [report, setReport] = useState("");
  const [loading, setLoading] = useState(false);
  const [refusalMsg, setRefusalMsg] = useState("");

  useEffect(() => {
    const generateReport = async () => {
      try {
        setReport("");
        setRefusalMsg(""); // Clear prior refusals
        if (!topic) return;
        setLoading(true);
        const response = await axios.post(
          "http://localhost:5001/api/research",
          { query: topic }
        );

        if (
          typeof response.data === "string" &&
          response.data.toLowerCase().includes("unable to generate report")
        ) {
          setRefusalMsg(response.data);
        } else {
          setReport(response.data.report);
        }
      } catch (error) {
        setRefusalMsg("Error generating report.");
        console.error("Error generating report:", error);
      }
      setLoading(false);
    };
    generateReport();
  }, [topic]);

  return (
    <div className="flex flex-col gap-8 items-center py-4 w-full">
      {refusalMsg ? (
        <div className="flex flex-col items-center justify-center min-h-[30vh] w-full">
          <div
            className="w-full max-w-md px-8 py-6 rounded-lg shadow-md border border-yellow-400 text-yellow-400 bg-gray-900 text-center"
            style={{
              fontFamily: "FK Grotesk, sans-serif",
              fontWeight: 700,
              fontSize: "0.8rem",
              color: "#EEFC7C",
              borderColor: "#EEFC7C",
            }}
          >
            {refusalMsg}
          </div>
        </div>
      ) : loading ? (
        <div className="flex flex-col items-center justify-center min-h-[50vh] w-full">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="w-12 h-12 text-yellow-400 animate-pulse"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 2a7 7 0 00-4 12.9V17a2 2 0 002 2h4a2 2 0 002-2v-2.1A7 7 0 0012 2z"
            />
          </svg>
          <span
            className="mt-3 text-lg font-medium"
            style={{ color: "#EEFC7C" }}
          >
            Generating research report...
          </span>
        </div>
      ) : report ? (
        <div className="w-full max-w-4xl">
          <ReactMarkdown
            className="text-white bg-gray-800 p-6 rounded-lg leading-relaxed"
            components={{
                h1: ({ children }) => (
                  <h1 className="text-lg font-bold text-white mt-8 mb-4 border-b border-gray-600 pb-2">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-base font-semibold text-white mt-6 mb-3">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-medium text-white mt-4 mb-2">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="mb-3 text-sm text-white leading-relaxed">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-4 ml-4 text-sm text-white space-y-1">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-4 ml-4 text-sm text-white space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-sm text-white">{children}</li>
                ),
                code: ({ children }) => (
                  <code className="bg-gray-700 text-white px-1 py-0.5 rounded text-xs font-mono">
                    {children}
                  </code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-gray-700 text-white p-3 rounded-lg overflow-x-auto mb-4 text-xs">
                    {children}
                  </pre>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="pl-4 border-l-4 border-gray-600 italic text-sm text-white mb-4">
                    {children}
                  </blockquote>
                ),
              strong: ({ children }) => (
                <strong className="font-bold text-white">{children}</strong>
              ),
              em: ({ children }) => (
                <em className="italic text-white">{children}</em>
              ),
              a: ({ href, children }) => (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="underline hover:no-underline transition-all duration-200"
                  style={{ color: "#ff3399" }}
                >
                  {children}
                </a>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="min-w-full border-collapse border border-gray-600 text-sm">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-gray-700">
                  {children}
                </thead>
              ),
              tbody: ({ children }) => (
                <tbody>
                  {children}
                </tbody>
              ),
              tr: ({ children }) => (
                <tr className="border-b border-gray-600">
                  {children}
                </tr>
              ),
              th: ({ children }) => (
                <th className="border border-gray-600 px-3 py-2 text-left font-semibold text-white bg-gray-700">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-gray-600 px-3 py-2 text-white">
                  {children}
                </td>
              ),
                hr: () => <div className="my-8 border-t border-gray-600" />, // section separator
            }}
          >
            {report}
          </ReactMarkdown>
        </div>
      ) : null}
    </div>
  );
};

export default ResearchReport;
