export default function Header({ mode, setMode }) {
  return (
    <header className="flex items-center justify-between px-12 py-4 bg-[#FFF8F0] border-b border-[#E5D3C5]">

      {/* LOGO */}
      <div className="flex items-center gap-4">
        <img
          src="/logo.png"
          alt="MindCare Logo"
          className="h-18 object-contain"
        />
      </div>

      {/* NAV */}
      <div className="flex gap-12">

        <button
          onClick={() => setMode("text")}
          className={`pb-2 text-xl font-semibold transition ${
            mode === "text"
              ? "text-[#ED8936] border-b-2 border-[#ED8936]"
              : "text-[#7B5E57] hover:text-[#5C4033]"
          }`}
        >
          Text Analysis
        </button>

        <button
          onClick={() => setMode("hybrid")}
          className={`pb-2 text-xl font-semibold transition ${
            mode === "hybrid"
              ? "text-[#2F855A] border-b-2 border-[#2F855A]"
              : "text-[#7B5E57] hover:text-[#5C4033]"
          }`}
        >
          Hybrid Analysis
        </button>

      </div>

      {/* SPACER */}
      <div className="w-[160px]" />

    </header>
  );
}