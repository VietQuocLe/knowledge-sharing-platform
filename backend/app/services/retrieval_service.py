import logging
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.asset_embedding import AssetEmbedding
from app.services.notebook_service import get_scoped_asset_ids

logger = logging.getLogger(__name__)


def generate_query_embedding(query: str) -> list[float]:
    """
    Generates query embedding using settings.GEMINI_EMBEDDING_MODEL
    with task_type='RETRIEVAL_QUERY' and output_dimensionality=768.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
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
    7. Enforces token budget (3000 tokens) using client.models.count_tokens.
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

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    # 2. Dense query (vector search)
    try:
        query_vector = generate_query_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        query_vector = None

    dense_results = []
    if query_vector is not None:
        # Note: Filter before ranking: WHERE asset_id IN (:scoped_ids) is within LIMIT 20 query
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
            .limit(20)
        )
        dense_results = db.execute(dense_stmt).all()
        logger.info(f"Hybrid retrieval: Dense search returned {len(dense_results)} chunks scoped to assets: {[r[0].asset_id for r in dense_results]}")

    # 3. Sparse query (TSV full-text search)
    # Note: Filter before ranking: WHERE asset_id IN (:scoped_ids) is within LIMIT 20 query
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
        .limit(20)
    )
    sparse_results = db.execute(sparse_stmt).all()
    logger.info(f"Hybrid retrieval: Sparse search returned {len(sparse_results)} chunks scoped to assets: {[r[0].asset_id for r in sparse_results]}")

    # 4. RRF Merging
    # k = 60
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
        rrf_dict[chunk.id]["rrf_score"] += 1.0 / (60.0 + rank)

    for rank, row in enumerate(sparse_results, 1):
        chunk = row[0]
        if chunk.id not in rrf_dict:
            rrf_dict[chunk.id] = {
                "chunk": chunk,
                "rrf_score": 0.0,
                "dense_rank": None,
                "sparse_rank": rank,
            }
        rrf_dict[chunk.id]["rrf_score"] += 1.0 / (60.0 + rank)

    # Sort all candidates by RRF score DESC
    sorted_candidates = sorted(rrf_dict.values(), key=lambda x: x["rrf_score"], reverse=True)
    # Filter to top 5 candidates
    top_5_candidates = sorted_candidates[:5]

    if not top_5_candidates:
        return {
            "status": "success",
            "chunks": [],
            "context": "",
        }

    # 5. Adjacent Chunk Stitching
    # Chunks are adjacent if same asset_id, same page_number, and chunk_index is contiguous (e.g. index i and i+1)
    chunks_for_stitch = [item["chunk"] for item in top_5_candidates]
    id_to_item = {item["chunk"].id: item for item in top_5_candidates}

    # Sort chunks by asset_id, page_number, and chunk_index to identify adjacent blocks
    chunks_sorted = sorted(chunks_for_stitch, key=lambda c: (c.asset_id, c.page_number, c.chunk_index))

    stitched_blocks = []
    for chunk in chunks_sorted:
        item = id_to_item[chunk.id]
        if stitched_blocks and (
            stitched_blocks[-1]["asset_id"] == chunk.asset_id
            and stitched_blocks[-1]["page_number"] == chunk.page_number
            and chunk.chunk_index == stitched_blocks[-1]["chunk_indices"][-1] + 1
        ):
            # Stitch content and append index
            stitched_blocks[-1]["chunk_indices"].append(chunk.chunk_index)
            stitched_blocks[-1]["content"] += " " + chunk.content
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
                "best_score": item["rrf_score"],
            })

    # Sort the stitched blocks back by their best score DESC to preserve RRF priority order
    stitched_blocks = sorted(stitched_blocks, key=lambda b: b["best_score"], reverse=True)

    # 6. Token Budget Enforcement (3000 tokens maximum)
    final_blocks = list(stitched_blocks)
    while len(final_blocks) > 0:
        # Build test doc string to count tokens
        context_str = ""
        for i, block in enumerate(final_blocks, 1):
            context_str += f"[{i}] [Asset ID: {block['asset_id']}, Trang: {block['page_number']}]\n{block['content']}\n\n"
        
        try:
            resp = client.models.count_tokens(
                model=settings.GEMINI_CHAT_MODEL,
                contents=context_str,
            )
            total_tokens = resp.total_tokens
        except Exception as e:
            logger.warning(f"Failed to call Gemini count_tokens, falling back to heuristic: {e}")
            total_tokens = len(context_str) // 3

        if total_tokens <= 3000 or len(final_blocks) == 1:
            break
        else:
            # Exceeded budget! Drop the block with the lowest rank (last index in sorted list)
            final_blocks.pop()

    # 7. Renumbering & Build final context string
    final_context_list = []
    final_context_str = ""
    for idx, block in enumerate(final_blocks, 1):
        from app.models.asset import Asset
        asset = db.get(Asset, block["asset_id"])
        file_name = asset.file_name if asset else f"Document_{block['asset_id']}"

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
