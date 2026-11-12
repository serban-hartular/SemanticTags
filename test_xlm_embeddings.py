"""Offline alignment checks with a tiny, randomly initialized XLM-RoBERTa."""

import unittest
from unittest.mock import patch

import torch
from tokenizers import Tokenizer, models, pre_tokenizers, processors, trainers
from transformers import PreTrainedTokenizerFast, XLMRobertaConfig, XLMRobertaModel

from xlm_embeddings import embed_sentence, get_word_embeddings


class WordEmbeddingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        backend = Tokenizer(models.BPE(unk_token="<unk>"))
        backend.pre_tokenizer = pre_tokenizers.Metaspace()
        backend.train_from_iterator(
            ["Ana are mere . neuropsiholingvistică , și Ana"],
            trainers.BpeTrainer(vocab_size=35,
                                special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>"]),
        )
        backend.post_processor = processors.TemplateProcessing(
            single="<s> $A </s>", special_tokens=[("<s>", 0), ("</s>", 2)],
        )
        cls.tokenizer = PreTrainedTokenizerFast(
            tokenizer_object=backend, bos_token="<s>", eos_token="</s>",
            pad_token="<pad>", unk_token="<unk>", model_max_length=64,
        )
        torch.manual_seed(7)
        cls.model = XLMRobertaModel(XLMRobertaConfig(
            vocab_size=len(cls.tokenizer), hidden_size=12, num_hidden_layers=2,
            num_attention_heads=3, intermediate_size=24, max_position_embeddings=66,
            pad_token_id=1, bos_token_id=0, eos_token_id=2,
        )).eval()

    def setUp(self):
        loader = patch("xlm_embeddings._load_model", return_value=(self.tokenizer, self.model))
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def test_word_alignment_matches_model_hidden_states(self):
        words = ["Ana", ",", "neuropsiholingvistică", "și", "Ana", "."]
        result = embed_sentence(words)
        encoded = self.tokenizer(words, is_split_into_words=True, return_tensors="pt")
        with torch.no_grad():
            expected = self.model(**encoded, output_hidden_states=True).hidden_states
        self.assertEqual(result.words, tuple(words))
        self.assertGreater(len(result.subwords[2]), 1)
        for word_index in range(len(words)):
            positions = [i for i, word_id in enumerate(encoded.word_ids())
                         if word_id == word_index]
            self.assertEqual(result.subwords[word_index],
                             tuple(encoded.tokens()[i] for i in positions))
            self.assertEqual(result.embeddings[word_index].shape, (3, len(positions), 12))
            self.assertFalse(result.embeddings[word_index].requires_grad)
            self.assertEqual(result.embeddings[word_index].device.type, "cpu")
            for layer in range(3):
                vectors = get_word_embeddings(result, word_index, layer)
                self.assertIsInstance(vectors, list)
                torch.testing.assert_close(torch.stack(vectors), expected[layer][0, positions])
        torch.testing.assert_close(torch.stack(get_word_embeddings(result, 2, -1)),
                                   result.embeddings[2][2])
        # Repeated spellings refer to distinct contextual positions.
        self.assertFalse(torch.equal(result.embeddings[0][-1], result.embeddings[4][-1]))

    def test_invalid_input_is_rejected_before_loading_model(self):
        for words in [[], [""], ["Ana", "  "]]:
            with self.subTest(words=words), self.assertRaises(ValueError):
                embed_sentence(words)
        for words in ["Ana are mere", ["Ana", 3]]:
            with self.subTest(words=words), self.assertRaises(TypeError):
                embed_sentence(words)
        self.loader.assert_not_called()

    def test_sentence_exceeding_model_capacity_is_not_truncated(self):
        with self.assertRaisesRegex(ValueError, "tokens including special tokens"):
            embed_sentence(["Ana"] * 100)

    def test_invalid_word_and_layer_indices(self):
        result = embed_sentence(["Ana"])
        for index in [-1, 1]:
            with self.subTest(index=index), self.assertRaises(IndexError):
                get_word_embeddings(result, index, 0)
        for layer in [-4, 3]:
            with self.subTest(layer=layer), self.assertRaises(IndexError):
                get_word_embeddings(result, 0, layer)
        with self.assertRaises(TypeError):
            get_word_embeddings(result, True)
        with self.assertRaises(TypeError):
            get_word_embeddings(result, 0, 0.5)


if __name__ == "__main__":
    unittest.main()
