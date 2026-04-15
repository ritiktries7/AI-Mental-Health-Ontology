const phqQuestions = [
  'Little interest or pleasure in doing things',
  'Feeling down, depressed, or hopeless',
  'Trouble falling or staying asleep, or sleeping too much',
  'Feeling tired or having little energy',
  'Poor appetite or overeating',
  'Feeling bad about yourself',
  'Trouble concentrating on things',
  'Moving or speaking so slowly that others notice or being fidgety',
  'Thoughts that you would be better off dead or hurting yourself'
];

function buildPHQ() {
  const container = document.getElementById('phq9');
  phqQuestions.forEach((q, i) => {
    const div = document.createElement('div');
    div.className = 'phq-item';
    const label = document.createElement('label');
    label.textContent = `${i+1}. ${q}`;
    const select = document.createElement('select');
    select.id = `phq_${i}`;
    for (let v = 0; v <= 3; v++) {
      const opt = document.createElement('option');
      opt.value = v;
      opt.text = `${v}`;
      select.appendChild(opt);
    }
    div.appendChild(label);
    div.appendChild(select);
    container.appendChild(div);
  });
}

function getPHQValues() {
  const vals = [];
  for (let i = 0; i < 9; i++) {
    const v = parseInt(document.getElementById(`phq_${i}`).value || '0', 10);
    vals.push(v);
  }
  return vals;
}

async function callApi(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

function showResult(obj) {
  const pre = document.getElementById('result');
  pre.textContent = JSON.stringify(obj, null, 2);
}

window.addEventListener('DOMContentLoaded', () => {
  buildPHQ();
  const btnPredict = document.getElementById('btn-predict');
  const btnHybrid = document.getElementById('btn-hybrid');
  btnPredict.addEventListener('click', async () => {
    const text = document.getElementById('text').value || '';
    btnPredict.disabled = true;
    try {
      const data = await callApi('/predict', { text });
      showResult(data);
    } catch (e) {
      showResult({ error: e.message });
    } finally {
      btnPredict.disabled = false;
    }
  });

  btnHybrid.addEventListener('click', async () => {
    const text = document.getElementById('text').value || '';
    const phq = getPHQValues();
    btnHybrid.disabled = true;
    try {
      const data = await callApi('/hybrid_predict', { text, phq9: phq });
      showResult(data);
    } catch (e) {
      showResult({ error: e.message });
    } finally {
      btnHybrid.disabled = false;
    }
  });
});
