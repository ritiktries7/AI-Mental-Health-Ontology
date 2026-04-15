"""
Depression-AI — Fixed Training Pipeline
========================================

Root cause of wrong predictions (diagnosed):
  The original dataset's label=0 class is Sentiment140 *Twitter* data,
  not genuine Reddit non-depression posts. The model therefore learned
  platform style (lol / omg / haha / twitter → not depressed) rather
  than actual depression signals. On real user input it fails badly.

Fixes applied:
  1. Drop Twitter-pattern rows (URLs, platform vocab)
  2. Stricter length filter per class (label=0 ≥20 words, label=1 ≥15 words)
  3. Block Twitter-leak vocab at preprocessing time (lol/omg/haha/tweet)
  4. TF-IDF with bigrams — captures 'feel empty', 'cant sleep', 'want die'
  5. class_weight='balanced' — handles remaining class imbalance
  6. Regularisation C tuned on held-out val set
  7. 80/10/10 stratified train/val/test split
  8. Reports precision/recall/F1, not just accuracy
  9. Depression recall highlighted — missing real cases is worst outcome

NOTE on data quality:
  Even after filtering, label=0 still contains Twitter lifestyle tweets.
  For production: replace label=0 with real Reddit non-depression posts
  (r/CasualConversation, r/AskReddit, r/happy). This script does the
  best possible with the current dataset.

Usage:
  python main.py --train
  python main.py --predict "I feel so alone and empty inside"
  python main.py --train --csv data/reddit.csv
"""

import argparse
import os
import re
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, recall_score
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# Twitter-origin artefact words — model was learning these as non-depression
# signals rather than genuine language patterns. Blocking them at preprocess
# time forces the model to learn content, not platform.
TWITTER_LEAK_WORDS = {
    'lol', 'omg', 'haha', 'hahaha', 'tweet', 'tweeted', 'retweet',
    'quot', 'dm', 'rt', 'iphone', 'ipod', 'myspace', 'twitterpated',
}

MIN_WORDS_CLASS0 = 20   # label=0 (non-depression): stricter — most Twitter noise is short
MIN_WORDS_CLASS1 = 15   # label=1 (depression): slightly looser

_URL_RE       = re.compile(r'http\S+|www\.\S+', re.IGNORECASE)
_TWITTER_ORIG = re.compile(r'http|twitpic|twitter\.com|facebook\.com|myspace', re.IGNORECASE)
_NON_ALPHA    = re.compile(r'[^a-z0-9\s]')
_WS           = re.compile(r'\s+')


# ---------------------------------------------------------------------------
# 1.  PREPROCESSING
# ---------------------------------------------------------------------------

def preprocess(text: str) -> str:
    """Lowercase, strip URLs, remove punctuation, collapse whitespace."""
    text = str(text).lower().strip()
    text = _URL_RE.sub('', text)
    text = _NON_ALPHA.sub(' ', text)
    text = _WS.sub(' ', text).strip()
    return text


def block_twitter_leak(text: str) -> str:
    """Remove known Twitter-artefact tokens so platform style is not a feature."""
    return ' '.join(t for t in text.split() if t not in TWITTER_LEAK_WORDS)


def full_preprocess(text: str) -> str:
    return block_twitter_leak(preprocess(text))


# ---------------------------------------------------------------------------
# 2.  DATA LOADING & CLEANING
# ---------------------------------------------------------------------------

def load_and_clean(csv_path: str) -> pd.DataFrame:
    """Load CSV, remove noise rows, apply preprocessing."""
    print(f"[data] Loading: {csv_path}")
    df = pd.read_csv(csv_path)

    required = {'clean_text', 'is_depression'}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required}")

    n_original = len(df)
    df = df.dropna(subset=['clean_text']).copy()

    # Remove rows that originated from Twitter (URL patterns, platform names)
    twitter_mask = df['clean_text'].str.contains(_TWITTER_ORIG, na=False)
    n_twitter    = twitter_mask.sum()
    df = df[~twitter_mask].copy()

    # Per-class length filter
    df['wc'] = df['clean_text'].str.split().str.len()
    n_before = len(df)
    mask_keep = (
        ((df['is_depression'] == 0) & (df['wc'] >= MIN_WORDS_CLASS0)) |
        ((df['is_depression'] == 1) & (df['wc'] >= MIN_WORDS_CLASS1))
    )
    df = df[mask_keep].drop(columns='wc').copy()
    n_short = n_before - len(df)

    # Preprocess text + block Twitter leak vocab
    df['clean_text'] = df['clean_text'].apply(full_preprocess)
    df = df[df['clean_text'].str.len() > 0].copy()

    print(f"[data] {n_original} rows  →  {len(df)} kept")
    print(f"[data]   removed {n_twitter} Twitter-origin rows")
    print(f"[data]   removed {n_short} short/noise rows")
    print(f"[data] Label distribution:\n{df['is_depression'].value_counts().to_string()}")

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3.  TRAINING
# ---------------------------------------------------------------------------

