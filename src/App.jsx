import { useState,useEffect } from "react";
import Header from "./components/Header";
import TextPrediction from "./components/TextPrediction";
import HybridPrediction from "./components/HybridPrediction";
import ResultPanel from "./components/ResultPanel";

export default function App() {
  const [mode, setMode] = useState("text");
  const [result, setResult] = useState(null);

   useEffect(() => {
    setResult(null);
  }, [mode]);
  return (
    <div className="h-screen flex flex-col relative">


      <Header mode={mode} setMode={setMode} />

      {/* MAIN SPLIT */}
      <div className="flex flex-1 px-10 py-8 gap-8">

        {/* LEFT SIDE */}
        <div className="flex-1 flex items-center justify-center">
          <div className="w-full ">
            {mode === "text" ? (
              <TextPrediction setResult={setResult} />
            ) : (
              <HybridPrediction setResult={setResult} />
            )}
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div className="flex-1 flex items-center justify-center bg-[#e5d3c54b] border border-[#E5D3C5] rounded-3xl">

          <ResultPanel result={result} />

        </div>

      </div>
    </div>
  );
}