import logging
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.observability import observe_llm
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.services.notebook_service import get_scoped_asset_ids

logger = logging.getLogger(__name__)


@observe_llm(name="generate_query_embedding", as_type="generation")
@retry(
    stop=stop_after_attempt(settings.GEMINI_RETRIEVAL_EMBED_RETRY_ATTEMPTS),
    wait=wait_exponential(
        multiplier=settings.GEMINI_RETRIEVAL_EMBED_RETRY_MULTIPLIER,
        min=settings.GEMINI_RETRIEVAL_EMBED_RETRY_MIN_WAIT,
        max=settings.GEMINI_RETRIEVAL_EMBED_RETRY_MAX_WAIT,
    ),
    reraise=True,
)
def generate_query_embedding(query: str) -> list[float]:
    """
    Generates query embedding using settings.GEMINI_EMBEDDING_MODEL
    with task_type='RETRIEVAL_QUERY' and output_dimensionality=settings.EMBEDDING_DIMENSION.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.EMBEDDING_DIMENSION,
            task_type="RETRIEVAL_QUERY",
        ),
    )
    return response.embeddings[0].values


def hybrid_retrieval(db: Session, notebook_id: int, query: str) -> dict:
    """
    Performs RRF-based Hybrid Search (Dense + Sparse).
    1. Fetches scoped asset IDs.
    2. If empty, short-circuits.
    3. Triggers Dense Search (top-20).
    4. Triggers Sparse Search (top-20).
    5. Performs RRF merge (k=60), filters to top-5.
    6. Stitches adjacent chunks.
    7. Enforces token budget (3000 tokens) in memory using accumulated token_count.
    8. Renumbers the final stitched chunks [1]..[N].
    """
    # 1. Fetch scoped assets (Early Return / Short-circuit)
    scoped_ids = get_scoped_asset_ids(db, notebook_id)
    if not scoped_ids:
        logger.info(f"Hybrid retrieval: Notebook {notebook_id} has no completed assets. Short-circuiting.")
        return {
            "status": "no_documents",
            "chunks": [],
            "context": "",
        }

    # 2. Dense query (vector search)
    try:
        query_vector = generate_query_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        query_vector = None

    dense_results = []
    if query_vector is not None:
        # Note: Filter before ranking: WHERE asset_id IN (:scoped_ids) is within LIMIT query
        dense_stmt = (
            select(
                AssetEmbedding,
                AssetEmbedding.embedding.cosine_distance(query_vector).label("distance"),
            )
            .where(
                AssetEmbedding.asset_id.in_(scoped_ids),
                AssetEmbedding.embedding.isnot(None),
            )
            .order_by("distance")
            .limit(settings.RAG_DENSE_SEARCH_TOP_K)
        )
        dense_results = db.execute(dense_stmt).all()
        logger.info(f"Hybrid retrieval: Dense search returned {len(dense_results)} chunks scoped to assets: {[r[0].asset_id for r in dense_results]}")

    # 3. Sparse query (TSV full-text search)
    # Note: Filter before ranking: WHERE asset_id IN (:scoped_ids) is within LIMIT query
    sparse_stmt = (
        select(
            AssetEmbedding,
            func.ts_rank_cd(
                AssetEmbedding.tsv_content,
                func.plainto_tsquery("simple", func.immutable_unaccent(query)),
            ).label("rank_score"),
        )
        .where(
            AssetEmbedding.asset_id.in_(scoped_ids),
            AssetEmbedding.tsv_content.bool_op("@@")(
                func.plainto_tsquery("simple", func.immutable_unaccent(query))
            ),
        )
        .order_by(text("rank_score DESC"))
        .limit(settings.RAG_SPARSE_SEARCH_TOP_K)
    )
    sparse_results = db.execute(sparse_stmt).all()
    logger.info(f"Hybrid retrieval: Sparse search returned {len(sparse_results)} chunks scoped to assets: {[r[0].asset_id for r in sparse_results]}")

    # 4. RRF Merging
    rrf_dict = {}

    for rank, row in enumerate(dense_results, 1):
        chunk = row[0]
        if chunk.id not in rrf_dict:
            rrf_dict[chunk.id] = {
                "chunk": chunk,
                "rrf_score": 0.0,
                "dense_rank": rank,
                "sparse_rank": None,
            }
        rrf_dict[chunk.id]["rrf_score"] += 1.0 / (settings.RAG_RRF_K + rank)

    for rank, row in enumerate(sparse_results, 1):
        chunk = row[0]
        if chunk.id not in rrf_dict:
            rrf_dict[chunk.id] = {
                "chunk": chunk,
                "rrf_score": 0.0,
                "dense_rank": None,
                "sparse_rank": rank,
            }
        rrf_dict[chunk.id]["rrf_score"] += 1.0 / (settings.RAG_RRF_K + rank)

    # Sort all candidates by RRF score DESC
    sorted_candidates = sorted(rrf_dict.values(), key=lambda x: x["rrf_score"], reverse=True)
    # Filter to top candidates
    top_candidates = sorted_candidates[:settings.RAG_RRF_TOP_K]

    if not top_candidates:
        return {
            "status": "success",
            "chunks": [],
            "context": "",
        }

    # 5. Adjacent Chunk Stitching
    # Chunks are adjacent if same asset_id, same page_number, and chunk_index is contiguous (e.g. index i and i+1)
    chunks_for_stitch = [item["chunk"] for item in top_candidates]
    id_to_item = {item["chunk"].id: item for item in top_candidates}

    # Sort chunks by asset_id, page_number, and chunk_index to identify adjacent blocks
    chunks_sorted = sorted(chunks_for_stitch, key=lambda c: (c.asset_id, c.page_number, c.chunk_index))

    stitched_blocks = []
    for chunk in chunks_sorted:
        item = id_to_item[chunk.id]
        chunk_tokens = chunk.token_count if (getattr(chunk, "token_count", 0) or 0) > 0 else max(1, int(len(chunk.content.split()) * 1.3))
        if stitched_blocks and (
            stitched_blocks[-1]["asset_id"] == chunk.asset_id
            and stitched_blocks[-1]["page_number"] == chunk.page_number
            and chunk.chunk_index == stitched_blocks[-1]["chunk_indices"][-1] + 1
        ):
            # Stitch content and append index
            stitched_blocks[-1]["chunk_indices"].append(chunk.chunk_index)
            stitched_blocks[-1]["content"] += " " + chunk.content
            stitched_blocks[-1]["token_count"] += chunk_tokens
            # Keep the highest RRF score (best score)
            if item["rrf_score"] > stitched_blocks[-1]["best_score"]:
                stitched_blocks[-1]["best_score"] = item["rrf_score"]
        else:
            # Start new block
            stitched_blocks.append({
                "asset_id": chunk.asset_id,
                "page_number": chunk.page_number,
                "chunk_indices": [chunk.chunk_index],
                "content": chunk.content,
                "token_count": chunk_tokens,
                "best_score": item["rrf_score"],
            })

    # Sort the stitched blocks back by their best score DESC to preserve RRF priority order
    stitched_blocks = sorted(stitched_blocks, key=lambda b: b["best_score"], reverse=True)

    # 6. Token Budget Enforcement
    max_budget = settings.RAG_CONTEXT_MAX_TOKENS
    accumulated_tokens = 0
    final_blocks = []

    for block in stitched_blocks:
        block_tokens = block.get("token_count", 0)
        if not final_blocks:
            # Always include at least the top-ranked block
            final_blocks.append(block)
            accumulated_tokens += block_tokens
        elif accumulated_tokens + block_tokens <= max_budget:
            final_blocks.append(block)
            accumulated_tokens += block_tokens
        else:
            # Stop adding blocks once budget is exceeded
            break

    # 7. Renumbering & Build final context string
    # Batch fetch Asset records for all unique asset_ids in final_blocks
    unique_asset_ids = list({block["asset_id"] for block in final_blocks})
    asset_map: dict[int, str] = {}
    if unique_asset_ids:
        assets = db.execute(select(Asset).where(Asset.id.in_(unique_asset_ids))).scalars().all()
        asset_map = {asset.id: asset.file_name for asset in assets}

    final_context_list = []
    final_context_str = ""
    for idx, block in enumerate(final_blocks, 1):
        file_name = asset_map.get(block["asset_id"], f"Document_{block['asset_id']}")

        block_desc = {
            "index": idx,
            "asset_id": block["asset_id"],
            "file_name": file_name,
            "page_number": block["page_number"],
            "content": block["content"],
            "best_score": block["best_score"],
        }
        final_context_list.append(block_desc)
        final_context_str += f"[{idx}] [Tài liệu: {file_name}, Trang: {block['page_number']}]\n{block['content']}\n\n"

    return {
        "status": "success",
        "chunks": final_context_list,
        "context": final_context_str.strip(),
    }