def train_and_save(csv_path: str, model_path: str, vect_path: str) -> None:
    """Train model, evaluate on held-out test set, save to disk."""
    df    = load_and_clean(csv_path)
    X_all = df['clean_text'].values
    y_all = df['is_depression'].values

    # ── 80 / 10 / 10 stratified split ──────────────────────────────────────
    X_tv, X_test, y_tv, y_test = train_test_split(
        X_all, y_all, test_size=0.10, stratify=y_all, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=0.111, stratify=y_tv, random_state=42
    )
    print(f"\n[split] train={len(X_train)} | val={len(X_val)} | test={len(X_test)}")

    # ── TF-IDF vectoriser ──────────────────────────────────────────────────
    print("[train] Fitting TF-IDF vectorizer (unigrams + bigrams)...")
    vectorizer = TfidfVectorizer(
        max_features=30_000,
        ngram_range=(1, 2),      # bigrams capture 'feel empty', 'cant sleep', 'want die'
        min_df=2,                # drop terms appearing in only 1 document
        sublinear_tf=True,       # log-scale TF — handles long Reddit posts better
        stop_words='english',
    )
    X_train_v = vectorizer.fit_transform(X_train)
    X_val_v   = vectorizer.transform(X_val)
    X_test_v  = vectorizer.transform(X_test)

    # ── Tune C on val set ──────────────────────────────────────────────────
    print("[train] Tuning regularisation C on val set...")
    best_c, best_f1 = 1.0, 0.0
    for c in [0.1, 0.3, 0.5, 1.0, 2.0, 5.0]:
        m = LogisticRegression(C=c, max_iter=1000,
                               class_weight='balanced', random_state=42)
        m.fit(X_train_v, y_train)
        f1 = f1_score(y_val, m.predict(X_val_v), average='macro')
        print(f"  C={c:<5}  val macro-F1={f1:.4f}")
        if f1 > best_f1:
            best_f1, best_c = f1, c

    print(f"\n[train] Best C={best_c}  (val macro-F1={best_f1:.4f})")

    # ── Final model on train + val ─────────────────────────────────────────
    print("[train] Re-training on train+val with best C...")
    X_tv_v = vectorizer.transform(np.concatenate([X_train, X_val]))
    model  = LogisticRegression(C=best_c, max_iter=1000,
                                 class_weight='balanced', random_state=42)
    model.fit(X_tv_v, np.concatenate([y_train, y_val]))

    # ── Test set evaluation ────────────────────────────────────────────────
    y_pred     = model.predict(X_test_v)
    dep_recall = recall_score(y_test, y_pred, pos_label=1)

    print("\n" + "=" * 58)
    print("TEST SET RESULTS  (held-out, never seen during training)")
    print("=" * 58)
    print(classification_report(
        y_test, y_pred,
        target_names=['no depression', 'depression']
    ))
    status = "GOOD" if dep_recall >= 0.85 else "NEEDS IMPROVEMENT"
    print(f"Depression recall: {dep_recall:.3f}  [{status}]")
    print("(recall = fraction of real depression cases we catch)")
    print("=" * 58)

    _print_top_features(model, vectorizer)

    # ── Save ──────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(os.path.dirname(vect_path),  exist_ok=True)
    joblib.dump(model,      model_path)
    joblib.dump(vectorizer, vect_path)
    print(f"\n[save] Model      → {model_path}")
    print(f"[save] Vectorizer → {vect_path}")

    _probe_real_sentences(model, vectorizer)


def _print_top_features(model, vectorizer, n: int = 15) -> None:
    feat = np.array(vectorizer.get_feature_names_out())
    coef = model.coef_[0]
    print("\n[features] Top depression indicators:")
    print(" ", list(feat[np.argsort(coef)[-n:][::-1]]))
    print("[features] Top non-depression indicators:")
    print(" ", list(feat[np.argsort(coef)[:n]]))


