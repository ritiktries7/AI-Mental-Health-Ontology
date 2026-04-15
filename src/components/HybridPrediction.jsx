import { useState, useRef } from "react";
import PHQ9Form from "./PHQ9Form";

export default function HybridPrediction({ result, setResult }) {
  const [text, setText] = useState("");
  const [phq9, setPhq9] = useState(Array(9).fill(0));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef(null);

  // 🔹 Handle input + auto resize
  const handleChange = (e) => {
    setText(e.target.value);
    setError("");

    const el = textareaRef.current;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  };

  // 🔹 API call
  const handlePredict = async () => {
    if (loading) return;

    if (!text.trim()) {
      setError("Please enter your thoughts.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const res = await fetch("http://localhost:8000/hybrid_predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text, phq9 }),
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

  const handleReset = () => {
    setResult(null);
    setText("");
    setPhq9(Array(9).fill(0));
  };

  // 🔥 RESULT VIEW
  if (result) {
    const risk = result.combined_risk || result.risk;
    const score = result.combined_score ?? result.score ?? 0;
    const cues = result?.ontology_explanation?.text_cues ?? [];

    // ✅ FIXED KEY
    const phqScore = result.phq_total ?? 0;

    const getSeverity = (score) => {
      if (score <= 4) return "Minimal";
      if (score <= 9) return "Mild";
      if (score <= 14) return "Moderate";
      if (score <= 19) return "Moderately Severe";
      return "Severe";
    };

    return (
      <div className="text-center space-y-8">

        {/* Title */}
        <h2 className="text-3xl font-semibold text-[#5C4033]">
          Hybrid Analysis Result
        </h2>

        {/* Risk */}
        <div className="text-2xl font-medium text-[#2F855A]">
          {risk} Risk
        </div>

        {/* AI Confidence */}
        <div className="max-w-md mx-auto">
          <div className="flex justify-between text-sm text-[#7B5E57] mb-2">
            <span>AI Confidence</span>
            <span>{(score * 100).toFixed(1)}%</span>
          </div>

          <div className="w-full bg-[#EFE6DD] h-3 rounded-full">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-[#2F855A] via-[#FBD38D] to-[#ED8936]"
              style={{ width: `${score * 100}%` }}
            />
          </div>
        </div>

        {/* 🔥 PHQ-9 SCORE */}
        <div className="bg-[#F5EFE6] p-5 rounded-xl max-w-md mx-auto">
          <p className="text-sm text-[#7B5E57] mb-1">
            PHQ-9 Score
          </p>

          <p className="text-3xl font-semibold text-[#5C4033]">
            {phqScore} / 27
          </p>

          <p className="text-sm text-[#2F855A] mt-1">
            {getSeverity(phqScore)}
          </p>
        </div>

        {/* Signals */}
        <div>
          <p className="text-sm text-[#7B5E57] mb-3">
            Detected Signals
          </p>

          {cues.length > 0 ? (
            <div className="flex flex-wrap justify-center gap-2">
              {cues.map((cue, i) => (
                <span
                  key={i}
                  className="px-3 py-1 text-xs rounded-full bg-[#EFE6DD] text-[#5C4033]"
                >
                  {cue}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#A1887F]">
              No strong signals detected
            </p>
          )}
        </div>

        {/* Reset */}
        <button
          onClick={handleReset}
          className="px-6 py-2 rounded-lg bg-[#2F855A] text-white hover:opacity-90"
        >
          Analyze Again
        </button>

      </div>
    );
  }

  // ✍️ INPUT VIEW
  return (
    <div className="space-y-5">

      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        placeholder="Tell us how you feel..."
        className="w-full min-h-[120px] p-4 rounded-2xl bg-[#FFF8F0] border border-[#E5D3C5] focus:ring-2 focus:ring-[#2F855A] resize-none transition-all duration-150"
      />

      {error && <p className="text-sm text-red-500">{error}</p>}

      <PHQ9Form phq9={phq9} setPhq9={setPhq9} />

      <button
        onClick={handlePredict}
        disabled={loading}
        className={`w-full py-3 rounded-xl text-white font-medium ${
          loading
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-[#2F855A] hover:opacity-90 cursor-pointer"
        }`}
      >
        {loading ? "Analyzing..." : "Analyze with PHQ-9"}
      </button>

    </div>
  );
}