export default function ResultPanel({ result }) {

  // 🔹 EMPTY STATE
  if (!result) {
    return (
      <div className="text-center text-[#A1887F]">
        <h3 className="text-lg mb-2">Your Result</h3>
        <p className="text-sm">
          Enter text on the left to see analysis
        </p>
      </div>
    );
  }

  // ✅ DIRECT FROM BACKEND
  const risk = result.combined_risk;
  const score = result.combined_score;
  const cues = result?.ontology_explanation?.text_cues ?? [];

  return (
    <div className="text-center space-y-6 w-full max-w-md">

      {/* TITLE */}
      <h2 className="text-2xl font-semibold text-[#5C4033]">
        Analysis Result
      </h2>

      {/* 🔹 RISK */}
      <div className="text-3xl font-semibold text-[#2F855A]">
        {risk} Risk
      </div>

      {/* 🔹 AI SCORE */}
      <div>
        <div className="flex justify-between text-sm text-[#7B5E57] mb-2">
          <span>AI Score</span>
          <span>{(score * 100).toFixed(1)}%</span>
        </div>

        <div className="w-full bg-[#EFE6DD] h-3 rounded-full">
          <div
            className="h-3 rounded-full bg-[#2F855A]"
            style={{ width: `${score * 100}%` }}
          />
        </div>
      </div>

      {/* 🔥 PHQ-9 SCORE (ONLY FOR HYBRID) */}
      {result.phq_total !== undefined && (
        <div className="bg-[#F5EFE6] p-4 rounded-xl">
          <p className="text-md text-[#7B5E57]">
            PHQ-9 Score
          </p>

          <p className="text-2xl font-semibold text-[#5C4033]">
            {result.phq_total} / 27
          </p>

          <p className="text-md text-[#2F855A]">
            {result.phq_severity}
          </p>
        </div>
      )}

      {/* 🔹 TEXT CUES */}
      <div>
        <p className="text-md text-[#7B5E57] mb-2">
          Detected Signals
        </p>

        {cues.length > 0 ? (
          <div className="flex flex-wrap justify-center gap-2">
            {cues.map((cue, i) => (
              <span
                key={i}
                className="px-3 py-1 text-sm rounded-full bg-[#EFE6DD] text-[#5C4033]"
              >
                {cue}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xl text-[#A1887F]">
            No signals detected
          </p>
        )}
      </div>

    </div>
  );
}