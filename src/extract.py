# Importaciones necesarias
import time
import logging
from datetime import datetime, timedelta
import sys

# Importar el cliente de Garmin Connect
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError
)

# Importar configuración
import config

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Función para inicializar el cliente de Garmin
def init_garmin_client():
    """Inicializa el cliente de Garmin Connect"""
    if not config.GARMIN_EMAIL or not config.GARMIN_PASSWORD:
        logger.error("Credenciales no configuradas")
        return None
    
    try:
        client = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)
        client.login()
        logger.info("Autenticación exitosa")
        return client
    except Exception as e:
        logger.error(f"Error de autenticación: {e}")
        return None

# Función para obtener actividades
def fetch_activities(client, start_date=None, end_date=None):
    """Obtiene actividades de Garmin Connect"""
    start_date = start_date or config.DEFAULT_START_DATE
    end_date = end_date or config.DEFAULT_END_DATE
    
    logger.info(f"Obteniendo actividades desde {start_date} hasta {end_date}")
    
    try:
        activities = client.get_activities_by_date(start_date, end_date)
        logger.info(f"Obtenidas {len(activities)} actividades")
        return activities
    except Exception as e:
        logger.error(f"Error obteniendo actividades: {e}")
        return []

# Función para obtener datos de salud
def fetch_health_data(client, data_type, start_date=None, end_date=None):
    """Obtiene datos de salud (pasos, FC, etc.)"""
    start_date = start_date or config.DEFAULT_START_DATE
    end_date = end_date or config.DEFAULT_END_DATE
    
    logger.info(f"Obteniendo datos de {data_type}")
    
    # Convertir a formato datetime
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    data_dict = {}
    current_date = start_dt
    
    while current_date <= end_dt:
        date_str = current_date.strftime("%Y-%m-%d")
        
        try:
            if data_type == "steps":
                data = client.get_steps_data(date_str)
            elif data_type == "heart_rate":
                data = client.get_heart_rates(date_str)
            elif data_type == "sleep":
                data = client.get_sleep_data(date_str)
            elif data_type == "weight":
                data = client.get_body_composition(date_str)
            else:
                logger.error(f"Tipo de datos desconocido: {data_type}")
                break
                
            data_dict[date_str] = data
            time.sleep(0.2)  # Evitar límites de tasa
            
        except Exception as e:
            logger.warning(f"Error para {date_str}: {e}")
            data_dict[date_str] = None
        
        current_date += timedelta(days=1)
    
    logger.info(f"Datos de {data_type} obtenidos para {len(data_dict)} días")
    return data_dict

# La función que estamos buscando
def extract_all_data(start_date=None, end_date=None):
    """
    Extrae todos los datos de Garmin Connect
    
    Args:
        start_date: Fecha inicial (formato YYYY-MM-DD)
        end_date: Fecha final (formato YYYY-MM-DD)
        
    Returns:
        Tupla (actividades, datos_salud)
    """
    # Inicializar cliente
    client = init_garmin_client()
    if not client:
        logger.error("No se pudo inicializar el cliente")
        return None, None
    
    # Obtener actividades
    activities = fetch_activities(client, start_date, end_date)
    
    # Obtener datos de salud
    health_data = {}
    for data_type in config.HEALTH_DATA_TYPES:
        health_data[data_type] = fetch_health_data(client, data_type, start_date, end_date)
    
    return activities, health_data

# Para ejecutar directamente
if __name__ == "__main__":
    print("Módulo extract.py ejecutado directamente")