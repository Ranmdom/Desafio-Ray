import os
import logging
import re
import unicodedata
from dotenv import load_dotenv
import pandas as pd
from googleapiclient.discovery import build
from sqlalchemy import create_engine, text

# lista de pilotos para extrair dos títulos
DRIVERS = [
    "Lewis Hamilton", "Max Verstappen", "Charles Leclerc",
    "Lando Norris", "Sergio Pérez", "George Russell",
    # … etc.
]

# mapeia palavra-chave → região amigável (ou circuito)
CIRCUITS = {
    "Monaco":                    "Mônaco (Monte Carlo)",
    "Silverstone":               "Reino Unido (Silverstone)",
    "Interlagos":                "Brasil (São Paulo)",
    "Spa":                       "Bélgica (Spa-Francorchamps)",
    "Suzuka":                    "Japão (Suzuka)",
    "Imola":                     "Itália (Imola)",
    "Mexico City":               "México (Cidade do México)",
    "Azerbaijan":                "Azerbaijão (Baku)",
    "Miami":                     "EUA (Miami)",
    "Bahrain":                   "Bahrain (Sakhir)",
    "Australian":                "Austrália (Melbourne)",
    "Austrian":                  "Áustria (Spielberg)",
    "Dutch":                     "Países Baixos (Zandvoort)",
    "Canadian":                  "Canadá (Montreal)",
    "Sao Paulo":                 "Brasil (São Paulo/Interlagos)",
    "Chinese":                   "China (Xangai)",
    "United States":             "EUA (Austin)",
    "Qatar":                     "Qatar (Lusail)",
    "Saudi Arabian":             "Arábia Saudita (Jeddah)",
    "Spanish":                   "Espanha (Barcelona)",
    "Belgian":                   "Bélgica (Spa-Francorchamps)",
    "Abu Dhabi":                 "Emirados Árabes (Abu Dhabi)",
    "Singapore":                 "Singapura (Singapore)",
    "Las Vegas":                 "EUA (Las Vegas)",
    "Italian":                   "Itália (Monza)",
    "Emilia Romagna":            "Itália (Imola)",
    "Hungarian":                 "Hungria (Budapeste)",
    "British":                   "Reino Unido (Silverstone)",
    "Japanese":                  "Japão (Suzuka)"
}

# normaliza texto removendo acentos e convertendo para lowercase

def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn').lower()

# detecta região a partir do título quando lat/lon não estiver disponível
def detect_region_from_title(title: str) -> str:
    norm_title = normalize_text(title)
    for key, region in CIRCUITS.items():
        if normalize_text(key) in norm_title:
            return region
    return "Região desconhecida"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

def load_env():
    load_dotenv()
    api_key     = os.getenv("YOUTUBE_API_KEY")
    db_url      = os.getenv("SUPABASE_DB_URL")
    playlist_id = os.getenv("YOUTUBE_PLAYLIST_ID", "")
    if not api_key or not db_url or not playlist_id:
        missing = [k for k,v in {
            'YOUTUBE_API_KEY': api_key,
            'SUPABASE_DB_URL': db_url,
            'YOUTUBE_PLAYLIST_ID': playlist_id
        }.items() if not v]
        logging.error(f"Variáveis faltando: {missing}")
        raise EnvironmentError("Variáveis de ambiente obrigatórias faltando")
    return api_key, db_url, playlist_id


def get_playlist_video_ids(youtube, playlist_id: str) -> list[str]:
    ids, next_token = [], None
    while True:
        resp = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_token
        ).execute()
        for it in resp.get("items", []):
            pub = it["snippet"]["publishedAt"]
            if "2024-01-01T00:00:00Z" <= pub < "2025-01-01T00:00:00Z":
                ids.append(it["snippet"]["resourceId"]["videoId"])
        next_token = resp.get("nextPageToken")
        if not next_token:
            break
    logging.info(f"Coletados {len(ids)} vídeos de 2024")
    return ids


