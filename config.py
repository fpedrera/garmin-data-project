# config.py
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Credenciales de Garmin Connect (NUNCA hardcodear credenciales)
GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")

# Configuración de fechas
DEFAULT_START_DATE = (datetime.now() - timedelta(days=365*3)).strftime("%Y-%m-%d")  # 3 años atrás
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")  # Hoy

# Directorios
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Ruta de la base de datos DuckDB
DB_PATH = os.path.join(DATA_DIR, "garmin_data.duckdb")

# Tipos de datos a extraer
ACTIVITY_TYPES = []  # Lista vacía para extraer todos los tipos
HEALTH_DATA_TYPES = ["steps", "heart_rate", "sleep", "weight", "stress"]

# Configuración de la API
API_DELAY = 0.2  # Retraso entre llamadas a la API (segundos)