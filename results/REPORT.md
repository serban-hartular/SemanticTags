# RoWordNet supersense exploration

Analyzed installed RoWordNet 1.1.0 using Princeton WordNet 3.0 lexicographer categories.

- **59,348 synsets**, including **41,063 noun synsets**.
- **26 noun categories**, including `noun.Tops`; all 45 lexnames are represented across parts of speech.
- **38,931 distinct noun literals**, including expressions.
- **4,487 noun literals (11.53%)** have at least two mapped supersenses.
- Restricting to literals without underscores or whitespace: **4,315** out of **24,998** nouns have multiple supersenses.
- **541 unmapped synsets**, all with `BILI-` IDs; **514** are nouns. These are retained with an empty supersense, never assigned a guessed category.
- **524 noun literals** have at least one unmapped sense. Counts of multi-supersense literals are therefore lower bounds.

## Examples

| Noun | Noun senses | Distinct supersenses | Categories |
| --- | ---: | ---: | --- |
| bancă | 6 | 3 | noun.artifact; noun.group; noun.possession |
| ochi | 9 | 3 | noun.artifact; noun.body; noun.cognition |
| masă | 18 | 8 | noun.artifact; noun.attribute; noun.communication; noun.food; noun.group; noun.object; noun.possession; noun.time |
| cap | 22 | 12 | noun.act; noun.animal; noun.artifact; noun.body; noun.cognition; noun.communication; noun.group; noun.location; noun.object; noun.person; noun.quantity; noun.state |

For `bancă`, the financial institution is `noun.group`, the building and seats are `noun.artifact`, and the gambling stake is `noun.possession`. These categories group senses; they are not usage predictions for a sentence.

## Available noun supersenses

| Supersense | Synsets | Distinct noun literals |
| --- | ---: | ---: |
| noun.Tops | 40 | 75 |
| noun.act | 4,313 | 4,839 |
| noun.animal | 2,050 | 2,334 |
| noun.artifact | 6,569 | 6,192 |
| noun.attribute | 2,012 | 2,217 |
| noun.body | 967 | 1,190 |
| noun.cognition | 1,799 | 2,091 |
| noun.communication | 3,066 | 3,347 |
| noun.event | 706 | 934 |
| noun.feeling | 320 | 453 |
| noun.food | 1,123 | 1,106 |
| noun.group | 1,429 | 1,526 |
| noun.location | 1,989 | 2,183 |
| noun.motive | 27 | 42 |
| noun.object | 912 | 1,070 |
| noun.person | 4,887 | 5,491 |
| noun.phenomenon | 379 | 482 |
| noun.plant | 1,719 | 2,227 |
| noun.possession | 562 | 570 |
| noun.process | 462 | 613 |
| noun.quantity | 823 | 910 |
| noun.relation | 263 | 317 |
| noun.shape | 200 | 237 |
| noun.state | 1,743 | 2,226 |
| noun.substance | 1,538 | 1,864 |
| noun.time | 651 | 710 |

## Number of categories per noun literal

| Mapped supersenses | Noun literals |
| ---: | ---: |
| 0 | 440 |
| 1 | 34,004 |
| 2 | 3,092 |
| 3 | 876 |
| 4 | 322 |
| 5 | 116 |
| 6 | 36 |
| 7 | 29 |
| 8 | 9 |
| 9 | 4 |
| 11 | 1 |
| 12 | 2 |

A zero means all available noun senses are unmapped, rather than that the noun has no semantic category. A literal may have both mapped and unmapped senses.

## Nouns spanning the most categories

| Noun | Distinct supersenses | Noun senses |
| --- | ---: | ---: |
| parte | 12 | 29 |
| cap | 12 | 22 |
| legătură | 11 | 33 |
| linie | 9 | 26 |
| bază | 9 | 25 |
| vârf | 9 | 16 |
| lucru | 9 | 14 |
| masă | 8 | 18 |
| pas | 8 | 16 |
| formă | 8 | 15 |
| potrivire | 8 | 15 |
| coadă | 8 | 14 |
| nod | 8 | 12 |
| rând | 8 | 12 |
| viață | 8 | 12 |
| sector | 8 | 11 |
| semn | 7 | 20 |
| loc | 7 | 19 |
| poziție | 7 | 18 |
| rezervă | 7 | 18 |

Open [multi_supersense_nouns.csv](multi_supersense_nouns.csv) for the full list, [noun_senses.csv](noun_senses.csv) for definitions and IDs, and [supersenses.csv](supersenses.csv) for categories across all parts of speech. See the [README](../README.md) for commands, counting rules and sources.
