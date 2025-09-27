import { Lightbulb } from "lucide-react";

const suggestions = [
  "Neural Networks",
  "Linear Algebra",
  "System Design"
];

const Suggestions = ({ onSuggestionClick }) => {
  const handleClick = (suggestion) => {
    if (typeof onSuggestionClick === "function") {
      onSuggestionClick(suggestion);
    }
  };

  return (
    <div className="flex gap-2 mt-3 w-full justify-center overflow-x-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion}
          className="px-2.5 py-1.5 bg-gray-800 text-gray-100 rounded-none shadow border border-gray-700 font-medium text-xs transition cursor-pointer flex items-center gap-1.5 group hover:shadow-lg hover:-translate-y-0.5 whitespace-nowrap"
          onClick={() => handleClick(suggestion)}
        >
          <Lightbulb className="w-3.5 h-3.5 text-yellow-400" />
          {suggestion}
        </button>
      ))}
    </div>
  );
};

export default Suggestions;
