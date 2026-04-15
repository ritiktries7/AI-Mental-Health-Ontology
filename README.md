# 🧠 MindCare AI -- Mental Health Analysis System

MindCare AI is a web-based application that analyzes mental health
using: - 📝 Text-based AI prediction - 📊 PHQ-9 questionnaire scoring -
🔗 Hybrid analysis combining both

It helps identify emotional signals, risk levels, and depression
severity.

------------------------------------------------------------------------

## 🚀 Features

### 🔹 1. Text Analysis

-   Enter your thoughts
-   AI predicts:
    -   Risk level (Low / Medium / High)
    -   Confidence score
    -   Emotional cues (e.g., fatigue, sadness)

### 🔹 2. Hybrid Analysis (Text + PHQ-9)

-   Combines:
    -   AI text prediction
    -   PHQ-9 questionnaire
-   Provides:
    -   Combined risk score
    -   PHQ-9 total score (0--27)
    -   Severity (Minimal → Severe)
    -   Detected signals

### 🔹 3. Clean UI/UX

-   Modern responsive design
-   Side-by-side layout (Input + Result)
-   Auto-resizing text input
-   Calm healthcare-focused theme

------------------------------------------------------------------------

## 🖥️ Tech Stack

Frontend: - React (Vite) - Tailwind CSS

Backend: - FastAPI (Python) - Machine Learning model - Ontology-based
explanation system

------------------------------------------------------------------------

## ⚙️ Installation & Setup

### Clone the repository

git clone https://github.com/ritiktries7/AI-Mental-Health-Ontology.git

### Install dependencies

npm install

### Run the app

npm run dev

------------------------------------------------------------------------

## 📊 Example API Response

{ "combined_risk": "High", "combined_score": 0.60, "phq_total": 27,
"phq_severity": "Severe", "ontology_explanation": { "text_cues":
\["Fatigue"\] } }

------------------------------------------------------------------------

## ⚠️ Disclaimer

This tool is for educational purposes only and not a medical diagnosis.

------------------------------------------------------------------------

## 👨‍💻 Author

Chirag
