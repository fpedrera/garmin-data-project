# src/load.py
import os
import logging
import duckdb
import sys
import pandas as pd

import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def initialize_database():
    """
    Inicializa la base de datos DuckDB y crea tablas si no existen
    
    Returns:
        Conexión a la base de datos
    """
    logger.info(f"Inicializando base de datos en {config.DB_PATH}")
    
    # Conectar a la base de datos
    conn = duckdb.connect(config.DB_PATH)
    
    # Crear tablas si no existen
    conn.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        activityId VARCHAR,
        activityName VARCHAR,
        activityType VARCHAR,
        startTimeLocal TIMESTAMP,
        startTimeGMT TIMESTAMP,
        duration DOUBLE,
        distance DOUBLE,
        averageSpeed DOUBLE,
        averageHR DOUBLE,
        maxHR DOUBLE,
        calories DOUBLE,
        elevationGain DOUBLE,
        elevationLoss DOUBLE
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS steps (
        date DATE PRIMARY KEY,
        total_steps INTEGER
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS heart_rate (
        date DATE PRIMARY KEY,
        avg_heart_rate DOUBLE,
        min_heart_rate DOUBLE,
        max_heart_rate DOUBLE,
        resting_heart_rate DOUBLE
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS sleep (
        date DATE PRIMARY KEY,
        sleep_duration_hours DOUBLE,
        deep_sleep_hours DOUBLE,
        light_sleep_hours DOUBLE,
        rem_sleep_hours DOUBLE,
        awake_time_hours DOUBLE
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS weight (
        date DATE PRIMARY KEY,
        weight_kg DOUBLE,
        bmi DOUBLE,
        body_fat_percent DOUBLE,
        muscle_mass_kg DOUBLE,
        bone_mass_kg DOUBLE
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS stress (
        date DATE PRIMARY KEY,
        avg_stress_level DOUBLE,
        max_stress_level DOUBLE,
        stress_duration_mins DOUBLE,
        rest_stress_duration_mins DOUBLE,
        activity_stress_duration_mins DOUBLE,
        low_stress_duration_mins DOUBLE,
        medium_stress_duration_mins DOUBLE,
        high_stress_duration_mins DOUBLE
    )
    """)
    
    return conn

def load_from_csv(conn, table_name, csv_file, replace=False):
    """
    Carga datos desde un archivo CSV a una tabla en DuckDB
    
    Args:
        conn: Conexión a la base de datos
        table_name: Nombre de la tabla
        csv_file: Ruta del archivo CSV
        replace: Si es True, reemplaza los datos existentes; si es False, inserta
        
    Returns:
        Número de filas cargadas
    """
    if not os.path.exists(csv_file):
        logger.warning(f"El archivo {csv_file} no existe")
        return 0
    
    logger.info(f"Cargando datos desde {csv_file} a la tabla {table_name}...")
    
    if replace:
        # Truncar la tabla antes de cargar
        conn.execute(f"DELETE FROM {table_name}")
    
    # Cargar datos desde CSV
    query = f"""
    INSERT INTO {table_name}
    SELECT * FROM read_csv_auto('{csv_file}')
    """
    conn.execute(query)
    
    # Contar filas
    result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    count = result[0] if result else 0
    
    logger.info(f"Cargadas {count} filas en la tabla {table_name}")
    return count

def load_activities(conn, activities_csv, replace=False):
    """
    Carga actividades en la base de datos, con manejo especial debido a su estructura
    
    Args:
        conn: Conexión a la base de datos
        activities_csv: Ruta del archivo CSV de actividades
        replace: Si es True, reemplaza los datos existentes
        
    Returns:
        Número de filas cargadas
    """
    if not os.path.exists(activities_csv):
        logger.warning(f"El archivo {activities_csv} no existe")
        return 0
    
    logger.info(f"Cargando actividades desde {activities_csv}...")
    
    # Leer CSV con pandas primero para manejar la estructura
    df = pd.read_csv(activities_csv)
    
    # Seleccionar columnas relevantes si existen
    relevant_cols = [
        'activityId', 'activityName', 'activityType', 
        'startTimeLocal', 'startTimeGMT', 'duration', 'distance',
        'averageSpeed', 'averageHR', 'maxHR', 'calories',
        'elevationGain', 'elevationLoss'
    ]
    
    # Seleccionar solo las columnas que existen en el DataFrame
    existing_cols = [col for col in relevant_cols if col in df.columns]
    df_filtered = df[existing_cols]
    
    if replace:
        # Truncar la tabla antes de cargar
        conn.execute("DELETE FROM activities")
    
    # Crear tabla temporal
    temp_table = "temp_activities"
    conn.register(temp_table, df_filtered)
    
    # Insertar datos
    conn.execute(f"""
    INSERT INTO activities ({', '.join(existing_cols)})
    SELECT {', '.join(existing_cols)} FROM {temp_table}
    """)
    
    # Contar filas
    result = conn.execute("SELECT COUNT(*) FROM activities").fetchone()
    count = result[0] if result else 0
    
    logger.info(f"Cargadas {count} actividades en la base de datos")
    return count

def load_all_data(replace=False):
    """
    Carga todos los datos CSV en la base de datos DuckDB
    
    Args:
        replace: Si es True, reemplaza los datos existentes
        
    Returns:
        Diccionario con el número de filas cargadas por tabla
    """
    # Inicializar la base de datos
    conn = initialize_database()
    
    # Rutas de los archivos CSV
    activities_csv = os.path.join(config.DATA_DIR, "activities.csv")
    steps_csv = os.path.join(config.DATA_DIR, "steps.csv")
    heart_rate_csv = os.path.join(config.DATA_DIR, "heart_rate.csv")
    sleep_csv = os.path.join(config.DATA_DIR, "sleep.csv")
    weight_csv = os.path.join(config.DATA_DIR, "weight.csv")
    stress_csv = os.path.join(config.DATA_DIR, "stress.csv")
    
    # Cargar datos
    rows_loaded = {
        "activities": load_activities(conn, activities_csv, replace),
        "steps": load_from_csv(conn, "steps", steps_csv, replace),
        "heart_rate": load_from_csv(conn, "heart_rate", heart_rate_csv, replace),
        "sleep": load_from_csv(conn, "sleep", sleep_csv, replace),
        "weight": load_from_csv(conn, "weight", weight_csv, replace),
        "stress": load_from_csv(conn, "stress", stress_csv, replace)
    }
    
    # Ejecutar algunas consultas de validación
    logger.info("Validando datos cargados con consultas de ejemplo:")
    
    # Actividades por tipo
    activity_types = conn.execute("""
    SELECT activityType, COUNT(*) as count
    FROM activities
    GROUP BY activityType
    ORDER BY count DESC
    LIMIT 5
    """).fetchdf()
    
    logger.info("Top 5 tipos de actividad:")
    for _, row in activity_types.iterrows():
        logger.info(f"- {row['activityType']}: {row['count']}")
    
    # Estadísticas de pasos
    steps_stats = conn.execute("""
    SELECT 
        COUNT(*) as days,
        AVG(total_steps) as avg_steps,
        MAX(total_steps) as max_steps
    FROM steps
    """).fetchone()
    
    if steps_stats and steps_stats[0] > 0:
        logger.info(f"Estadísticas de pasos: {steps_stats[0]} días, Promedio: {steps_stats[1]:.0f}, Máximo: {steps_stats[2]}")
    
    # Cerrar conexión
    conn.close()
    
    return rows_loaded

if __name__ == "__main__":
    # Si se ejecuta directamente, cargar todos los datos
    load_all_data(replace=True)