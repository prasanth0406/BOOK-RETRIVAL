from flask import Flask, render_template, request, jsonify
from retrieval import BookSearchEngine

app = Flask(__name__)
engine = BookSearchEngine("data/books.csv")


@app.route("/")
def index():
    return render_template(
        "index.html",
        genres=engine.genres(),
        genre_colors=engine.genre_colors(),
        book_count=len(engine.df),
    )


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    model = request.args.get("model", "tfidf")
    genre = request.args.get("genre", "All")
    min_rating = request.args.get("min_rating", type=float)
    sort_by = request.args.get("sort", "relevance")

    results = engine.search(
        query=query, model=model, genre=genre,
        min_rating=min_rating, sort_by=sort_by, top_k=40,
    )
    return jsonify({"count": len(results), "results": results})


@app.route("/api/similar/<int:book_id>")
def api_similar(book_id):
    results = engine.similar_to(book_id, top_k=6)
    return jsonify({"count": len(results), "results": results})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
