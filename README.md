# Stacks — Book Retrieval System

A book search website: describe a book vaguely ("orphan boy discovers he is
a wizard") and it retrieves the closest matches — ranked by relevance, not
exact keyword match — with genre/rating filters, a **TF-IDF vs BM25**
ranking toggle, and a "more like this" nearest-neighbor lookup.

**This version runs on your real Goodreads dataset** (17,267 books, after
cleaning) — see the data quality note below.

## ⚠️ Data quality issue found & fixed: the `genres` column bug

Your raw `Goodreadss_Books.csv` has a real bug: Goodreads' full 29-item
genre navigation menu is **duplicated and prepended** to the `genres` field
on *every single row*, before the book's actual genre tags:

```
Art,Biography,Business,...,Young Adult,   <- 29-item master list
Art,Biography,Business,...,Young Adult,   <- same list again
Fantasy,Young Adult,Fiction,Magic,...     <- the book's REAL tags
```

Left unfixed, every book would appear to belong to all 29 categories, which
would break genre filtering completely (every filter would match almost
every book) and make the "primary genre" shown on each card meaningless
(it would always be "Art", since that's first in the master list).

`prepare_real_data.py` detects and strips this duplicated prefix, dedupes
the real tags, and labels the ~4,500 books that have no real tags left over
as `"Uncategorized"` rather than dropping them. This is exactly the kind of
thing worth screenshotting for your report — finding and explaining a real
bug in scraped data is a stronger EDA story than "the data was clean."

## How it works (pipeline)

1. **Corpus**: `data/books.csv` — your real Goodreads catalog, cleaned down
   from 20,068 to **17,267 books** (dropped: duplicate `bookId`s, missing
   titles, and rows with no description at all — nothing for TF-IDF/BM25 to
   index).
2. **Preprocessing** (`retrieval.py -> preprocess_text`): lowercase, tokenize
   (NLTK `word_tokenize`), drop stopwords/non-alphabetic tokens, lemmatize.
3. **Indexing — two models, same preprocessed tokens**:
   - **TF-IDF**: scikit-learn `TfidfVectorizer` (title counted twice, so
     title matches outrank body-only matches).
   - **BM25**: `rank_bm25.BM25Okapi` over the same tokens — adds term-
     frequency saturation and document-length normalization on top of what
     plain TF-IDF does.
4. **Query processing**: query text goes through the same `preprocess_text`
   function before scoring.
5. **Ranking**: cosine similarity (TF-IDF) or BM25 score, chosen live via
   the toggle in the UI.
6. **Filtering**: genre (substring match) and minimum rating, applied after
   ranking. The genre dropdown shows the top 50 most common tags (there are
   835 distinct tags in the real data — most appear on only 1–2 books, so
   showing all of them wouldn't be a useful filter).
7. **Sorting**: relevance (default), rating, or most-rated.
8. **"More like this"**: cosine similarity between one book's TF-IDF vector
   and every other book's — nearest neighbors in vector space, no query
   text involved. (Try it on a Sherlock Holmes book — it correctly surfaces
   the other Sherlock Holmes volumes.)
9. **Evaluation** (`evaluate.py`): Precision@10 for TF-IDF vs BM25, on real
   data this time — **BM25 scores 0.98 mean P@10 vs. TF-IDF's 0.93** across
   the test queries, which is a genuinely interesting, reportable result
   (unlike the synthetic-data version where both models tied at a trivial
   ceiling).

## Project structure

```
book_search/
├── app.py                Flask backend: /api/search, /api/similar/<id>
├── retrieval.py           Core IR engine (preprocessing, TF-IDF + BM25, ranking)
├── prepare_real_data.py    Cleans a raw Goodreads CSV into data/books.csv
├── generate_data.py        (Fallback) generates a synthetic catalog instead
├── evaluate.py              TF-IDF vs BM25 Precision@10 comparison
├── data/books.csv            The cleaned, real book catalog (17,267 rows)
├── templates/index.html      Search UI
├── static/style.css          Styling
├── static/script.js          Frontend logic
└── requirements.txt
```

## Running it locally

```bash
pip install -r requirements.txt
python3 app.py
```

Then open **http://localhost:3000**. First load takes ~25-30 seconds while
the TF-IDF and BM25 indexes build over 17K books — that's a one-time cost
at server startup, not per search.

To re-clean the data from a fresh raw export (e.g. if you re-scrape or get
an updated CSV):
```bash
python3 prepare_real_data.py path/to/your_raw_export.csv
```

To run the TF-IDF vs BM25 evaluation:
```bash
python3 evaluate.py
```

## What's genuinely more advanced here than a basic TF-IDF project

- **A real, documented data-cleaning fix** (the genre master-list bug) —
  good material for the "data cleaning" section of your report.
- **Two ranking models, swappable live, with a real (non-trivial) evaluation
  gap between them** — most student IR projects stop at TF-IDF.
- **"More like this"** — a second, independent use of the same vector index
  (item-to-item similarity, not just query-to-item).
- **Preprocessing is verifiably wired into both indexes** — not a dead code
  path like in the original notebook.

## Ideas to push further (optional)

- Swap the keyword-based evaluation relevance rule for real hand-labeled
  judgments — you have real data now, so this is worth doing properly.
- Add a semantic embedding model (`sentence-transformers`) as a third
  ranking option, to directly address vocabulary mismatch (e.g. "wizard
  school" vs. "academy of magic") that TF-IDF/BM25 can't catch.
- Clean up the noisier genre tags further (e.g. some rows have Goodreads
  "listopia" page names mixed into the genre field, like "Goodreads'
  Transgender Books page" — worth a mention as a known data limitation).
- Deploy it (Render, Railway, or Streamlit Community Cloud) so you have a
  live link instead of just local `localhost`.
