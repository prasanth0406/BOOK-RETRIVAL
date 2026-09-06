"""
Generates a synthetic book catalog (data/books.csv) for the book retrieval
website. Built from templates so descriptions have real narrative content
for TF-IDF/BM25 to work with meaningfully.

Run: python3 generate_data.py
"""
import csv
import random

random.seed(7)

GENRES = {
    "Fantasy": {
        "settings": ["a kingdom on the edge of ruin", "a hidden magical school",
                     "an island where the sea remembers every secret", "a city built on the back of a sleeping dragon",
                     "a forest that shifts its paths after dark", "a court of feuding wizards"],
        "protagonists": ["an orphan boy discovers he has forgotten powers", "a stubborn princess refuses her arranged fate",
                          "a young apprentice is framed for a crime he didn't commit", "a thief steals something that isn't supposed to exist",
                          "a farm girl finds she is the last of an ancient bloodline", "a exiled prince returns to reclaim his throne"],
        "conflicts": ["a rising dark lord threatens to unmake the world", "an ancient prophecy begins to unfold",
                      "a war between rival magical houses breaks out", "a curse spreads through the land, turning people to stone",
                      "the old gods stir from their centuries-long sleep", "a rebellion against a tyrant king gathers strength"],
    },
    "Science Fiction": {
        "settings": ["a generation ship drifting between stars", "a colony on a dying Mars",
                     "a city where memories can be bought and sold", "a future Earth ruled by artificial intelligence",
                     "a space station on the edge of known space", "a virtual world indistinguishable from reality"],
        "protagonists": ["a rogue engineer uncovers a conspiracy", "a soldier wakes with no memory of the last decade",
                          "a scientist's cloning experiment goes wrong", "a hacker stumbles onto a government secret",
                          "a pilot is the only survivor of a doomed mission", "an AI begins to question its own programming"],
        "conflicts": ["humanity's last colony is running out of time", "a war between humans and machines escalates",
                      "first contact with an alien species turns hostile", "a plague engineered in a lab threatens all life",
                      "the fabric of reality itself starts to break down", "a corporation controls what people are allowed to remember"],
    },
    "Mystery": {
        "settings": ["a snowed-in manor house", "a small coastal town with old secrets",
                     "a locked-room in a university library", "a decaying seaside hotel out of season",
                     "a train crossing the country overnight", "a quiet suburb hiding a decades-old crime"],
        "protagonists": ["a retired detective is pulled back for one last case", "a journalist starts digging into a cold case",
                          "a young lawyer discovers her client isn't telling the truth", "an insurance investigator smells something wrong",
                          "a widow starts to suspect her husband's death wasn't an accident", "a rookie cop's first case turns out to be personal"],
        "conflicts": ["a body is found with no explanation", "a witness disappears before they can testify",
                      "the evidence keeps pointing to someone who couldn't have done it", "an old confession turns out to be a lie",
                      "someone is covering up a murder from twenty years ago", "the killer seems to be one step ahead of the investigation"],
    },
    "Romance": {
        "settings": ["a small vineyard town in autumn", "a bookshop that's about to close down",
                     "a wedding neither of them wanted to attend", "a research station over one long winter",
                     "a family inn during the busiest season", "a city they both left years ago"],
        "protagonists": ["a chef who's sworn off relationships", "two rival architects forced to share an office",
                          "a widow slowly opening her heart again", "childhood friends reunited after a decade apart",
                          "a workaholic lawyer who doesn't believe in love", "a musician hiding from her old life"],
        "conflicts": ["they're competing for the same promotion", "an old betrayal stands between them",
                      "one of them is about to move across the world", "their families have been feuding for years",
                      "a marriage of convenience slowly becomes real", "a second chance neither of them expected"],
    },
    "Thriller": {
        "settings": ["a city during a blackout", "an isolated cabin during a storm",
                     "a corporate headquarters after hours", "a cruise ship in international waters",
                     "a border town during an uneasy ceasefire", "an underground bunker built for a war that never came"],
        "protagonists": ["an off-duty agent stumbles onto a plot", "a whistleblower goes into hiding",
                          "a mother searches for her missing daughter", "a hostage negotiator gets a call that's personal",
                          "a former soldier is pulled back into old work", "a data analyst finds something she wasn't meant to see"],
        "conflicts": ["a countdown begins that no one can stop", "someone close to them isn't who they claimed to be",
                      "a conspiracy reaches the highest levels of government", "a bomb is hidden somewhere in the city",
                      "the only way out means trusting someone they shouldn't", "a decades-old cover-up starts to unravel"],
    },
    "Historical Fiction": {
        "settings": ["a besieged city in the final year of the war", "a plantation in the years before independence",
                     "a royal court on the brink of revolution", "a fishing village during a famine",
                     "an ocean liner crossing the Atlantic in 1912", "a resistance cell in occupied territory"],
        "protagonists": ["a young nurse tending to the wounded", "a soldier writing letters he may never send",
                          "a seamstress secretly aiding a resistance", "an immigrant family starting over with nothing",
                          "a scholar hiding banned books", "a servant who knows more than she lets on"],
        "conflicts": ["the war changes everything they believed in", "a forbidden love crosses class lines",
                      "a family secret threatens to come undone", "loyalty to country and to family come into conflict",
                      "survival means making an impossible choice", "the truth about the past finally comes out"],
    },
    "Young Adult": {
        "settings": ["a boarding school with a strange history", "a small town everyone is desperate to leave",
                     "a summer camp reunion after years apart", "a competition with everything on the line",
                     "the last year of high school before everything changes", "a road trip none of them planned for"],
        "protagonists": ["a shy artist finds her voice", "a star athlete hides an injury that could end everything",
                          "twins who've grown apart try to reconnect", "a new student trying to survive junior year",
                          "a group of unlikely friends thrown together", "a girl determined to prove everyone wrong about her"],
        "conflicts": ["a rumor threatens to destroy a friendship", "a first love collides with growing up",
                      "a family is falling apart and no one will talk about it", "a secret could get someone expelled",
                      "the pressure to be perfect starts to break someone", "a choice that will decide the rest of their life"],
    },
    "Horror": {
        "settings": ["a house that's stood empty for forty years", "a small town where no one ever seems to leave",
                     "an abandoned asylum on the edge of the woods", "a cabin deep in a forest with no signal",
                     "a hotel that changes layout after midnight", "a coastal town where the fog never lifts"],
        "protagonists": ["a family moves into a house with a history", "a group of friends break into a place they shouldn't",
                          "a woman starts hearing things that aren't there", "a paranormal investigator takes one case too many",
                          "a child insists someone else lives in the walls", "a writer researching a book he can't seem to finish"],
        "conflicts": ["something in the house doesn't want them to leave", "the town's history refuses to stay buried",
                      "each night, something gets a little closer", "no one believes her until it's too late",
                      "the past never really stayed in the past", "what they found wasn't meant to be disturbed"],
    },
}

