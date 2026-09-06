"""
Core IR engine for the book retrieval website.

Pipeline:
    load CSV -> preprocess text (tokenize/stopword/lemmatize) -> build TF-IDF
    index AND a BM25 index over the same tokens -> query -> rank by chosen
    model -> filter (genre/rating) -> sort.
"""
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"]:
    try:
        nltk.data.find(pkg)
    except LookupError:
        nltk.download(pkg, quiet=True)

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()

# fixed, deterministic palette for genre shelf-marks (library card-catalog theme)
PALETTE = [
    "#2F6F62", "#3B6E91", "#6B4C6B", "#A14B5C", "#A2472B", "#B08B2E",
    "#6E8F53", "#5A2A2A", "#456A8C", "#7A5C8E", "#8C5A3C", "#4C7A6E",
    "#9C5B4A", "#5B6E3C",
]


def preprocess_text(text: str) -> list[str]:
    """Lowercase -> tokenize -> drop non-alphabetic/stopword tokens -> lemmatize."""
    text = str(text).lower()
    tokens = word_tokenize(text)
    filtered = [w for w in tokens if w.isalpha() and w not in STOP_WORDS]
    return [LEMMATIZER.lemmatize(w) for w in filtered]


class BookSearchEngine:
    """TF-IDF + BM25 retrieval engine over the book catalog."""

    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.df["description"] = self.df["description"].fillna("")
        self.df["genres"] = self.df["genres"].fillna("")
        self.df["author"] = self.df["author"].fillna("")

        # --- preprocessing (feeds BOTH indexes below) ---
        self.df["processed_description"] = self.df["description"].apply(preprocess_text)
        self.df["processed_title"] = self.df["title"].apply(preprocess_text)

        self.df["processed_text"] = self.df["processed_description"].apply(" ".join)
        title_text = self.df["processed_title"].apply(" ".join)
        # title counted twice -> matches there weigh more than body matches
        self.df["search_text"] = title_text + " " + title_text + " " + self.df["processed_text"]

        # --- TF-IDF index ---
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["search_text"])

        # --- BM25 index (same tokens, weighted title included twice too) ---
        self.bm25_corpus = [
            (row.processed_title * 2 + row.processed_description)
            for row in self.df.itertuples()
        ]
        self.bm25 = BM25Okapi(self.bm25_corpus)

    def genres(self, top_n: int = 50):
        """Most frequent genre tags in the catalog (there can be hundreds of
        distinct tags in real Goodreads data, so we cap the filter dropdown
        to the ones that are actually useful to filter by)."""
        counts = {}
        for g in self.df["genres"]:
            for part in str(g).split(","):
                part = part.strip()
                if part:
                    counts[part] = counts.get(part, 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:top_n]
        return sorted(name for name, _ in top)

    def genre_colors(self, top_n: int = 14):
        """Deterministic color assignment for the most common genres, used
        for the shelf-mark strip on cards and the sidebar legend. Deterministic
        (hash-free) so the mapping is identical across server restarts."""
        counts = {}
        for g in self.df["genres"]:
            for part in str(g).split(","):
                part = part.strip()
                if part:
                    counts[part] = counts.get(part, 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:top_n]
        return {name: PALETTE[i % len(PALETTE)] for i, (name, _) in enumerate(top)}

    def _score_tfidf(self, query_tokens):
        query_text = " ".join(query_tokens)
        query_vec = self.vectorizer.transform([query_text])
        return cosine_similarity(query_vec, self.tfidf_matrix).flatten()

    def _score_bm25(self, query_tokens):
        scores = self.bm25.get_scores(query_tokens)
        max_score = scores.max() if len(scores) and scores.max() > 0 else 1.0
        return scores / max_score  # normalize to 0-1 so the UI meter is comparable

    def search(self, query: str, model: str = "tfidf", genre: str = None,
               min_rating: float = None, sort_by: str = "relevance", top_k: int = 40):
        results = self.df.copy()
        query_tokens = preprocess_text(query) if query else []

        if query_tokens:
            if model == "bm25":
                scores = self._score_bm25(query_tokens)
            else:
                scores = self._score_tfidf(query_tokens)
            results["score"] = scores
            results = results[results["score"] > 0]
        else:
            results["score"] = 1.0

        if genre and genre != "All":
            results = results[results["genres"].str.contains(genre, case=False, na=False)]
        if min_rating is not None:
            results = results[results["avg_rating"] >= min_rating]

        if sort_by == "rating":
            results = results.sort_values("avg_rating", ascending=False)
        elif sort_by == "popularity":
            results = results.sort_values("num_ratings", ascending=False)
        else:  # relevance
            results = results.sort_values("score", ascending=False)

        results = results.head(top_k)
        return self._rows_to_dicts(results)

    def similar_to(self, book_id: int, top_k: int = 8):
        """Nearest neighbours of a given book in TF-IDF vector space."""
        idx_matches = self.df.index[self.df["bookId"] == book_id]
        if len(idx_matches) == 0:
            return []
        idx = idx_matches[0]
        sims = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
        sims[idx] = -1  # exclude the book itself
        top_idx = sims.argsort()[::-1][:top_k]
        results = self.df.iloc[top_idx].copy()
        results["score"] = sims[top_idx]
        results = results[results["score"] > 0]
        return self._rows_to_dicts(results)

    def _rows_to_dicts(self, results):
        out = []
        for _, row in results.iterrows():
            out.append({
                "bookId": int(row["bookId"]),
                "title": row["title"],
                "author": row["author"],
                "description": row["description"],
                "genres": row["genres"],
                "avg_rating": float(row["avg_rating"]),
                "num_ratings": int(row["num_ratings"]),
                "score": round(float(row["score"]), 4),
            })
        return out


if __name__ == "__main__":
    engine = BookSearchEngine("data/books.csv")
    print("TF-IDF matrix:", engine.tfidf_matrix.shape)
    print("\n--- TF-IDF: 'orphan discovers hidden magical power' ---")
    for r in engine.search("orphan discovers hidden magical power", model="tfidf", top_k=5):
        print(round(r["score"], 3), r["title"], "|", r["genres"])
    print("\n--- BM25: same query ---")
    for r in engine.search("orphan discovers hidden magical power", model="bm25", top_k=5):
        print(round(r["score"], 3), r["title"], "|", r["genres"])
