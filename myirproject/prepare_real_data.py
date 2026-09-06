"""
Cleans the real Goodreads export into data/books.csv, matching the schema
BookSearchEngine expects: bookId, title, author, description, genres,
avg_rating, num_ratings.

Fixes a real data-quality issue found in the raw file: Goodreads' full
29-item genre navigation menu is duplicated and prepended to the `genres`
field on every row, ahead of the book's actual genre tags, e.g.:

    "Art,Biography,...,Young Adult,Art,Biography,...,Young Adult,Fantasy,Magic,..."
     \\_______________ 29-item master list, TWICE _______________/  \\_ real tags _/

Left unfixed, every book would appear to belong to all 29 genres, which
would break genre filtering and the genre legend entirely.

Run: python3 prepare_real_data.py path/to/Goodreadss_Books.csv
"""
import sys
import pandas as pd

MASTER_GENRE_LIST = [
    "Art", "Biography", "Business", "Children's", "Christian", "Classics",
    "Comics", "Cookbooks", "Ebooks", "Fantasy", "Fiction", "Graphic Novels",
    "Historical Fiction", "History", "Horror", "Memoir", "Music", "Mystery",
    "Nonfiction", "Poetry", "Psychology", "Romance", "Science",
    "Science Fiction", "Self Help", "Sports", "Thriller", "Travel",
    "Young Adult",
]
M = len(MASTER_GENRE_LIST)


def clean_genres(raw):
    """Strip the duplicated 29-item master list prefix, dedupe remaining
    tags (preserving order), and rejoin as a clean comma-separated string."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    parts = [p.strip() for p in raw.split(",")]

    if len(parts) >= 2 * M and parts[:M] == MASTER_GENRE_LIST and parts[M:2 * M] == MASTER_GENRE_LIST:
        real_tags = parts[2 * M:]
    else:
        # doesn't match the known pattern -- leave as-is rather than guess
        real_tags = parts

    seen = set()
    deduped = []
    for tag in real_tags:
        if tag and tag not in seen:
            seen.add(tag)
            deduped.append(tag)
    return ", ".join(deduped)


def main(src_path):
    df = pd.read_csv(src_path)
    print("Raw shape:", df.shape)

    books = df[["bookId", "title", "author", "description",
                "genres", "avg_rating", "num_ratings"]].copy()

    before = len(books)
    books = books.drop_duplicates(subset="bookId")
    books = books.dropna(subset=["title"])
    print(f"Dropped {before - len(books)} rows (duplicate bookId / missing title)")

    books["description"] = books["description"].fillna("")
    books["author"] = books["author"].fillna("Unknown")
    books["avg_rating"] = books["avg_rating"].fillna(books["avg_rating"].mean())
    books["num_ratings"] = books["num_ratings"].fillna(0).astype(int)

    books["genres"] = books["genres"].fillna("").apply(clean_genres)
    n_no_genre = (books["genres"] == "").sum()
    books.loc[books["genres"] == "", "genres"] = "Uncategorized"
    print(f"{n_no_genre} books had no real genre tags -> labeled 'Uncategorized'")

    # drop books with no description at all -- nothing for TF-IDF/BM25 to index
    before = len(books)
    books = books[books["description"].str.strip() != ""]
    print(f"Dropped {before - len(books)} rows with empty description")

    books.to_csv("data/books.csv", index=False)
    print("Saved cleaned dataset:", books.shape, "-> data/books.csv")

    print("\nSample genre cleaning (before -> after) on first 3 rows:")
    for i in range(3):
        print(" before:", df["genres"].iloc[i][:70], "...")
        print(" after :", books["genres"].iloc[i] if i < len(books) else "(dropped)")
        print()


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/Goodreadss_Books_raw.csv"
    main(src)
