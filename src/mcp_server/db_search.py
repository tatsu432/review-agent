import os
from typing import Any, Dict, Optional

import psycopg
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_model = os.getenv("EMBED_MODEL") or "text-embedding-3-small"


def embed(text: str) -> list[float]:
    return _client.embeddings.create(model=_model, input=[text]).data[0].embedding


DSN = os.getenv("DATABASE_URL")


def _goodness(
    vec_score: float, star_rating: Optional[float], review_count: Optional[int]
) -> float:
    s = vec_score or 0.0
    r = float(star_rating or 0.0)
    n = int(review_count or 0)
    # shrinkage against a prior mean for Tabelog in Tokyo wards (tune for your data)
    mu0, w0 = 3.50, 30
    rating_shrunk = (n * r + w0 * mu0) / (n + w0) if (n + w0) > 0 else mu0
    rating_norm = max(0.0, min(1.0, (rating_shrunk - 3.0) / 1.5))
    return 0.6 * s + 0.4 * rating_norm


def search_restaurants(
    query_text: str,
    ward: Optional[str] = None,
    max_dinner_budget: Optional[int] = None,
    smoking: Optional[str] = None,  # '禁煙'|'喫煙'|'分煙'|'加熱式のみ'
    with_children: Optional[bool] = None,
    category_hint: Optional[str] = None,
    k: int = 10,
) -> Dict[str, Any]:
    """
    Returns {status, results[], retryable:false}
    Each result: {restaurant_id, name, page_url, star_rating, review_count, categories, explain, score_goodness, score_semantic}
    """
    try:
        qvec = embed(query_text)

        sql = """
        WITH filt AS (
          SELECT r.restaurant_id, r.name, r.page_url, r.star_rating, r.review_count,
                 r.categories, r.seats, r.smoking, r.with_children, r.ward, r.area_hint,
                 r.retrieval_text_ja,
                 -- quick category filter (ILIKE) if hint present
                 CASE WHEN %(category_hint)s IS NOT NULL THEN
                     EXISTS (SELECT 1 FROM unnest(r.categories) c WHERE c ILIKE '%' || %(category_hint)s || '%')
                 ELSE TRUE END AS cat_ok
          FROM restaurants r
          WHERE (%(ward)s IS NULL OR r.ward = %(ward)s)
            AND (%(max_dinner)s IS NULL OR r.budget_dinner_max IS NULL OR r.budget_dinner_max <= %(max_dinner)s)
            AND (%(smoking)s IS NULL OR r.smoking = %(smoking)s)
            AND (%(with_children)s IS NULL OR r.with_children = %(with_children)s)
        )
        SELECT f.*, 1 - (v.embedding <=> %(qvec)s::vector) AS vec_score
        FROM filt f
        JOIN restaurant_vectors v USING (restaurant_id)
        WHERE f.cat_ok
        ORDER BY vec_score DESC
        LIMIT 50;
        """

        params = dict(
            ward=ward,
            max_dinner=max_dinner_budget,
            smoking=smoking,
            with_children=with_children,
            category_hint=category_hint,
            qvec=qvec,
        )

        results = []
        with psycopg.connect(DSN) as con, con.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [c.name for c in cur.description]
            for row in rows:
                rec = dict(zip(cols, row))
                g = _goodness(rec["vec_score"], rec["star_rating"], rec["review_count"])
                expl_bits = []
                if ward:
                    expl_bits.append(f"{ward}")
                if max_dinner_budget:
                    expl_bits.append(f"予算≤{max_dinner_budget}")
                if smoking:
                    expl_bits.append(f"{smoking}")
                if with_children is not None:
                    expl_bits.append("子連れ可" if with_children else "子連れ不可")
                if category_hint:
                    expl_bits.append(f"カテゴリ:{category_hint}")
                results.append(
                    {
                        "restaurant_id": rec["restaurant_id"],
                        "name": rec["name"],
                        "page_url": rec["page_url"],
                        "star_rating": float(rec["star_rating"])
                        if rec["star_rating"] is not None
                        else None,
                        "review_count": int(rec["review_count"])
                        if rec["review_count"] is not None
                        else None,
                        "categories": rec["categories"],
                        "score_semantic": float(rec["vec_score"] or 0.0),
                        "score_goodness": float(g),
                        "explain": "・".join(expl_bits)
                        if expl_bits
                        else "セマンティック一致が高い候補",
                    }
                )
        # final top-k by goodness
        results.sort(key=lambda r: r["score_goodness"], reverse=True)
        return {"status": "ok", "results": results[:k], "retryable": False}
    except Exception as e:
        return {"status": "error", "reason": str(e)[:200], "retryable": False}


def get_restaurant_by_name(name: str, min_score: float = 0.75) -> Dict[str, Any]:
    """
    Vector-search by restaurant name only and return a single restaurant dict if
    similarity >= min_score, else return {status:'ok', restaurant: None}.
    """
    try:
        qvec = embed(name)

        sql = """
        SELECT r.restaurant_id, r.name, r.page_url, r.star_rating, r.review_count,
               r.categories, r.address, r.ward, r.area_hint,
               1 - (v.embedding <=> %(qvec)s::vector) AS vec_score
        FROM restaurants r
        JOIN restaurant_vectors v USING (restaurant_id)
        ORDER BY vec_score DESC
        LIMIT 1;
        """

        with psycopg.connect(DSN) as con, con.cursor() as cur:
            cur.execute(sql, {"qvec": qvec})
            row = cur.fetchone()
            if not row:
                return {"status": "ok", "restaurant": None, "retryable": False}
            (
                restaurant_id,
                rname,
                page_url,
                star_rating,
                review_count,
                categories,
                address,
                ward,
                area_hint,
                vec_score,
            ) = row

            score = float(vec_score or 0.0)
            if score < min_score:
                return {"status": "ok", "restaurant": None, "retryable": False}

            restaurant = {
                "restaurant_id": restaurant_id,
                "name": rname,
                "page_url": page_url,
                "star_rating": float(star_rating) if star_rating is not None else None,
                "review_count": int(review_count) if review_count is not None else None,
                "categories": categories,
                "address": address,
                "ward": ward,
                "area_hint": area_hint,
                "score_semantic": score,
            }
            return {"status": "ok", "restaurant": restaurant, "retryable": False}
    except Exception as e:
        return {"status": "error", "reason": str(e)[:200], "retryable": False}
