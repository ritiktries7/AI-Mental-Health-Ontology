import { useState, useRef } from "react";

export default function TextPrediction({ setResult }) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef(null);

  const handleChange = (e) => {
    setText(e.target.value);
    setError("");

    const el = textareaRef.current;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  };

  const handlePredict = async () => {
    if (loading) return;

    if (!text.trim()) {
      setError("Please enter your thoughts.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) throw new Error();

      const data = await res.json();
      setResult(data);

    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

return (
  <div className="space-y-6 max-w-lg">

    <div>
      <h2 className="text-8xl font-semibold text-[#5C4033] mb-3">
        Understand Your Emotions
      </h2>

      <p className="text-[#7B5E57] text-xl leading-relaxed">
        Share how you feel. This AI analyzes emotional signals in your text 
        and helps you understand your mental state.
      </p>
    </div>

    <textarea
      ref={textareaRef}
      value={text}
      onChange={handleChange}
      placeholder="Write what's on your mind..."
      className="w-full text-xl min-h-[140px] p-4 rounded-2xl bg-[#FFF8F0] border border-[#E5D3C5] focus:ring-2 focus:ring-[#ED8936] resize-none"
    />

    {error && <p className="text-sm text-red-500">{error}</p>}

    <button
      onClick={handlePredict}
      disabled={loading}
      className={`px-6 py-3 rounded-xl text-white ${
        loading ? "bg-gray-400" : "bg-[#ED8936]"
      }`}
    >
      {loading ? "Analyzing..." : "Analyze"}
    </button>

  </div>
);
}