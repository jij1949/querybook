from datetime import datetime
from langchain.docstore.document import Document
from langchain.vectorstores import ElasticsearchStore
from lib.logger import get_logger
from lib.vector_store.base_vector_store import VectorStoreBase
from models.metastore import DataTable
from typing import (
    Any,
    List,
    Tuple,
)

LOG = get_logger(__file__)

# Minimum interval between reprocessing tables in minutes
# This is to avoid reprocessing tables too frequently
REPROCESS_TABLES_AFTER_MINUTES = 60 * 24 * 30  # 30 days


class ElasticsearchVectorStore(ElasticsearchStore, VectorStoreBase):
    def get_doc_by_id(self, doc_id: str):
        try:
            doc = self.client.get(index=self.index_name, id=doc_id)
            return Document(
                page_content=doc["_source"]["text"],
                metadata=doc["_source"]["metadata"],
            )
        except Exception as e:
            # return None for not found or any error occurs
            LOG.error(f"Failed to get document {doc_id} from vector store: {e}")
            return None

    def delete_doc_by_id(self, doc_id: str):
        self.client.delete(index=self.index_name, id=doc_id)

    def similarity_search_with_score(
        self, *args: Any, **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """Run similarity search with distance."""

        # The default implementation of similarity_search_with_score
        # passes the OpenSearch-compatible `boolean_filter` argument
        #
        # OpenSearch: `boolean_filter`: single filter
        # Elasticsearch: `filter`: list of filters
        #
        # So pop the `boolean_filter` from kwargs and pass it as `filter`
        filter = [kwargs.pop("boolean_filter", None)]

        return super().similarity_search_with_score(*args, filter=filter, **kwargs)

    def should_skip_table(self, table: DataTable) -> bool:
        """Whether to skip logging the table to the vector store.

        Override this method to implement custom logic for your vector store."""

        # Avoid circular import
        from logic.vector_store import _get_table_doc_id

        # Check if the table is already in the vector store
        existing_doc = self.get_doc_by_id(_get_table_doc_id(table.id))

        # Skip if the table is already in the vector store
        # and it was updated within the last REPROCESS_TABLES_AFTER_MINUTES
        if existing_doc:
            if "updated_at" in existing_doc.metadata:
                updated_at = datetime.fromisoformat(existing_doc.metadata["updated_at"])
                if (
                    datetime.now() - updated_at
                ).total_seconds() / 60 < REPROCESS_TABLES_AFTER_MINUTES:
                    LOG.debug(
                        f"Table {table.id} is already in the vector store, skipping"
                    )
                    return True

        return False
