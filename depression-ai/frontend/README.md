This is a minimal static frontend for the depression-ai project.

Usage:
1. Start the backend API (from project root):

   uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000

2. Open the UI in a browser:

   http://127.0.0.1:8000/

The UI calls `/predict` for ML-only and `/hybrid_predict` for ML + PHQ-9 based predictions.
