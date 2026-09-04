#!/usr/bin/env python3
"""
Controlled Re-ingestion Script for Demo Assets.
Allows targeted re-ingestion of specific assets with Sentence-Aware chunking,
3-field metadata, and configurable embedding providers (Gemini / Jina).
Requires explicit user confirmation before executing to protect API quota.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure backend root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.document import Document
from app.rag.ingestion.pipeline import ingest_asset


def list_assets(db) -> list[Asset]:
    stmt = (
        select(Asset, Document.title)
        .outerjoin(Document, Asset.document_id == Document.id)
        .order_by(Asset.id.asc())
    )
    results = db.execute(stmt).all()

    print("\n" + "=" * 80)
    print(f"{'ID':<5} | {'File Name':<35} | {'Document Title':<25} | {'Chunks':<6} | {'Status':<10}")
    print("-" * 80)
    assets = []
    for asset, doc_title in results:
        assets.append(asset)
        d_title = (doc_title[:22] + "...") if doc_title and len(doc_title) > 25 else (doc_title or "-")
        fname = (asset.file_name[:32] + "...") if len(asset.file_name) > 35 else asset.file_name
        status_str = asset.ingestion_status.value if hasattr(asset.ingestion_status, "value") else str(asset.ingestion_status)
        print(f"{asset.id:<5} | {fname:<35} | {d_title:<25} | {asset.chunk_count or 0:<6} | {status_str:<10}")
    print("=" * 80 + "\n")
    return assets


def main():
    parser = argparse.ArgumentParser(
        description="Targeted re-ingestion tool for knowledge sharing platform demo assets."
    )
    parser.add_argument(
        "--asset-ids",
        type=str,
        help="Comma-separated list of Asset IDs to re-ingest (e.g., --asset-ids 2 or --asset-ids 2,3,4)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Re-ingest ALL existing assets in the database.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing assets in database and exit without ingesting.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt and proceed with re-ingestion immediately.",
    )

    args = parser.parse_args()
    db = SessionLocal()

    try:
        if args.list or (not args.asset_ids and not args.all):
            print("📋 DANH SÁCH ASSETS HIỆN CÓ TRONG HỆ THỐNG:")
            list_assets(db)
            if not args.asset_ids and not args.all:
                print("ℹ Để re-ingest các asset, hãy chạy lệnh:")
                print("   python scripts/reingest_demo.py --asset-ids <id1,id2,...>")
                print("   Hoặc re-ingest toàn bộ: python scripts/reingest_demo.py --all")
            return

        if args.all:
            selected_assets = db.execute(select(Asset).order_by(Asset.id.asc())).scalars().all()
            target_ids = [a.id for a in selected_assets]
        else:
            # Parse requested asset IDs
            raw_ids = [s.strip() for s in args.asset_ids.split(",") if s.strip()]
            try:
                target_ids = [int(x) for x in raw_ids]
            except ValueError:
                print(f"❌ Lỗi: Tham số --asset-ids phải là các số nguyên phân tách bởi dấu phẩy. Nhận được: '{args.asset_ids}'")
                sys.exit(1)

            if not target_ids:
                print("❌ Lỗi: Không có asset_id hợp lệ nào được cung cấp.")
                sys.exit(1)

            # Query and validate target assets
            selected_assets = []
            for aid in target_ids:
                asset = db.get(Asset, aid)
                if not asset:
                    print(f"❌ Không tìm thấy Asset với ID={aid} trong cơ sở dữ liệu.")
                    sys.exit(1)
                selected_assets.append(asset)

        print("\n" + "=" * 70)
        print("   XÁC NHẬN RE-INGEST TÀI LIỆU DEMO")
        print("=" * 70)
        print("Danh sách tài liệu sẽ được re-ingest (Sentence-Aware Chunking + Embeddings):")
        for a in selected_assets:
            print(f" • [ID {a.id}] {a.file_name} (Chunks hiện tại: {a.chunk_count or 0})")

        print("\n⚠ CẢNH BÁO: Quá trình này sẽ xóa embeddings cũ và gọi API embedding mới.")
        print(f"Tổng số tài liệu cần re-ingest: {len(selected_assets)}")

        if not args.yes:
            confirm = input("\nBạn có chắc chắn muốn tiếp tục? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Đã hủy thao tác re-ingest.")
                return

        print("\n🚀 Bắt đầu quá trình re-ingest...\n")
        start_all = time.perf_counter()
        success_count = 0

        for idx, asset in enumerate(selected_assets, 1):
            print(f"[{idx}/{len(selected_assets)}] Đang xử lý Asset ID {asset.id}: '{asset.file_name}'...")
            t0 = time.perf_counter()
            success = ingest_asset(asset.id, db)
            elapsed = time.perf_counter() - t0

            if success:
                db.refresh(asset)
                success_count += 1
                print(f"   ✔ Hoàn thành Asset ID {asset.id} | Số chunks mới: {asset.chunk_count} | Thời gian: {elapsed:.2f}s\n")
            else:
                print(f"   ❌ Thất bại khi ingest Asset ID {asset.id} (Lỗi: {asset.ingestion_error})\n")

        total_elapsed = time.perf_counter() - start_all
        print("=" * 70)
        print(f"✔ HOÀN TẤT RE-INGEST: {success_count}/{len(selected_assets)} thành công trong {total_elapsed:.2f}s.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()

