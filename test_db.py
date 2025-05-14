# test_db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()  # carrega SUPABASE_DB_URL do seu .env

engine = create_engine(os.getenv("SUPABASE_DB_URL"))
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Conexão OK:", result.all())
