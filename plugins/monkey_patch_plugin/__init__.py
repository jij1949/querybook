# NOTE: If you want to add or override an API endpoint, please use API plugin instead.

# from .demo import patch as demo_patch
#
# demo_patch()

from .vector_store import patch as vector_store_patch

vector_store_patch()
