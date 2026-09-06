const queryInput = document.getElementById("query");
const searchBtn = document.getElementById("search-btn");
const genreSel = document.getElementById("genre");
const minRatingSel = document.getElementById("min-rating");
const sortSel = document.getElementById("sort");
const resetBtn = document.getElementById("reset-btn");
const modelBtns = document.querySelectorAll(".model-btn");

const resultsGrid = document.getElementById("results-grid");
const resultsMeta = document.getElementById("results-meta");
const emptyState = document.getElementById("empty-state");
const heroHint = document.getElementById("hero-hint");
const legendList = document.getElementById("legend-list");
const similarBanner = document.getElementById("similar-banner");
const similarBannerText = document.getElementById("similar-banner-text");
const clearSimilarBtn = document.getElementById("clear-similar");

const GENRE_COLORS = window.GENRE_COLORS || {};
const FALLBACK_COLOR = "#5B6472";

let currentModel = "tfidf";
let debounceTimer = null;
let similarModeBookTitle = null;

function primaryGenre(genresStr) {
  const first = (genresStr || "").split(",")[0].trim();
  return first;
}

function shortGenres(genresStr, maxTags = 3) {
  const tags = (genresStr || "").split(",").map(g => g.trim()).filter(Boolean);
  return tags.slice(0, maxTags).join(", ");
}

function truncate(str, maxLen = 220) {
  if (!str || str.length <= maxLen) return str || "";
  return str.slice(0, maxLen).replace(/\s+\S*$/, "") + "\u2026";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function renderLegend() {
  legendList.innerHTML = Object.entries(GENRE_COLORS).map(([g, color]) => `
    <div class="legend-item">
      <span class="legend-swatch" style="background:${color}"></span>${g}
    </div>`).join("");
}

function buildParams() {
  const params = new URLSearchParams();
  params.set("q", queryInput.value.trim());
  params.set("model", currentModel);
  params.set("genre", genreSel.value);
  if (minRatingSel.value) params.set("min_rating", minRatingSel.value);
  params.set("sort", sortSel.value);
  return params;
}

function cardHTML(book, hasQuery) {
  const matchPct = Math.round(book.score * 100);
  const genre = primaryGenre(book.genres);
  const color = GENRE_COLORS[genre] || FALLBACK_COLOR;

  const matchBlock = hasQuery ? `
    <div class="match-meter">
      <div class="match-label"><span>Match (${currentModel.toUpperCase()})</span><span>${matchPct}%</span></div>
      <div class="match-track"><div class="match-fill" style="width:${matchPct}%"></div></div>
    </div>` : "";

  return `
    <div class="card" style="--shelf-color:${color}">
      <div class="card-genres">${escapeHtml(shortGenres(book.genres))}</div>
      <h3 class="card-title">${escapeHtml(book.title)}</h3>
      <p class="card-author">by ${escapeHtml(book.author)}</p>
      <hr class="card-rule">
      <p class="card-desc">${escapeHtml(truncate(book.description))}</p>
      <div class="card-bottom">
        <span class="card-rating"><span class="star">&#9733;</span> ${book.avg_rating.toFixed(2)} (${book.num_ratings.toLocaleString("en-IN")})</span>
        <button class="similar-link" data-book-id="${book.bookId}" data-book-title="${escapeHtml(book.title)}">More like this &rarr;</button>
      </div>
      ${matchBlock}
    </div>`;
}

function renderResults(results, hasQuery, metaText, hintText) {
  if (results.length === 0) {
    resultsGrid.innerHTML = "";
    emptyState.hidden = false;
    resultsMeta.textContent = "0 results";
    return;
  }
  emptyState.hidden = true;
  resultsMeta.textContent = metaText;
  heroHint.textContent = hintText;
  resultsGrid.innerHTML = results.map(b => cardHTML(b, hasQuery)).join("");

  resultsGrid.querySelectorAll(".similar-link").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.bookId;
      const title = btn.dataset.bookTitle;
      loadSimilar(id, title);
    });
  });
}

async function runSearch() {
  similarModeBookTitle = null;
  similarBanner.hidden = true;

  const params = buildParams();
  resultsMeta.textContent = "Searching\u2026";

  const res = await fetch(`/api/search?${params.toString()}`);
  const data = await res.json();
  const hasQuery = queryInput.value.trim().length > 0;

  const metaText = hasQuery
    ? `${data.count} result${data.count === 1 ? "" : "s"} ranked by ${currentModel.toUpperCase()} for "${queryInput.value.trim()}"`
    : `${data.count} books in catalog`;
  const hintText = hasQuery
    ? `Ranking with ${currentModel === "bm25" ? "BM25 (term-frequency saturation + length normalization)" : "TF-IDF cosine similarity"}.`
    : "Showing all books. Start typing to rank by relevance.";

  renderResults(data.results, hasQuery, metaText, hintText);
}

async function loadSimilar(bookId, title) {
  resultsMeta.textContent = "Finding similar books\u2026";
  const res = await fetch(`/api/similar/${bookId}`);
  const data = await res.json();

  similarModeBookTitle = title;
  similarBanner.hidden = false;
  similarBannerText.textContent = `Showing books similar to "${title}"`;

  const metaText = `${data.count} similar book${data.count === 1 ? "" : "s"} found`;
  const hintText = "Similarity computed via cosine distance between TF-IDF vectors.";
  renderResults(data.results, true, metaText, hintText);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runSearch, 300);
}

queryInput.addEventListener("input", debouncedSearch);
searchBtn.addEventListener("click", runSearch);
queryInput.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
genreSel.addEventListener("change", runSearch);
minRatingSel.addEventListener("change", runSearch);
sortSel.addEventListener("change", runSearch);

modelBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    modelBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentModel = btn.dataset.model;
    runSearch();
  });
});

clearSimilarBtn.addEventListener("click", () => {
  similarBanner.hidden = true;
  runSearch();
});

resetBtn.addEventListener("click", () => {
  queryInput.value = "";
  genreSel.value = "All";
  minRatingSel.value = "";
  sortSel.value = "relevance";
  similarBanner.hidden = true;
  runSearch();
});

renderLegend();
runSearch();
