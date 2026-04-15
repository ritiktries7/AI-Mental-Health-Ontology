const questions = [
  "Little interest or pleasure in doing things",
  "Feeling down, depressed, or hopeless",
  "Trouble falling or staying asleep, or sleeping too much",
  "Feeling tired or having little energy",
  "Poor appetite or overeating",
  "Feeling bad about yourself",
  "Trouble concentrating on things",
  "Moving or speaking so slowly that others notice or being fidgety",
  "Thoughts that you would be better off dead or hurting yourself",
];

export default function PHQ9Form({ phq9, setPhq9 }) {
  const handleChange = (i, val) => {
    const updated = [...phq9];
    updated[i] = Number(val);
    setPhq9(updated);
  };

  return (
    <div className="grid gap-3">
      {questions.map((q, i) => (
        <div key={i} className="flex justify-between items-center bg-[#F5EFE6] p-3 rounded-xl">
          <span className="text-xl text-[#5C4033]">{q}</span>

          <select
            value={phq9[i]}
            onChange={(e) => handleChange(i, e.target.value)}
            className="border rounded px-2 py-1"
          >
            {[0,1,2,3].map(v => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}