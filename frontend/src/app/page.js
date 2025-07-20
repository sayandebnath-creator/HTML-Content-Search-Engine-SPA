"use client";

import { useState } from "react";
import { Search, Globe, Sparkles, AlertCircle, Loader2 } from "lucide-react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!url || !query) return;

    setLoading(true);
    setError("");
    setResults([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url, query }),
      });

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch results. Ensure backend is running and the URL is valid.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-normal text-gray-800 mb-6">
            <span className="text-blue-500">W</span>
            <span className="text-red-500">e</span>
            <span className="text-yellow-500">b</span>
            <span className="text-blue-500">S</span>
            <span className="text-green-500">i</span>
            <span className="text-red-500">t</span>
            <span className="text-yellow-500">e </span>
            Content Search
          </h1>
        </div>

        {/* Search Form */}
        <div className="mb-8">
          {/* URL Input */}
          <div className="mb-4">
            <div className="relative">
              <div className="flex items-center w-full max-w-lg mx-auto bg-white border border-gray-300 rounded-full px-4 py-3 shadow-lg hover:shadow-xl focus-within:shadow-xl transition-shadow duration-200">
                <Globe className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
                <input
                  type="text"
                  placeholder="Enter website URL"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1 outline-none text-gray-700 text-base"
                />
              </div>
            </div>
          </div>

          {/* Query Input with Search Button */}
          <div className="relative">
            <div className="flex items-center w-full max-w-lg mx-auto bg-white border border-gray-300 rounded-full px-4 py-3 shadow-lg hover:shadow-xl focus-within:shadow-xl transition-shadow duration-200">
              <Search className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
              <input
                type="text"
                placeholder="Search for content..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 outline-none text-gray-700 text-base mr-2"
              />
              <button
                onClick={handleSearch}
                disabled={loading || !url || !query}
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 flex items-center gap-2 flex-shrink-0"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="hidden sm:inline">Searching</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span className="hidden sm:inline">Search</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-2xl mx-auto bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div className="max-w-2xl mx-auto">
            <div className="mb-4 text-sm text-gray-600">
              About {results.length} results
            </div>
            
            <div className="space-y-6">
              {results.map((res, i) => (
                <div key={i} className="border-b border-gray-200 pb-4">
                  <div className="mb-2">
                    <h3 className="text-lg text-blue-600 hover:underline cursor-pointer font-medium">
                      Result {i + 1}
                    </h3>
                    <div className="text-sm text-green-700">
                      Content excerpt
                    </div>
                  </div>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {res.content.slice(0, 300)}...
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && results.length === 0 && !error && (
          <div className="text-center py-16">
            <div className="text-gray-400 mb-4">
              <Search className="w-16 h-16 mx-auto opacity-20" />
            </div>
            <p className="text-gray-500 text-sm">
              Enter a website URL and search query to find relevant content
            </p>
          </div>
        )}
      </div>
    </div>
  );
}