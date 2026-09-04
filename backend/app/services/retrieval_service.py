"""
Proxy re-export module for backward compatibility.
Original implementation has been migrated to app.rag.retrieval.retriever.
"""
from app.rag.retrieval.retriever import (
    generate_query_embedding,
    get_scoped_asset_ids,
    hybrid_retrieval,
)
from app.rag.retrieval.retriever import *  # noqa: F401, F403
