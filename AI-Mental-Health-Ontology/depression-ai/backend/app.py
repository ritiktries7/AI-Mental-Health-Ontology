from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import joblib
import importlib

try:
    owlready2 = importlib.import_module("owlready2")
except Exception:
    owlready2 = None


app = FastAPI(title="depression-ai API")

# Allow browser clients (e.g., Vite dev server) to call the API endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files so the UI is served by the same app.
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


class PredictRequest(BaseModel):
    text: str


class HybridRequest(BaseModel):
    text: Optional[str] = ""
    phq9: Optional[List[int]] = None  # list of 9 integers 0-3


def _model_paths():
    """Return absolute paths for model and vectorizer (resolved relative to repo root)."""
    repo_root = Path(__file__).resolve().parents[1]
    model_dir = repo_root / "model"
    return model_dir / "model.joblib", model_dir / "vectorizer.joblib"


def _ontology_path():
    repo_root = Path(__file__).resolve().parents[1]
    # Prefer user's provided ontology file if present, otherwise fallback to the simple one
    preferred = repo_root / "ontology" / "depression_mental_health_ontology.owl"
    fallback = repo_root / "ontology" / "depression_ontology.owl"
    if preferred.exists():
        print("Preferred is active")
        return preferred
    return fallback


@app.on_event("startup")
def load_model_and_ontology():
    """Load model, vectorizer and ontology once on startup and save them on app.state."""
    global owlready2

    # Re-attempt optional owlready2 import in case it was installed after process start.
    if owlready2 is None:
        try:
            owlready2 = importlib.import_module("owlready2")
        except Exception:
            owlready2 = None

    model_path, vect_path = _model_paths()
    try:
        app.state.model = joblib.load(model_path)
        app.state.vectorizer = joblib.load(vect_path)
        app.state.model_loaded = True
        app.state.model_error = None
    except Exception as e:
        app.state.model_loaded = False
        app.state.model_error = str(e)

    # Load ontology if possible. Prefer owlready2 but fall back to a local XML parse
    ont_path = _ontology_path()
    app.state.ontology = None
    app.state.ontology_labels = []
    if not ont_path.exists():
        app.state.ontology_loaded = False
        app.state.ontology_error = f"ontology file not found at {ont_path}"
        return

    if owlready2:
        try:
            # Try loading via owlready2 first
            try:
                app.state.ontology = owlready2.get_ontology(ont_path.resolve().as_uri()).load()
                app.state.ontology_loaded = True
                app.state.ontology_error = None
            except Exception:
                # Fall back to a world-based load (sometimes helps), then fallback to XML parse
                try:
                    world = owlready2.World()
                    app.state.ontology = world.get_ontology(ont_path.resolve().as_uri()).load()
                    app.state.ontology_loaded = True
                    app.state.ontology_error = None
                except Exception as e:
                    # Record the owlready2 error but attempt a lightweight XML parse
                    owl_err = str(e)
                    labels = _parse_owl_labels(ont_path)
                    if labels:
                        app.state.ontology_labels = labels
                        app.state.ontology_loaded = True
                        app.state.ontology_error = f"loaded via XML fallback (owlready2 error: {owl_err})"
                    else:
                        app.state.ontology_loaded = False
                        app.state.ontology_error = f"owlready2 load failed: {owl_err}"
        except Exception as e:
            app.state.ontology_loaded = False
            app.state.ontology_error = str(e)
    else:
        # owlready2 not installed: try a lightweight local parse so the service can still provide basic labels
        labels = _parse_owl_labels(ont_path)
        if labels:
            app.state.ontology_labels = labels
            app.state.ontology_loaded = True
            app.state.ontology_error = "loaded via XML fallback (owlready2 not installed)"
        else:
            app.state.ontology_loaded = False
            app.state.ontology_error = "owlready2 not installed and no ontology labels could be parsed"


def _parse_owl_labels(path: Path):
    """Lightweight XML parse to extract rdfs:label or owl:Class local names from the OWL file.
    This avoids network imports and gives a minimal set of class labels for explainability.
    Returns a list of labels (strings).
    """
    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse(str(path))
        root = tree.getroot()
        ns = {k: v for k, v in [
            ("owl", "http://www.w3.org/2002/07/owl#"),
            ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
            ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        ]}
        labels = []
        # Find rdfs:label elements
        for lbl in root.findall('.//{http://www.w3.org/2000/01/rdf-schema#}label'):
            if lbl.text:
                labels.append(lbl.text)

        # If no labels found, fall back to extracting owl:Class/@rdf:about or rdf:ID
        if not labels:
            for cls in root.findall('.//{http://www.w3.org/2002/07/owl#}Class'):
                about = cls.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about') or cls.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID')
                if about:
                    # Extract the local name from the URI
                    local_name = about.split('#')[-1].split('/')[-1]
                    labels.append(local_name)

        # Deduplicate and return
        return list(dict.fromkeys(labels))
    except Exception:
        return []


@app.get("/")
def read_root():
    # Serve the frontend index if available, otherwise return a JSON status
    index_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "ok", "message": "depression-ai API is running"}


@app.get("/health")
def health():
    loaded = getattr(app.state, "model_loaded", False)
    return {
        "model_loaded": loaded,
        "model_error": getattr(app.state, "model_error", None),
        "ontology_loaded": getattr(app.state, "ontology_loaded", False),
        "ontology_error": getattr(app.state, "ontology_error", None),
    }


@app.get("/version")
def version():
    return {"service": "depression-ai", "version": "0.1.0"}


