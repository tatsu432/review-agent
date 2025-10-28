# embed_openai.py
import os

import psycopg
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # This loads the .env file

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed(texts):
    # Ensure all elements in texts are strings
    resp = client.embeddings.create(model=os.getenv("EMBED_MODEL"), input=texts)
    return [e.embedding for e in resp.data]


def embed_to_db(dsn: str) -> None:
    with psycopg.connect(dsn) as con, con.cursor() as cur:
        cur.execute("""
        SELECT restaurant_id, name
        FROM restaurants
        WHERE restaurant_id NOT IN (SELECT restaurant_id FROM restaurant_vectors)
        AND name IS NOT NULL AND name <> ''
        LIMIT 1000
        """)
        rows = cur.fetchall()
        # Sanitize and filter input names to prevent invalid embedding requests
        filtered_rows = []
        for rid, name in rows:
            text = (
                name
                if isinstance(name, str)
                else str(name)
                if name is not None
                else None
            )
            if text is None:
                continue
            text = text.strip()
            if text == "":
                continue
            filtered_rows.append((rid, text))

        if not filtered_rows:
            con.commit()
            return

        batch_texts = [text for _, text in filtered_rows]
        embs = embed(batch_texts)
        for (rid, _), vec in zip(filtered_rows, embs):
            cur.execute(
                """
            INSERT INTO restaurant_vectors (restaurant_id, embedding)
            VALUES (%s, %s)
            ON CONFLICT (restaurant_id) DO UPDATE SET embedding=EXCLUDED.embedding, updated_at=now()
            """,
                (rid, vec),
            )
        con.commit()
