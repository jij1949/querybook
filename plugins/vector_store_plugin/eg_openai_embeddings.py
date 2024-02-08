from __future__ import annotations

from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.openai import embed_with_retry

import logging
from typing import (
    List,
    Optional,
)

import numpy as np

logger = logging.getLogger(__name__)


class EGOpenAIEmbeddings(OpenAIEmbeddings):
    """
    This class is a subclass of OpenAIEmbeddings that overrides the _get_len_safe_embeddings method

    This is to fix the limitation of the Gen AI Proxy which only supports text input to the embedding API
    Reference: https://github.expedia.biz/AI/ksphere/blob/main/ksphere/utilities/openai_embedding_wrapper.py
    See Also: https://expedia.slack.com/archives/C0425D3PS72/p1706705846271549
    """

    # please refer to
    # https://github.com/openai/openai-cookbook/blob/main/examples/Embedding_long_inputs.ipynb
    def _get_len_safe_embeddings(
        self, texts: List[str], *, engine: str, chunk_size: Optional[int] = None
    ) -> List[List[float]]:
        embeddings: List[List[float]] = [[] for _ in range(len(texts))]
        try:
            import tiktoken
        except ImportError:
            raise ImportError(
                "Could not import tiktoken python package. "
                "This is needed in order to for OpenAIEmbeddings. "
                "Please install it with `pip install tiktoken`."
            )

        tokens = []
        indices = []
        model_name = self.tiktoken_model_name or self.model
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning("Warning: model not found. Using cl100k_base encoding.")
            model = "cl100k_base"
            encoding = tiktoken.get_encoding(model)
        for i, text in enumerate(texts):
            if self.model.endswith("001"):
                # See: https://github.com/openai/openai-python/issues/418#issuecomment-1525939500
                # replace newlines, which can negatively affect performance.
                text = text.replace("\n", " ")
            token = encoding.encode(
                text,
                allowed_special=self.allowed_special,
                disallowed_special=self.disallowed_special,
            )
            for j in range(0, len(token), self.embedding_ctx_length):
                tokens.append(token[j : j + self.embedding_ctx_length])
                indices.append(i)

        batched_embeddings: List[List[float]] = []
        _chunk_size = chunk_size or self.chunk_size

        if self.show_progress_bar:
            try:
                import tqdm

                _iter = tqdm.tqdm(range(0, len(tokens), _chunk_size))
            except ImportError:
                _iter = range(0, len(tokens), _chunk_size)
        else:
            _iter = range(0, len(tokens), _chunk_size)

        for i in _iter:
            decoded_input = [
                encoding.decode(x) for x in tokens[i : i + _chunk_size]
            ]  ## <-- new
            response = embed_with_retry(
                self,
                input=decoded_input,  ## <-- new
                **self._invocation_params,
            )
            batched_embeddings.extend(r["embedding"] for r in response["data"])

        results: List[List[List[float]]] = [[] for _ in range(len(texts))]
        num_tokens_in_batch: List[List[int]] = [[] for _ in range(len(texts))]
        for i in range(len(indices)):
            results[indices[i]].append(batched_embeddings[i])
            num_tokens_in_batch[indices[i]].append(len(tokens[i]))

        for i in range(len(texts)):
            _result = results[i]
            if len(_result) == 0:
                average = embed_with_retry(
                    self,
                    input="",
                    **self._invocation_params,
                )[
                    "data"
                ][0]["embedding"]
            else:
                average = np.average(_result, axis=0, weights=num_tokens_in_batch[i])
            embeddings[i] = (average / np.linalg.norm(average)).tolist()

        return embeddings