@app.post("/reload_ontology")
def reload_ontology():
    """Endpoint to re-run ontology loading (useful after installing owlready2 or updating the ontology file)."""
    # Re-run the loading logic (this will also re-check model files but is cheap)
    load_model_and_ontology()
    return {
        "ontology_loaded": getattr(app.state, "ontology_loaded", False),
        "ontology_error": getattr(app.state, "ontology_error", None),
        "ontology_labels_count": len(getattr(app.state, "ontology_labels", [])),
    }


@app.get("/favicon.ico")
def favicon():
    # Return 204 if there's no favicon file to avoid 404 spam from browsers
    favicon_path = Path(__file__).resolve().parents[1] / "frontend" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    return ("", 204)


def phq9_score_and_severity(phq9: List[int]):
    """Compute PHQ-9 total score and severity label."""
    if phq9 is None or len(phq9) != 9:
        return None, None
    total = sum(int(min(max(0, int(x)), 3)) for x in phq9)
    if total <= 4:
        severity = "Minimal"
    elif total <= 9:
        severity = "Mild"
    elif total <= 14:
        severity = "Moderate"
    elif total <= 19:
        severity = "Moderately Severe"
    else:
        severity = "Severe"
    return total, severity


def ontology_explain(phq9: Optional[List[int]], text: str):
    """Create an ontology-based explanation combining fixed rules and dynamic ontology labels."""
    # Map PHQ-9 indices to meaningful symptom labels
    symptom_map = {
        0: "Loss of interest", 1: "Sadness", 2: "Sleep issues",
        3: "Fatigue", 4: "Appetite change", 5: "Low self-worth",
        6: "Concentration issues", 7: "Restlessness", 8: "Suicidal thoughts",
    }

    # Text cue mapping: substrings -> human-friendly symptom labels
    text_cue_map = {
        "suicid": "Suicidal thoughts", "suicide": "Suicidal thoughts",
        "tired": "Fatigue", "fatigue": "Fatigue",
        "sleep": "Sleep issues", "insomnia": "Sleep issues",
        "appetite": "Appetite change", "hungry": "Appetite change",
        "worthless": "Low self-worth", "alone": "Loneliness",
        "hopeless": "Hopelessness", "concentrat": "Concentration issues",
        "interest": "Loss of interest", "anhedonia": "Loss of interest",
    }

    explains = []
    if phq9:
        for i, val in enumerate(phq9):
            try:
                v = int(val)
            except Exception:
                continue
            if v and v > 0:
                item_label = symptom_map.get(i, f"phq{i+1}")
                explains.append({"item": item_label, "score": v})

    cues_set = set()
    txt = (text or "").lower()

    # 1. Hardcoded dictionary matching
    for key, label in text_cue_map.items():
        if key in txt:
            cues_set.add(label)

    # 2. Dynamic Ontology matching
    # Fetch dynamically loaded labels from app state
    ontology_labels = getattr(app.state, "ontology_labels", [])
    
    for label in ontology_labels:
        # Clean label to match standard text (e.g., "Loss_of_Interest" -> "loss of interest")
        clean_label = str(label).replace("_", " ").lower()
        if clean_label and clean_label in txt:
            # Add the nicely formatted label to the set
            cues_set.add(str(label).replace("_", " "))

    cues = sorted(cues_set)

    return {"phq_items": explains, "text_cues": cues}


@app.post("/predict")
def predict(req: PredictRequest):
    if not getattr(app.state, "model_loaded", False):
        raise HTTPException(status_code=503, detail=f"Model not loaded: {app.state.model_error}")

    text = req.text or ""
    vec = app.state.vectorizer.transform([text])
    prob = app.state.model.predict_proba(vec)[0][1]

    risk = "High" if prob > 0.6 else "Low"

    # Also provide ontology-based explanation for the free-text input
    try:
        ontology_result = ontology_explain(None, text)
    except Exception as e:
        ontology_result = {"error": f"ontology_explain error: {e}"}

    return {"text": text, "risk": risk, "score": float(prob), "ontology_explanation": ontology_result}


@app.post("/hybrid_predict")
def hybrid_predict(req: HybridRequest):
    # Ensure model loaded
    if not getattr(app.state, "model_loaded", False):
        raise HTTPException(status_code=503, detail=f"Model not loaded: {app.state.model_error}")

    text = req.text or ""
    phq9 = req.phq9

    # ML prediction
    vec = app.state.vectorizer.transform([text])
    ml_prob = float(app.state.model.predict_proba(vec)[0][1])

    # PHQ-9 rule-based
    phq_total, phq_severity = phq9_score_and_severity(phq9) if phq9 is not None else (None, None)

    # Combine results with a simple weighted formula
    # weight_ml = 0.6, weight_phq = 0.4 (phq normalized by 27)
    phq_norm = (phq_total / 27) if phq_total is not None else 0.0
    combined_score = 0.6 * ml_prob + 0.4 * phq_norm

    if combined_score >= 0.6:
        combined_risk = "High"
    elif combined_score >= 0.4:
        combined_risk = "Medium"
    else:
        combined_risk = "Low"

    # Ontology-based explanation
    ontology_result = ontology_explain(phq9, text)

    return {
        "text": text,
        "ml_probability": ml_prob,
        "phq_total": phq_total,
        "phq_severity": phq_severity,
        "combined_score": combined_score,
        "combined_risk": combined_risk,
        "ontology_explanation": ontology_result,
    }