def get_videos_details(youtube, video_ids: list[str]) -> pd.DataFrame:
    rows = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        resp = youtube.videos().list(
            part="snippet,statistics,recordingDetails",
            id=",".join(batch)
        ).execute()
        for v in resp.get("items", []):
            s = v.get("statistics", {})
            loc = v.get("recordingDetails", {}).get("location", {})
            title = v["snippet"]["title"]
            driver = next((d for d in DRIVERS if normalize_text(d) in normalize_text(title)), "Outro/Desconhecido")

            lat = loc.get("latitude")
            lon = loc.get("longitude")
            region = None
            if lat is None or lon is None:
                region = detect_region_from_title(title)

            rows.append({
                "videoId":      v["id"],
                "title":        title,
                "publishedAt":  v["snippet"]["publishedAt"],
                "viewCount":    int(s.get("viewCount", 0)),
                "likeCount":    int(s.get("likeCount", 0)),
                "commentCount": int(s.get("commentCount", 0)),
                "latitude":     lat,
                "longitude":    lon,
                "driver":       driver,
                "region":       region
            })
    df = pd.DataFrame(rows)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"])
    df["year"]    = df["publishedAt"].dt.year
    df["month"]   = df["publishedAt"].dt.month
    df["day"]     = df["publishedAt"].dt.day
    df["weekday"] = df["publishedAt"].dt.day_name()
    return df


def upsert_to_db(df: pd.DataFrame, db_url: str):
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.f1_highlights (
          videoId      TEXT PRIMARY KEY,
          title        TEXT,
          publishedAt  TIMESTAMPTZ,
          viewCount    INTEGER,
          likeCount    INTEGER,
          commentCount INTEGER,
          latitude     DOUBLE PRECISION,
          longitude    DOUBLE PRECISION,
          driver       TEXT,
          region       TEXT,
          year         INTEGER,
          month        INTEGER,
          day          INTEGER,
          weekday      TEXT
        );
        """))

        upsert = text("""
        INSERT INTO public.f1_highlights
          (videoId, title, publishedAt, viewCount, likeCount, commentCount,
           latitude, longitude, driver, region, year, month, day, weekday)
        VALUES
          (:videoId, :title, :publishedAt, :viewCount, :likeCount, :commentCount,
           :latitude, :longitude, :driver, :region, :year, :month, :day, :weekday)
        ON CONFLICT (videoId) DO UPDATE SET
          title        = EXCLUDED.title,
          publishedAt  = EXCLUDED.publishedAt,
          viewCount    = EXCLUDED.viewCount,
          likeCount    = EXCLUDED.likeCount,
          commentCount = EXCLUDED.commentCount,
          latitude     = EXCLUDED.latitude,
          longitude    = EXCLUDED.longitude,
          driver       = EXCLUDED.driver,
          region       = EXCLUDED.region,
          year         = EXCLUDED.year,
          month        = EXCLUDED.month,
          day          = EXCLUDED.day,
          weekday      = EXCLUDED.weekday;
        """)

        for record in df.to_dict("records"):
            conn.execute(upsert, record)

        conn.execute(text("CREATE SCHEMA IF NOT EXISTS reporting;"))

        conn.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS reporting.f1_monthly_summary AS
        SELECT
          year,
          month,
          COUNT(*)          AS total_videos,
          SUM(viewCount)    AS total_views,
          AVG(likeCount)    AS avg_likes,
          SUM(commentCount) AS total_comments
        FROM public.f1_highlights
        GROUP BY year, month
        ORDER BY year, month;
        """))

        conn.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS reporting.f1_driver_summary AS
        SELECT
          driver,
          COUNT(*)          AS videos_count,
          SUM(viewCount)    AS views_total,
          SUM(commentCount) AS comments_total,
          AVG(likeCount)    AS likes_avg
        FROM public.f1_highlights
        GROUP BY driver
        ORDER BY comments_total DESC;
        """))

    logging.info("ETL concluído e views de reporting criadas")


def main():
    setup_logging()
    api_key, db_url, pl_id = load_env()
    youtube = build("youtube", "v3", developerKey=api_key)
    ids = get_playlist_video_ids(youtube, pl_id)
    df  = get_videos_details(youtube, ids)
    upsert_to_db(df, db_url)

if __name__ == "__main__":
    main()
