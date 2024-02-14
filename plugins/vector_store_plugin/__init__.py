from lib.vector_store.stores.opensearch import OpenSearchVectorStore

from langchain_community.embeddings import (
    AzureOpenAIEmbeddings,
    HuggingFaceEmbeddings,
    HuggingFaceBgeEmbeddings,
    OpenAIEmbeddings,
)

from vector_store_plugin.elasticsearch import ElasticsearchVectorStore
from vector_store_plugin.eg_openai_embeddings import EGOpenAIEmbeddings

ALL_PLUGIN_VECTOR_STORES = {
    "elasticsearch": ElasticsearchVectorStore,
    "opensearch": OpenSearchVectorStore,
}

ALL_PLUGIN_EMBEDDINGS = {
    "openai": OpenAIEmbeddings,
    #
    # Note: EG Gen AI Proxy requires `openai` provider even when using Azure OpenAI endpoint
    "azure_openai": AzureOpenAIEmbeddings,
    #
    # Custom wrapper that overrides the _get_len_safe_embeddings method
    # GenAI Proxy only supports text input to the embedding API, so we need to override
    # the default behavior of the OpenAIEmbeddings class
    "eg_openai": EGOpenAIEmbeddings,
    #
    # These options run locally and require `sentence_transformers` package to be installed
    # Good for testing and development; note they return smaller vector sizes so
    # you cannot mix and match with OpenAI embeddings
    "bge": HuggingFaceBgeEmbeddings,
    "sentence_transformers": HuggingFaceEmbeddings,
}
