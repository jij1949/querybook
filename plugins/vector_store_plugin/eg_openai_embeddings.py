from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

import logging
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

import tiktoken


logger = logging.getLogger(__name__)


class EGOpenAIEmbeddings(OpenAIEmbeddings):
    """
    This class is a subclass of OpenAIEmbeddings that overrides the _get_len_safe_embeddings method to
    convert tokens back to strings before sending them to the OpenAI API.

    This is to fix the limitation of the Gen AI Proxy which only supports text input to the embedding API
    Inspired by: https://github.expedia.biz/AI/ksphere/blob/main/ksphere/utilities/openai_embedding_wrapper.py
    See Also: https://expedia.slack.com/archives/C0425D3PS72/p1706705846271549

    Original Source:
    https://github.com/langchain-ai/langchain/blob/master/libs/partners/openai/langchain_openai/embeddings/base.py
    """

    # please refer to
    # https://github.com/openai/openai-cookbook/blob/main/examples/Embedding_long_inputs.ipynb
    def _get_len_safe_embeddings(
        self, texts: List[str], *, engine: str, chunk_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate length-safe embeddings for a list of texts.

        This method handles tokenization and embedding generation, respecting the
        set embedding context length and chunk size. It supports both tiktoken
        and HuggingFace tokenizer based on the tiktoken_enabled flag.

        Args:
            texts (List[str]): A list of texts to embed.
            engine (str): The engine or model to use for embeddings.
            chunk_size (Optional[int]): The size of chunks for processing embeddings.

        Returns:
            List[List[float]]: A list of embeddings for each input text.
        """
        _chunk_size = chunk_size or self.chunk_size
        _iter, tokens, indices, encoding = self._tokenize(
            texts, _chunk_size
        )  ## <-- added encoding
        batched_embeddings: List[List[float]] = []
        for i in _iter:
            decoded_input = [
                encoding.decode(x) for x in tokens[i : i + _chunk_size]
            ]  ## <-- new
            response = self.client.create(
                input=decoded_input, **self._invocation_params  ## <-- new
            )
            if not isinstance(response, dict):
                response = response.model_dump()
            batched_embeddings.extend(r["embedding"] for r in response["data"])

        embeddings = _process_batched_chunked_embeddings(
            len(texts), tokens, batched_embeddings, indices, self.skip_empty
        )
        _cached_empty_embedding: Optional[List[float]] = None

        def empty_embedding() -> List[float]:
            nonlocal _cached_empty_embedding
            if _cached_empty_embedding is None:
                average_embedded = self.client.create(
                    input="", **self._invocation_params
                )
                if not isinstance(average_embedded, dict):
                    average_embedded = average_embedded.model_dump()
                _cached_empty_embedding = average_embedded["data"][0]["embedding"]
            return _cached_empty_embedding

        return [e if e is not None else empty_embedding() for e in embeddings]

    def _tokenize(
        self, texts: List[str], chunk_size: int
    ) -> Tuple[Iterable[int], List[Union[List[int], str]], List[int]]:
        """
        Take the input `texts` and `chunk_size` and return 3 iterables as a tuple:

        We have `batches`, where batches are sets of individual texts
        we want responses from the openai api. The length of a single batch is
        `chunk_size` texts.

        Each individual text is also split into multiple texts based on the
        `embedding_ctx_length` parameter (based on number of tokens).

        This function returns a 3-tuple of the following:

        _iter: An iterable of the starting index in `tokens` for each *batch*
        tokens: A list of tokenized texts, where each text has already been split
            into sub-texts based on the `embedding_ctx_length` parameter. In the
            case of tiktoken, this is a list of token arrays. In the case of
            HuggingFace transformers, this is a list of strings.
        indices: An iterable of the same length as `tokens` that maps each token-array
            to the index of the original text in `texts`.
        """
        tokens: List[Union[List[int], str]] = []
        indices: List[int] = []
        model_name = self.tiktoken_model_name or self.model

        # If tiktoken flag set to False
        if not self.tiktoken_enabled:
            try:
                from transformers import AutoTokenizer
            except ImportError:
                raise ValueError(
                    "Could not import transformers python package. "
                    "This is needed for OpenAIEmbeddings to work without "
                    "`tiktoken`. Please install it with `pip install transformers`. "
                )

            tokenizer = AutoTokenizer.from_pretrained(
                pretrained_model_name_or_path=model_name
            )
            for i, text in enumerate(texts):
                # Tokenize the text using HuggingFace transformers
                tokenized: List[int] = tokenizer.encode(text, add_special_tokens=False)

                # Split tokens into chunks respecting the embedding_ctx_length
                for j in range(0, len(tokenized), self.embedding_ctx_length):
                    token_chunk: List[int] = tokenized[
                        j : j + self.embedding_ctx_length
                    ]

                    # Convert token IDs back to a string
                    chunk_text: str = tokenizer.decode(token_chunk)
                    tokens.append(chunk_text)
                    indices.append(i)
        else:
            try:
                encoding = tiktoken.encoding_for_model(model_name)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            encoder_kwargs: Dict[str, Any] = {
                k: v
                for k, v in {
                    "allowed_special": self.allowed_special,
                    "disallowed_special": self.disallowed_special,
                }.items()
                if v is not None
            }
            for i, text in enumerate(texts):
                if self.model.endswith("001"):
                    # See: https://github.com/openai/openai-python/
                    #      issues/418#issuecomment-1525939500
                    # replace newlines, which can negatively affect performance.
                    text = text.replace("\n", " ")

                if encoder_kwargs:
                    token = encoding.encode(text, **encoder_kwargs)
                else:
                    token = encoding.encode_ordinary(text)

                # Split tokens into chunks respecting the embedding_ctx_length
                for j in range(0, len(token), self.embedding_ctx_length):
                    tokens.append(token[j : j + self.embedding_ctx_length])
                    indices.append(i)

        if self.show_progress_bar:
            try:
                from tqdm.auto import tqdm

                _iter: Iterable = tqdm(range(0, len(tokens), chunk_size))
            except ImportError:
                _iter = range(0, len(tokens), chunk_size)
        else:
            _iter = range(0, len(tokens), chunk_size)
        return _iter, tokens, indices, encoding  ## <-- added encoding


## Copied as-is from langchain_core/embeddings/base.py
def _process_batched_chunked_embeddings(
    num_texts: int,
    tokens: List[Union[List[int], str]],
    batched_embeddings: List[List[float]],
    indices: List[int],
    skip_empty: bool,
) -> List[Optional[List[float]]]:
    # for each text, this is the list of embeddings (list of list of floats)
    # corresponding to the chunks of the text
    results: List[List[List[float]]] = [[] for _ in range(num_texts)]

    # for each text, this is the token length of each chunk
    # for transformers tokenization, this is the string length
    # for tiktoken, this is the number of tokens
    num_tokens_in_batch: List[List[int]] = [[] for _ in range(num_texts)]

    for i in range(len(indices)):
        if skip_empty and len(batched_embeddings[i]) == 1:
            continue
        results[indices[i]].append(batched_embeddings[i])
        num_tokens_in_batch[indices[i]].append(len(tokens[i]))

    # for each text, this is the final embedding
    embeddings: List[Optional[List[float]]] = []
    for i in range(num_texts):
        # an embedding for each chunk
        _result: List[List[float]] = results[i]

        if len(_result) == 0:
            # this will be populated with the embedding of an empty string
            # in the sync or async code calling this
            embeddings.append(None)
            continue

        elif len(_result) == 1:
            # if only one embedding was produced, use it
            embeddings.append(_result[0])
            continue

        else:
            # else we need to weighted average
            # should be same as
            # average = np.average(_result, axis=0, weights=num_tokens_in_batch[i])
            total_weight = sum(num_tokens_in_batch[i])
            average = [
                sum(
                    val * weight
                    for val, weight in zip(embedding, num_tokens_in_batch[i])
                )
                / total_weight
                for embedding in zip(*_result)
            ]

            # should be same as
            # embeddings.append((average / np.linalg.norm(average)).tolist())
            magnitude = sum(val**2 for val in average) ** 0.5
            embeddings.append([val / magnitude for val in average])

    return embeddings
