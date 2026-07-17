import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "biotrace_db")