AUTHORS = [
    "Elena Marsh", "Thomas Okafor", "Priya Raman", "James Whitfield", "Naomi Cole",
    "Daniel Reyes", "Fiona Blackwood", "Marcus Lindqvist", "Anika Verma", "Oliver Hart",
    "Sofia Bianchi", "Ethan Cross", "Ingrid Solberg", "Rahul Mehta", "Claire Dubois",
    "Gabriel Novak", "Yuki Tanaka", "Isabel Ortega", "Nathaniel Grey", "Amara Chukwu",
]

TITLE_TEMPLATES = [
    "The {adj} {noun}",
    "{noun} of {place}",
    "The Last {noun}",
    "A {adj} Kind of {noun2}",
    "The {noun} We Left Behind",
    "Where the {noun} Sleeps",
    "The {adj} Hour",
    "{place}'s {noun}",
]

ADJ = ["Silent", "Hidden", "Forgotten", "Broken", "Last", "Quiet", "Distant", "Burning",
       "Fractured", "Unspoken", "Lost", "Endless", "Crooked", "Pale", "Wandering"]
NOUN = ["Garden", "Kingdom", "Letter", "River", "Storm", "Promise", "Shore", "Winter",
        "Flame", "Harbor", "Song", "Door", "Star", "Road", "House"]
NOUN2 = ["Silence", "Truth", "Goodbye", "Love", "Escape", "Reckoning"]
PLACE = ["Ashford", "Meridian", "Blackwater", "Solenne", "Kestrel Bay", "Corvin",
         "Thornfield", "Elderglen", "Marrow", "Halveston"]


def make_title():
    template = random.choice(TITLE_TEMPLATES)
    return template.format(
        adj=random.choice(ADJ), noun=random.choice(NOUN),
        noun2=random.choice(NOUN2), place=random.choice(PLACE),
    )


def make_description(genre_info):
    setting = random.choice(genre_info["settings"])
    protagonist = random.choice(genre_info["protagonists"])
    conflict = random.choice(genre_info["conflicts"])
    templates = [
        f"Set in {setting}, {protagonist}. When {conflict}, everything they thought they knew is put to the test.",
        f"In {setting}, {protagonist}. But {conflict}, and there may be no going back.",
        f"{protagonist.capitalize()} in {setting}. As {conflict}, they must decide what they're willing to risk.",
    ]
    return random.choice(templates)


def make_books(n_per_genre=75):
    rows = []
    book_id = 1
    used_titles = set()
    for genre, info in GENRES.items():
        made = 0
        attempts = 0
        while made < n_per_genre and attempts < n_per_genre * 5:
            attempts += 1
            title = make_title()
            key = (title, genre)
            if key in used_titles:
                continue
            used_titles.add(key)
            author = random.choice(AUTHORS)
            description = make_description(info)
            secondary_genre = random.choice([g for g in GENRES if g != genre])
            genres_field = f"{genre}, {secondary_genre}"
            avg_rating = round(random.uniform(3.1, 4.9), 2)
            num_ratings = random.randint(120, 250000)
            rows.append({
                "bookId": book_id,
                "title": title,
                "author": author,
                "description": description,
                "genres": genres_field,
                "avg_rating": avg_rating,
                "num_ratings": num_ratings,
            })
            book_id += 1
            made += 1
    random.shuffle(rows)
    return rows


def main():
    rows = make_books()
    fieldnames = ["bookId", "title", "author", "description", "genres", "avg_rating", "num_ratings"]
    with open("data/books.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} books to data/books.csv")


if __name__ == "__main__":
    main()
