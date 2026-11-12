"""Contextual XLM-RoBERTa embeddings aligned to pre-split input words."""

from dataclasses import dataclass
from functools import lru_cache

import torch
from transformers import AutoModel, AutoTokenizer


@dataclass(frozen=True)
class SentenceEmbeddings:
    """Embeddings and subword strings in the original input order.

    ``embeddings[word_index]`` is a detached CPU tensor with shape
    ``(num_hidden_layers + 1, num_subwords, hidden_size)``.
    Layer 0 is the embedding module's output; layers 1..N are encoder outputs.
    ``subwords[word_index]`` names the corresponding subwords, in token order.
    Added special tokens are excluded. Tensors are not pooled or normalized.
    """

    words: tuple[str, ...]
    subwords: tuple[tuple[str, ...], ...]
    embeddings: tuple[torch.Tensor, ...]


@lru_cache(maxsize=1)
def _load_model(model_name: str, device: str):
    """Reuse the most recently requested tokenizer and model between calls."""
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if not tokenizer.is_fast:
        raise ValueError("A fast tokenizer is required for word-to-subword alignment.")
    model = AutoModel.from_pretrained(model_name)
    if model.config.model_type != "xlm-roberta":
        raise ValueError("model_name must identify an XLM-RoBERTa model.")
    model.to(device)
    model.eval()
    return tokenizer, model


def embed_sentence(
    words: list[str],
    *,
    model_name: str = "FacebookAI/xlm-roberta-base",
    device: str = "cpu",
) -> SentenceEmbeddings:
    """Return all layers of subword embeddings, grouped by input word.

    ``words`` must be a nonempty list of nonblank strings, e.g.
    ``["Ana", "are", "mere", "."]``. Indices refer to this list, including
    punctuation. Repeated words retain their separate positions and contexts.
    Use the checkpoint name or a local pretrained model directory as model_name.
    The first call downloads the tokenizer and model unless already cached.

    Inference runs with dropout and gradients disabled. Outputs reside on CPU
    even when ``device="cuda"`` is used for inference. Oversized inputs raise
    ValueError instead of silently truncating words or subwords.
    """
    if not isinstance(words, list) or any(not isinstance(w, str) for w in words):
        raise TypeError("words must be a list of strings.")
    if not words or any(not word.strip() for word in words):
        raise ValueError("words must be nonempty and contain no blank entries.")

    tokenizer, model = _load_model(model_name, device)
    encoded = tokenizer(words, is_split_into_words=True, return_tensors="pt",
                        truncation=False)
    # XLM-R position IDs start at pad_token_id + 1 for non-padding tokens.
    position_limit = model.config.max_position_embeddings - model.config.pad_token_id - 1
    max_length = min(tokenizer.model_max_length, position_limit)
    sequence_length = encoded["input_ids"].shape[1]
    if sequence_length > max_length:
        raise ValueError(
            f"Sentence produces {sequence_length} tokens including special tokens; "
            f"this model supports at most {max_length}. Split the sentence first."
        )

    positions: list[list[int]] = [[] for _ in words]
    for token_index, word_index in enumerate(encoded.word_ids()):
        if word_index is not None:
            positions[word_index].append(token_index)
    missing = [i for i, indices in enumerate(positions) if not indices]
    if missing:
        raise ValueError(f"Tokenizer produced no subwords for input word indices {missing}.")

    tokens = encoded.tokens()
    with torch.no_grad():
        output = model(**encoded.to(device), output_hidden_states=True, return_dict=True)
    # Stack after copying to CPU so GPU storage is released after this call.
    layers = torch.stack([layer[0].detach().cpu() for layer in output.hidden_states])
    return SentenceEmbeddings(
        words=tuple(words),
        subwords=tuple(tuple(tokens[i] for i in indices) for indices in positions),
        embeddings=tuple(layers[:, indices, :].contiguous() for indices in positions),
    )


def get_word_embeddings(
    sentence: SentenceEmbeddings, word_index: int, layer: int = -1,
) -> list[torch.Tensor]:
    """Return one vector per subword for the chosen word and layer.

    The word index is zero-based and must be nonnegative. Layers accept Python
    indexing: 0 is the embedding output, 1 is the first encoder layer and -1 is
    the last encoder layer. Each vector has shape ``(hidden_size,)``.
    Returned vectors are views into the stored tensor; clone before modifying.
    """
    if not isinstance(word_index, int) or isinstance(word_index, bool):
        raise TypeError("word_index must be an integer.")
    if not 0 <= word_index < len(sentence.words):
        raise IndexError(f"word_index must be between 0 and {len(sentence.words) - 1}.")
    if not isinstance(layer, int) or isinstance(layer, bool):
        raise TypeError("layer must be an integer.")
    embeddings = sentence.embeddings[word_index]
    num_layers = embeddings.shape[0]
    if not -num_layers <= layer < num_layers:
        raise IndexError(f"layer must be between {-num_layers} and {num_layers - 1}.")
    return list(embeddings[layer].unbind(dim=0))
