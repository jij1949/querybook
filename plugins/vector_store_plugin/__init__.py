# ALL_PLUGIN_VECTOR_STORES = {}
# ALL_PLUGIN_EMBEDDINGS = {}

# Example to add vector store

from lib.vector_store.stores.opensearch import OpenSearchVectorStore
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceBgeEmbeddings,
)

ALL_PLUGIN_VECTOR_STORES = {"opensearch": OpenSearchVectorStore}

ALL_PLUGIN_EMBEDDINGS = {
    "openai": OpenAIEmbeddings,
    # Both of these require `sentence_transformers` package to be installed
    "bge": HuggingFaceBgeEmbeddings,
    "sentence_transformers": HuggingFaceEmbeddings,
}
