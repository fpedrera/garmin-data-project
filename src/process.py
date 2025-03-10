# src/process.py
import os
import json
import logging
import pandas as pd
import sys

import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def process_activities(activities):
    """
    Procesa las actividades y las guarda en un CSV
    
    Args:
        activities: Lista de actividades de Garmin Connect
        
    Returns:
        DataFrame de pandas con los datos procesados
    """
    if not activities:
        logger.warning("No hay actividades para procesar")
        return None
    
    logger.info(f"Procesando {len(activities)} actividades...")
    
    # Convertir a DataFrame
    df = pd.DataFrame(activities)
    
    # Guardar en CSV
    output_file = os.path.join(config.DATA_DIR, "activities.csv")
    df.to_csv(output_file, index=False)
    logger.info(f"Guardadas {len(df)} actividades en {output_file}")
    
    return df

def process_health_data(health_data):
    """
    Procesa los datos de salud y los guarda en CSVs
    
    Args:
        health_data: Diccionario con los datos de salud por tipo
        
    Returns:
        Diccionario con DataFrames de los datos procesados
    """
    processed_dfs = {}
    
    for data_type, data in health_data.items():
        if not data:
            logger.warning(f"No hay datos de {data_type} para procesar")
            continue
        
        logger.info(f"Procesando datos de {data_type}...")
        processed_data = []
        
        for date, daily_data in data.items():
            if not daily_data:
                continue
            
            if data_type == "steps":
                # Procesar datos de pasos
                try:
                    daily_total = sum(item.get('steps', 0) for item in daily_data)
                    processed_data.append({
                        'date': date,
                        'total_steps': daily_total
                    })
                except Exception as e:
                    logger.debug(f"Error procesando pasos para {date}: {e}")
            
            elif data_type == "heart_rate":
                # Procesar datos de frecuencia cardíaca
                try:
                    if isinstance(daily_data, list) and daily_data:
                        hr_data = daily_data
                    elif isinstance(daily_data, dict) and 'heartRateValues' in daily_data:
                        hr_data = daily_data['heartRateValues']
                    else:
                        hr_data = []
                        
                    if hr_data:
                        hr_values = [item[1] for item in hr_data if len(item) >= 2 and item[1] > 0]
                        if hr_values:
                            processed_data.append({
                                'date': date,
                                'avg_heart_rate': sum(hr_values) / len(hr_values),
                                'min_heart_rate': min(hr_values),
                                'max_heart_rate': max(hr_values),
                                'resting_heart_rate': daily_data.get('restingHeartRate', None) 
                                    if isinstance(daily_data, dict) else None
                            })
                except Exception as e:
                    logger.debug(f"Error procesando frecuencia cardíaca para {date}: {e}")
            
            elif data_type == "sleep":
                # Procesar datos de sueño
                try:
                    if daily_data and isinstance(daily_data, dict) and 'sleepTimeSeconds' in daily_data:
                        processed_data.append({
                            'date': date,
                            'sleep_duration_hours': daily_data.get('sleepTimeSeconds', 0) / 3600,
                            'deep_sleep_hours': daily_data.get('deepSleepSeconds', 0) / 3600,
                            'light_sleep_hours': daily_data.get('lightSleepSeconds', 0) / 3600,
                            'rem_sleep_hours': daily_data.get('remSleepSeconds', 0) / 3600,
                            'awake_time_hours': daily_data.get('awakeSleepSeconds', 0) / 3600
                        })
                except Exception as e:
                    logger.debug(f"Error procesando sueño para {date}: {e}")
        
        # Convertir a DataFrame
        if processed_data:
            df = pd.DataFrame(processed_data)
            
            # Convertir fecha a datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # Guardar a CSV
            output_file = os.path.join(config.DATA_DIR, f"{data_type}.csv")
            df.to_csv(output_file, index=False)
            logger.info(f"Guardados {len(df)} registros de {data_type} en {output_file}")
            
            processed_dfs[data_type] = df
        else:
            logger.warning(f"No se pudieron procesar datos de {data_type}")
    
    return processed_dfs

def save_raw_data(activities, health_data):
    """
    Guarda los datos crudos en formato JSON para respaldo
    
    Args:
        activities: Lista de actividades
        health_data: Diccionario con datos de salud por tipo
    """
    if activities:
        raw_activities_file = os.path.join(config.DATA_DIR, "raw_activities.json")
        with open(raw_activities_file, 'w') as f:
            json.dump(activities, f)
        logger.info(f"Datos crudos de actividades guardados en {raw_activities_file}")
    
    for data_type, data in health_data.items():
        if data:
            raw_data_file = os.path.join(config.DATA_DIR, f"raw_{data_type}.json")
            with open(raw_data_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Datos crudos de {data_type} guardados en {raw_data_file}")

def process_all_data(activities, health_data, save_raw=True):
    """
    Procesa todos los datos y genera los CSV
    
    Args:
        activities: Lista de actividades
        health_data: Diccionario con datos de salud por tipo
        save_raw: Si es True, guarda también los datos crudos en JSON
        
    Returns:
        Tupla (activities_df, health_dataframes)
    """
    # Guardar datos crudos para respaldo
    if save_raw:
        save_raw_data(activities, health_data)
    
    # Procesar actividades
    activities_df = process_activities(activities)
    
    # Procesar datos de salud
    health_dataframes = process_health_data(health_data)
    
    return activities_df, health_dataframes

if __name__ == "__main__":
    logger.info("Módulo de procesamiento ejecutado directamente")