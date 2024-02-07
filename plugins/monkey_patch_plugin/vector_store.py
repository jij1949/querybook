from lib.logger import get_logger

from logic import vector_store as vector_store_logic
from monkey_patch_plugin.rate_limit import rate_limit

LOG = get_logger(__file__)

CREATE_AND_STORE_DOCUMENT_MIN_INTERVAL = 2.5  # 30 TPM (2 seconds per request)

old_create_and_store_document = vector_store_logic.create_and_store_document

create_and_store_document = rate_limit(
    old_create_and_store_document, min_interval=CREATE_AND_STORE_DOCUMENT_MIN_INTERVAL
)


def patch():
    vector_store_logic.create_and_store_document = create_and_store_document
    LOG.info("Patched vector_store_logic.create_and_store_document with rate limit")
    return True
