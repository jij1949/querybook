from lib.vector_store.stores.opensearch import OpenSearchVectorStore
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceBgeEmbeddings,
)

from vector_store_plugin.elasticsearch import ElasticsearchVectorStore

ALL_PLUGIN_VECTOR_STORES = {
    "elasticsearch": ElasticsearchVectorStore,
    "opensearch": OpenSearchVectorStore,
}

ALL_PLUGIN_EMBEDDINGS = {
    "openai": OpenAIEmbeddings,
    # Both of these require `sentence_transformers` package to be installed
    "bge": HuggingFaceBgeEmbeddings,
    "sentence_transformers": HuggingFaceEmbeddings,
}
