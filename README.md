# Exploring Romanian WordNet supersenses

Run from this directory using the existing virtual environment:

```bash
# All available categories and the nouns with most distinct supersenses
.venv/bin/python explore_supersenses.py

# Inspect definitions and categories for every noun sense of an exact literal
.venv/bin/python explore_supersenses.py --word bancă
.venv/bin/python explore_supersenses.py --word masă

# Find nouns that have BOTH a person sense and an artifact sense
.venv/bin/python explore_supersenses.py --supersense noun.person --supersense noun.artifact

# Exclude multiword expressions; show more results
.venv/bin/python explore_supersenses.py --single-words --limit 100

# List nouns within a category, including those with only one supersense
.venv/bin/python explore_supersenses.py --supersense noun.food --min-supersenses 1

# Regenerate the complete spreadsheet exports
.venv/bin/python explore_supersenses.py --export results
```

See [the report](results/REPORT.md) for counts and examples. Open the CSVs in a
spreadsheet, or use them in Python. No extra packages or runtime downloads are
needed beyond the installed `rowordnet` and its dependencies.

## What is being counted

A **synset** represents one sense. Its **supersense** is a coarse semantic category
such as `noun.person` or `noun.artifact`, obtained from the Princeton WordNet 3.0
lexicographer file number. A **literal** is the exact Romanian word or expression
listed in a synset. A literal belongs to multiple supersenses when its noun
senses span at least two distinct categories. Multiple senses within a single
category do not qualify.

RoWordNet's `domain` field provides topic labels such as `banking` and `furniture`;
these are a different classification. The exports retain both fields so you can
compare them. The classification here uses the full lexicographer inventory:
26 noun categories including the special root category `noun.Tops`, 15 verb
categories, three adjective categories and one adverb category. Some supersense
annotation schemes omit `noun.Tops` or treat adjectives differently.

Only exact literals and noun senses contribute to the noun counts. Thus the verb
`ochi` does not contribute to the noun `ochi`, and a noun occurring only inside
an expression is not counted as a standalone literal. Spelling, capitalization
and diacritics are preserved; multiword expressions are included by default.
"Single word" means no underscore or whitespace; hyphenated forms remain included.
Noun literals with unmapped senses can have additional categories that are
unknown here, so the ambiguity count is a lower bound.

## Exported tables

| File | Contents |
| --- | --- |
| [supersenses.csv](results/supersenses.csv) | All 45 lexnames with synset counts and distinct literal counts |
| [nouns.csv](results/nouns.csv) | All noun literals, number of senses, distinct categories and missing mappings |
| [multi_supersense_nouns.csv](results/multi_supersense_nouns.csv) | Noun literals with two or more mapped supersenses |
| [noun_senses.csv](results/noun_senses.csv) | Every literal–noun-synset membership, with category, domain, definition and synonyms |
| [summary.json](results/summary.json) | Summary counts and every unmapped synset ID |

CSV files use UTF-8 with a BOM for spreadsheet compatibility. Category lists use
`; ` as a separator. Synset counts and literal counts are distinct: a literal
can occur in several synsets or categories. Display filters do not restrict
exports. Ordering is by descending supersense count, then sense count, then
Unicode literal order; this is not a corpus frequency ranking.

## Sources and reproducibility

- [RoWordNet API and dataset](https://github.com/dumitrescustefan/RoWordNet), installed version 1.1.0.
- [Princeton lexicographer category inventory](https://wordnet.princeton.edu/documentation/lexnames5wn).
- [Princeton data file format](https://wordnet.princeton.edu/documentation/wndb5wn).
- [Official WordNet 3.0 archive](https://wordnetcode.princeton.edu/3.0/WordNet-3.0.tar.gz).

The offline table `data/wordnet30_supersenses.tsv` is derived from WordNet 3.0's
`dict/data.noun`, `data.verb`, `data.adj` and `data.adv`. Each data row starts with
`synset_offset lex_filenum ss_type`; `lex_filenum` resolves through `dict/lexnames`.
The join key is `ENG30-{synset_offset}-{ss_type}`, normalizing adjective satellite
`s` to `a` for RoWordNet. This is an ID-based mapping, with no translation or
hypernym inference. Unmatched IDs remain unclassified. The archive checksum is
recorded in [provenance.json](data/provenance.json); the WordNet license is retained
in [WORDNET-LICENSE.txt](data/WORDNET-LICENSE.txt).

The loader passes the package's bundled pickle path explicitly using
`importlib.resources`, avoiding `RoWordNet()`'s obsolete `pkg_resources` dependency
on this Python 3.13 environment. It does not modify the installed package.

## XLM-RoBERTa word embeddings

Install the embedding dependencies in your virtual environment:

```bash
.venv/bin/python -m pip install -r requirements-embeddings.txt
```

For a CPU-only PyTorch installation, install `torch` from
`https://download.pytorch.org/whl/cpu` first. The current project environment has
the CPU version installed.

In a Python session started from this directory:

```python
from xlm_embeddings import embed_sentence, get_word_embeddings

words = ["Ana", "studiază", "neuropsiholingvistica", "."]
sentence = embed_sentence(words)

# All layers for the third input word: [layers, subwords, hidden_size].
sentence.embeddings[2].shape
sentence.subwords[2]  # Subword strings, in the same order as the vectors.

# A list containing one 768-dimensional tensor per subword, final layer.
vectors = get_word_embeddings(sentence, word_index=2, layer=-1)

# The same word's first transformer layer.
first_layer_vectors = get_word_embeddings(sentence, word_index=2, layer=1)
```

The default checkpoint is `FacebookAI/xlm-roberta-base`: 12 transformer layers
and 768 dimensions per vector. There are **13 returned layers**: layer `0` is the
embedding module's output, and layers `1`–`12` are transformer outputs. `-1`
selects the final layer. Word indices start at zero and include punctuation.
Repeated words remain separate entries. No averaging of subwords is performed.
The vectors are contextual representations computed from the entire input list.

The first call downloads the pretrained tokenizer and weights from Hugging Face;
later calls reuse the loaded model. Use `model_name="FacebookAI/xlm-roberta-large"`
or a local model directory to select another XLM-RoBERTa checkpoint, and
`device="cuda"` for GPU inference with a suitable PyTorch installation. Returned
tensors always reside on CPU and have gradients disabled. Only the most recently
used model/device pair is kept in the in-process cache.

Alignment uses the fast tokenizer's `word_ids()` with `is_split_into_words=True`.
Added special tokens participate in model inference but are omitted from the
word groups. Blank entries and empty lists are rejected; sentences beyond the
model's token limit raise an error instead of truncating the input. Vectors from
`get_word_embeddings` share storage with the result; use `.clone()` if modifying
them independently.

Run offline tests with a small randomly initialized XLM-RoBERTa model:

```bash
.venv/bin/python -m unittest -v test_xlm_embeddings
```

References: [tokenizer word alignment](https://huggingface.co/docs/transformers/main_classes/tokenizer#transformers.BatchEncoding.word_ids),
[XLM-RoBERTa hidden states](https://huggingface.co/docs/transformers/model_doc/xlm-roberta#transformers.XLMRobertaModel),
and [base checkpoint configuration](https://huggingface.co/FacebookAI/xlm-roberta-base/blob/main/config.json).
