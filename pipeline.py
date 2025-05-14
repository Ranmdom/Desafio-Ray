"""
Pipeline de ETL: extrai vídeos de uma playlist YouTube, filtra por data, e faz upsert no banco (Supabase/Postgres).
"""

import os
import logging
from dotenv import load_dotenv
import pandas as pd
from googleapiclient.discovery import build
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )


def load_env():
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    db_url  = os.getenv("SUPABASE_DB_URL")
    if not api_key or not db_url:
        logging.error("Variáveis de ambiente YOUTUBE_API_KEY e SUPABASE_DB_URL são obrigatórias")
        raise EnvironmentError("Missing environment variables")
    return api_key, db_url


def get_playlist_video_ids(youtube, playlist_id: str) -> list[str]:
    ids = []
    next_token = None
    while True:
        resp = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_token,
        ).execute()
        for item in resp.get("items", []):
            pub = item["snippet"]["publishedAt"]
            # filtra vídeos de 2024
            if "2024-01-01T00:00:00Z" <= pub < "2025-01-01T00:00:00Z":
                ids.append(item["snippet"]["resourceId"]["videoId"])
        next_token = resp.get("nextPageToken")
        if not next_token:
            break
    logging.info(f"Total vídeos coletados: {len(ids)}")
    return ids


def get_videos_details(youtube, video_ids: list[str]) -> pd.DataFrame:
    rows = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        resp = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(batch),
        ).execute()
        for v in resp.get("items", []):
            s = v.get("statistics", {})
            rows.append({
                "videoId":      v["id"],
                "title":        v["snippet"]["title"],
                "publishedAt":  v["snippet"]["publishedAt"],
                "viewCount":    int(s.get("viewCount", 0)),
                "likeCount":    int(s.get("likeCount", 0)),
                "commentCount": int(s.get("commentCount", 0)),
            })
    return pd.DataFrame(rows)


def upsert_to_db(df: pd.DataFrame, db_url: str):
    engine = create_engine(db_url, echo=False, future=True)
    with engine.begin() as conn:
        # cria tabela se não existir
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS f1_highlights (
            videoId      TEXT PRIMARY KEY,
            title        TEXT,
            publishedAt  TIMESTAMPTZ,
            viewCount    INTEGER,
            likeCount    INTEGER,
            commentCount INTEGER
        );
        """))
        # upsert
        for row in df.to_dict(orient="records"):
            stmt = text("""
            INSERT INTO f1_highlights (videoId, title, publishedAt, viewCount, likeCount, commentCount)
            VALUES (:videoId, :title, :publishedAt, :viewCount, :likeCount, :commentCount)
            ON CONFLICT (videoId) DO UPDATE SET
                title        = EXCLUDED.title,
                publishedAt  = EXCLUDED.publishedAt,
                viewCount    = EXCLUDED.viewCount,
                likeCount    = EXCLUDED.likeCount,
                commentCount = EXCLUDED.commentCount;
            """)
            conn.execute(stmt, row)
    logging.info("Upsert concluído no banco de dados")


def main():
    setup_logging()
    api_key, db_url = load_env()
    youtube = build("youtube", "v3", developerKey=api_key)
    playlist_id = os.getenv("YOUTUBE_PLAYLIST_ID", "PLfoNZDHitwjUv0pjTwlV1vzaE0r7UDVDR")

    ids = get_playlist_video_ids(youtube, playlist_id)
    df = get_videos_details(youtube, ids)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"])
    upsert_to_db(df, db_url)
    logging.info("Pipeline concluído com sucesso")

if __name__ == "__main__":
    main()