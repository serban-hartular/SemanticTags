from explore_supersenses import load_wordnet, analyze

wn = load_wordnet()
inventory, noun_rows, nouns, summary = analyze(wn)  # Run once.

senses = nouns.get("masă", [])

for sense in senses:
    print(sense["synset_id"], sense["supersense"] or "(unmapped)")
    print(sense["definition"])
    print()

