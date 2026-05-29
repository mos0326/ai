"""ベクトル類似検索ユーティリティ（コサイン類似度）。

SQLite では pgvector が使えないため、候補ベクトルを Python に読み込んで
numpy でコサイン類似度を計算する。個人利用（記憶 数百〜数千件）の規模なら
これで十分に高速。Postgres + pgvector へ移す場合はこの関数を置き換える。
"""

from __future__ import annotations

from typing import Sequence, TypeVar

import numpy as np

T = TypeVar("T")


def cosine_topk(
    query: Sequence[float],
    items: list[tuple[T, Sequence[float] | None]],
    k: int = 6,
    min_similarity: float = 0.0,
) -> list[tuple[T, float]]:
    """query に近い順に items を並べ、上位 k 件を (item, score) で返す。

    items は (任意オブジェクト, embedding) のリスト。embedding が None または
    次元が query と異なるものはスキップする。
    """
    q = np.asarray(query, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm == 0 or q.size == 0:
        return []
    q = q / q_norm

    scored: list[tuple[T, float]] = []
    for obj, emb in items:
        if emb is None:
            continue
        v = np.asarray(emb, dtype=np.float32)
        if v.size != q.size:
            continue  # プロバイダ変更などで次元が異なる場合は比較しない
        v_norm = np.linalg.norm(v)
        if v_norm == 0:
            continue
        sim = float(np.dot(q, v / v_norm))
        if sim >= min_similarity:
            scored.append((obj, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
