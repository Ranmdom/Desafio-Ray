# test_env.py
import os
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
print("arquivo .env encontrado em:", dotenv_path)

loaded = load_dotenv(dotenv_path)
print("load_dotenv retornou:", loaded)
print("SUPABASE_DB_URL =", os.getenv("SUPABASE_DB_URL"))
