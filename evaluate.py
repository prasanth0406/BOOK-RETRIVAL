"""
Compares TF-IDF and BM25 ranking using Precision@k over a set of test queries.

Relevance is approximated with a keyword rule per query (a book counts as
relevant if its title, description, or genre tags contain at least one
keyword). For a stronger report, replace this with hand-labeled relevance
judgments.

Run: python3 evaluate.py
"""
from retrieval import BookSearchEngine

engine = BookSearchEngine("data/books.csv")

TEST_QUERIES = {
    "orphan boy discovers he is a wizard":     ["orphan", "wizard", "magic", "hogwarts", "harry potter"],
    "detective investigates a murder":         ["murder", "detective", "investigat", "mystery", "crime"],
    "two people fall in love":                 ["love", "romance"],
    "soldiers fighting in a war":              ["war", "soldier", "battle", "army"],
    "haunted house ghost story":               ["haunt", "house", "horror", "ghost"],
    "spaceship travels to another planet":     ["space", "planet", "ship", "alien", "galaxy"],
}


def is_relevant(book, keywords):
    text = f"{book['title']} {book['description']} {book['genres']}".lower()
    return any(kw in text for kw in keywords)


def precision_at_k(query, keywords, model, k=10):
    results = engine.search(query, model=model, top_k=k)
    if not results:
        return 0.0
    relevant = sum(1 for r in results if is_relevant(r, keywords))
    return relevant / len(results)


def main():
    print(f"{'Query':40s} {'TF-IDF P@10':>12s} {'BM25 P@10':>12s}")
    print("-" * 66)
    tfidf_scores, bm25_scores = [], []
    for query, keywords in TEST_QUERIES.items():
        p_tfidf = precision_at_k(query, keywords, "tfidf", k=10)
        p_bm25 = precision_at_k(query, keywords, "bm25", k=10)
        tfidf_scores.append(p_tfidf)
        bm25_scores.append(p_bm25)
        print(f"{query:40s} {p_tfidf:12.2f} {p_bm25:12.2f}")

    print("-" * 66)
    print(f"{'Mean':40s} {sum(tfidf_scores)/len(tfidf_scores):12.2f} "
          f"{sum(bm25_scores)/len(bm25_scores):12.2f}")


if __name__ == "__main__":
    main()
