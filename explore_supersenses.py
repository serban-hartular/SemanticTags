"""Explore Romanian WordNet supersenses using an offline Princeton 3.0 mapping."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from importlib.metadata import version
from importlib.resources import as_file, files
from pathlib import Path

from rowordnet import RoWordNet, Synset


ROOT = Path(__file__).resolve().parent


def load_wordnet():
    # Explicit resource path avoids rowordnet 1.1.0's obsolete pkg_resources import.
    with as_file(files("rowordnet").joinpath("rowordnet.pickle")) as path:
        return RoWordNet(filename=str(path))


def analyze(wn):
    with (ROOT / "data/wordnet30_supersenses.tsv").open(encoding="utf-8") as stream:
        mapping = {row["synset_id"]: row["supersense"]
                   for row in csv.DictReader(stream, delimiter="\t")}
    inventory = {line.split()[1]: {"synsets": 0, "literals": set()}
                 for line in (ROOT / "data/lexnames").read_text().splitlines()}
    nouns = defaultdict(list)
    missing = []
    unmapped_by_pos = Counter()
    pos_counts = Counter()
    for synset_id in wn.synsets():
        synset = wn.synset(synset_id)
        pos_counts[str(synset.pos)] += 1
        supersense = mapping.get(synset_id)
        if supersense is None:
            missing.append(synset_id)
            unmapped_by_pos[str(synset.pos)] += 1
        else:
            inventory[supersense]["synsets"] += 1
            inventory[supersense]["literals"].update(synset.literals)
        if synset.pos == Synset.Pos.NOUN:
            # Exact literals only: never add components of multiword expressions.
            for literal in set(synset.literals):
                nouns[literal].append({
                    "synset_id": synset_id,
                    "supersense": supersense or "",
                    "domain": synset.domain or "",
                    "definition": synset.definition or "",
                    "synonyms": "; ".join(synset.literals),
                })
    inventory_rows = [
        {"supersense": name, "synset_count": item["synsets"],
         "literal_count": len(item["literals"])}
        for name, item in sorted(inventory.items())
    ]
    noun_rows = []
    for literal, senses in nouns.items():
        categories = sorted({s["supersense"] for s in senses if s["supersense"]})
        noun_rows.append({
            "literal": literal,
            "supersense_count": len(categories),
            "sense_count": len(senses),
            "unmapped_sense_count": sum(not s["supersense"] for s in senses),
            "supersenses": "; ".join(categories),
            "is_multiword": "_" in literal or any(c.isspace() for c in literal),
        })
    noun_rows.sort(key=lambda r: (-r["supersense_count"], -r["sense_count"], r["literal"]))
    summary = {
        "rowordnet_version": version("rowordnet"),
        "wordnet_mapping_version": "3.0",
        "synset_count": sum(pos_counts.values()),
        "synsets_by_pos": dict(sorted(pos_counts.items())),
        "available_lexnames": sum(r["synset_count"] > 0 for r in inventory_rows),
        "available_noun_supersenses": sum(r["synset_count"] > 0 and
                                          r["supersense"].startswith("noun.")
                                          for r in inventory_rows),
        "noun_literal_count": len(noun_rows),
        "multi_supersense_noun_count": sum(r["supersense_count"] > 1 for r in noun_rows),
        "single_word_noun_count": sum(not r["is_multiword"] for r in noun_rows),
        "single_word_multi_supersense_noun_count": sum(
            r["supersense_count"] > 1 and not r["is_multiword"] for r in noun_rows),
        "noun_supersense_count_distribution": dict(sorted(Counter(
            r["supersense_count"] for r in noun_rows).items())),
        "unmapped_synset_count": len(missing),
        "unmapped_synsets_by_pos": dict(sorted(unmapped_by_pos.items())),
        "noun_literals_with_unmapped_senses": sum(
            r["unmapped_sense_count"] > 0 for r in noun_rows),
        "unmapped_synset_ids": sorted(missing),
    }
    return inventory_rows, noun_rows, nouns, summary


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export(directory, inventory, noun_rows, nouns, summary):
    directory.mkdir(parents=True, exist_ok=True)
    write_csv(directory / "supersenses.csv", list(inventory[0]), inventory)
    fields = ["literal", "supersense_count", "sense_count", "unmapped_sense_count",
              "supersenses", "is_multiword"]
    write_csv(directory / "nouns.csv", fields, noun_rows)
    write_csv(directory / "multi_supersense_nouns.csv", fields,
              (r for r in noun_rows if r["supersense_count"] > 1))
    write_csv(directory / "noun_senses.csv",
              ["literal", "synset_id", "supersense", "domain", "definition", "synonyms"],
              ({"literal": literal, **sense} for literal in sorted(nouns)
               for sense in sorted(nouns[literal], key=lambda s: s["synset_id"])))
    (directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--word", help="Show every noun sense for an exact Romanian literal")
    parser.add_argument("--supersense", action="append", default=[],
                        help="Require this supersense; repeat to require several")
    parser.add_argument("--min-supersenses", type=int, default=2)
    parser.add_argument("--single-words", action="store_true", help="Exclude multiword literals")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--export", type=Path, metavar="DIRECTORY",
                        help="Export complete tables, independent of display filters")
    args = parser.parse_args()
    if args.limit < 1 or args.min_supersenses < 0:
        parser.error("--limit must be positive and --min-supersenses nonnegative")
    inventory, noun_rows, nouns, summary = analyze(load_wordnet())
    valid = {r["supersense"] for r in inventory if r["supersense"].startswith("noun.")}
    if set(args.supersense) - valid:
        parser.error("Unknown noun supersense: " + ", ".join(sorted(set(args.supersense) - valid)))
    print(f"RoWordNet {summary['rowordnet_version']}: {summary['synset_count']:,} synsets; "
          f"{summary['synsets_by_pos'].get('n', 0):,} noun synsets")
    print(f"{summary['noun_literal_count']:,} noun literals; "
          f"{summary['multi_supersense_noun_count']:,} have more than one supersense")
    print(f"Unmapped synsets: {summary['unmapped_synset_count']}")
    if args.export:
        export(args.export, inventory, noun_rows, nouns, summary)
        print(f"Exported complete tables to {args.export.resolve()}")
    if args.word is not None:
        senses = nouns.get(args.word, [])
        print(f"\n{args.word}: {len(senses)} noun senses")
        for sense in sorted(senses, key=lambda s: (s["supersense"], s["synset_id"])):
            print(f"\n  {sense['supersense'] or '(unmapped)'} | {sense['synset_id']}"
                  f" | domain: {sense['domain']}")
            print(f"  {sense['definition']}")
            print(f"  Synonyms: {sense['synonyms']}")
        return
    print("\nSupersense / lexname          Synsets   Distinct literals")
    for row in inventory:
        print(f"{row['supersense']:<28} {row['synset_count']:>7,} {row['literal_count']:>19,}")
    selected = [r for r in noun_rows
                if r["supersense_count"] >= args.min_supersenses
                and (not args.single_words or not r["is_multiword"])
                and set(args.supersense).issubset(r["supersenses"].split("; "))]
    print(f"\n{len(selected):,} matching noun literals (showing up to {args.limit}):")
    for row in selected[:args.limit]:
        print(f"{row['literal']} ({row['supersense_count']} supersenses, "
              f"{row['sense_count']} senses): {row['supersenses']}")


if __name__ == "__main__":
    main()
