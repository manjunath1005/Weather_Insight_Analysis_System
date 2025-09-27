import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") 
WEATHER_API_URL = os.getenv("WEATHER_API_URL") 

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)