def _probe_real_sentences(model, vectorizer) -> None:
    """Hand-crafted sentences — the real test that matters for production."""
    probes = [
        ("i feel so alone nobody understands me",                       1),
        ("cant sleep again everything feels pointless",                 1),
        ("i dont want to wake up tomorrow",                             1),
        ("i have been feeling really down lately cant get out of bed",  1),
        ("i cry every night and i dont even know why anymore",          1),
        ("today was a great day went hiking with friends",              0),
        ("just finished a project feeling really accomplished",         0),
        ("went to the gym this morning feeling good",                   0),
        ("had a nice dinner with family tonight",                       0),
        ("really enjoying this book i started reading",                 0),
    ]
    texts  = [full_preprocess(t) for t, _ in probes]
    truths = [l for _, l in probes]
    X      = vectorizer.transform(texts)
    preds  = model.predict(X)
    probs  = model.predict_proba(X)

    print("\n[probe] Real-sentence sanity check:")
    correct = 0
    for (raw, true), pred, prob in zip(probes, preds, probs):
        ok     = pred == true
        status = "OK   " if ok else "WRONG"
        label  = "depression" if pred == 1 else "no-dep    "
        correct += int(ok)
        print(f"  [{status}] {label} ({max(prob):.2f}) | {raw[:58]}")

    print(f"\n  Probe: {correct}/{len(probes)} correct")
    if correct < 8:
        print("\n  To improve further:")
        print("  - Replace label=0 data with real Reddit non-depression posts")
        print("  - Use MentalBERT instead of TF-IDF for much better semantics")
        print("    pip install transformers torch")
        print("    model: 'mental/mental-bert-base-uncased'")


# ---------------------------------------------------------------------------
# 4.  INFERENCE
# ---------------------------------------------------------------------------

def load_model_and_vectorizer(model_path: str, vect_path: str):
    if not os.path.exists(model_path) or not os.path.exists(vect_path):
        raise FileNotFoundError(
            "Model or vectorizer not found — run with --train first."
        )
    return joblib.load(model_path), joblib.load(vect_path)


def predict_texts(model, vectorizer, texts: List[str]) -> Tuple[List, List]:
    """Predict labels and return probabilities for raw input strings."""
    cleaned = [full_preprocess(t) if t else "" for t in texts]
    X       = vectorizer.transform(cleaned)
    return model.predict(X), model.predict_proba(X)


# ---------------------------------------------------------------------------
# 5.  CLI
# ---------------------------------------------------------------------------

def _default_paths(base_dir: str):
    model_dir = os.path.join(base_dir, 'model')
    return (
        os.path.join(base_dir, 'data', 'reddit.csv'),
        os.path.join(model_dir, 'model.joblib'),
        os.path.join(model_dir, 'vectorizer.joblib'),
    )


def main():
    repo_base = os.path.dirname(os.path.abspath(__file__))
    csv_default, model_default, vect_default = _default_paths(repo_base)

    parser = argparse.ArgumentParser(description='Depression-AI — fixed pipeline')
    parser.add_argument('--train',      action='store_true',
                        help='Train and save model to disk')
    parser.add_argument('--csv',        default=csv_default,
                        help='Path to CSV dataset')
    parser.add_argument('--model-path', default=model_default,
                        help='Path to save/load model')
    parser.add_argument('--vect-path',  default=vect_default,
                        help='Path to save/load vectorizer')
    parser.add_argument('--predict',    nargs='*',
                        help='Text(s) to classify (wrap in quotes)')
    args = parser.parse_args()

    # Auto-train if model files are missing
    if args.train or not (os.path.exists(args.model_path)
                          and os.path.exists(args.vect_path)):
        train_and_save(args.csv, args.model_path, args.vect_path)

    model, vectorizer = load_model_and_vectorizer(args.model_path, args.vect_path)

    texts        = args.predict or ["I feel alone and tired all the time"]
    preds, probs = predict_texts(model, vectorizer, texts)

    print("\n--- Predictions ---")
    for t, p, pr in zip(texts, preds, probs):
        label = "depression" if p == 1 else "no depression"
        print(f"\nText       : {t}")
        print(f"Prediction : {label}  (confidence: {max(pr):.2f})")
        print(f"Raw probs  : no-dep={pr[0]:.3f}  dep={pr[1]:.3f}")


if __name__ == '__main__':
    main()