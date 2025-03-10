# main.py
import os
import logging
import argparse
from datetime import datetime, timedelta
import sys
sys.path.append('/home/fpedrera/DEV')

import config

# Asegurarse de que los directorios necesarios existen
os.makedirs(config.DATA_DIR, exist_ok=True)
log_dir = os.path.join(config.DATA_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

# Ruta del archivo de log
log_file = os.path.join(log_dir, f"garmin_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ahora que el logging está configurado, po# main.py
import os
import logging
import argparse
from datetime import datetime, timedelta
import sys
sys.path.append('/home/fpedrera/DEV')

import config

# Asegurarse de que los directorios necesarios existen
os.makedirs(config.DATA_DIR, exist_ok=True)
log_dir = os.path.join(config.DATA_DIR, "logs")
os.makedirs(log_dir, exist_ok=True)

# Ruta del archivo de log
log_file = os.path.join(log_dir, f"garmin_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ahora que el logging está configurado, podemos importar los módulos
# que podrían usar logging durante la importación
from src.extract import extract_all_data
from src.process import process_all_data
from src.load import load_all_data

# Agregar un mensaje de comprobación
logger.info(f"Iniciando proceso ETL de Garmin Connect. Log guardado en {log_file}")

# Verificar que el logging está funcionando
test_log_message = f"Test de log - {datetime.now()}"
logger.debug("DEBUG: " + test_log_message)
logger.info("INFO: " + test_log_message)
logger.warning("WARNING: " + test_log_message)
logger.error("ERROR: " + test_log_message)

# Verificar que el archivo existe y tiene permisos de escritura
try:
    with open(log_file, 'a') as f:
        f.write("Test de escritura directa en el archivo de log\n")
    logger.info(f"Archivo de log creado correctamente en: {log_file}")
except Exception as e:
    print(f"Error al escribir en el archivo de log: {e}")

def check_credentials():
    """Verifica que las credenciales estén configuradas"""
    if not config.GARMIN_EMAIL or not config.GARMIN_PASSWORD:
        logger.error("❌ ERROR: No se han configurado las credenciales de Garmin Connect")
        logger.error("Por favor, establece las variables de entorno GARMIN_EMAIL y GARMIN_PASSWORD")
        logger.error("O crea un archivo .env con estas variables")
        sys.exit(1)
    else:
        logger.info(f"✅ Credenciales configuradas correctamente para: {config.GARMIN_EMAIL}")

def parse_args():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Extraer, procesar y cargar datos de Garmin Connect')
    
    parser.add_argument('--start-date', 
                        help='Fecha inicial en formato YYYY-MM-DD')
    
    parser.add_argument('--end-date', 
                        help='Fecha final en formato YYYY-MM-DD')
    
    parser.add_argument('--days', type=int, default=0,
                        help='Número de días hacia atrás desde hoy')
    
    parser.add_argument('--skip-extract', action='store_true',
                        help='Omitir la fase de extracción')
    
    parser.add_argument('--skip-process', action='store_true',
                        help='Omitir la fase de procesamiento')
    
    parser.add_argument('--skip-load', action='store_true',
                        help='Omitir la fase de carga en DuckDB')
    
    return parser.parse_args()

def main():
    # Verificar credenciales
    check_credentials()
    
    # Parsear argumentos
    args = parse_args()
    
    # Determinar fechas
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    
    if args.days > 0:
        start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    else:
        start_date = args.start_date or config.DEFAULT_START_DATE
    
    logger.info(f"Período de análisis: {start_date} a {end_date}")
    
    activities = None
    health_data = None
    
    # Fase 1: Extracción
    if not args.skip_extract:
        logger.info("=== FASE 1: EXTRACCIÓN DE DATOS ===")
        activities, health_data = extract_all_data(start_date, end_date)
    else:
        logger.info("Fase de extracción omitida según parámetros")
    
    # Fase 2: Procesamiento
    if not args.skip_process:
        logger.info("=== FASE 2: PROCESAMIENTO DE DATOS ===")
        if args.skip_extract:
            # Si se omitió la extracción, intentar cargar desde archivos JSON
            import json
            try:
                raw_activities_file = os.path.join(config.DATA_DIR, "raw_activities.json")
                if os.path.exists(raw_activities_file):
                    with open(raw_activities_file, 'r') as f:
                        activities = json.load(f)
                    logger.info(f"Cargados datos de actividades desde {raw_activities_file}")
                
                health_data = {}
                for data_type in config.HEALTH_DATA_TYPES:
                    raw_data_file = os.path.join(config.DATA_DIR, f"raw_{data_type}.json")
                    if os.path.exists(raw_data_file):
                        with open(raw_data_file, 'r') as f:
                            health_data[data_type] = json.load(f)
                        logger.info(f"Cargados datos de {data_type} desde {raw_data_file}")
            except Exception as e:
                logger.error(f"Error cargando datos crudos: {e}")
        
        if activities or health_data:
            activities_df, health_dataframes = process_all_data(activities, health_data)
        else:
            logger.warning("No hay datos para procesar")
    else:
        logger.info("Fase de procesamiento omitida según parámetros")
    
    # Fase 3: Carga en DuckDB
    if not args.skip_load:
        logger.info("=== FASE 3: CARGA EN DUCKDB ===")
        rows_loaded = load_all_data(replace=True)
        
        # Resumen de filas cargadas
        logger.info("Resumen de carga en DuckDB:")
        for table, count in rows_loaded.items():
            logger.info(f"- {table}: {count} filas")
    else:
        logger.info("Fase de carga en DuckDB omitida según parámetros")
    
    logger.info("Proceso ETL completado!")

if __name__ == "__main__":
    main()