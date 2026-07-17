from pymongo import MongoClient, ASCENDING, DESCENDING
from config_vars import MONGO_URI, DB_NAME

def setup_database():
    print(f"Conectando a MongoDB en {MONGO_URI}...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Crear colecciones (si no existen) e indices
    print("Configurando colección 'pacientes'...")
    pacientes = db['pacientes']
    pacientes.create_index([("dni", ASCENDING)], unique=True)
    pacientes.create_index([("apellido", ASCENDING), ("nombre", ASCENDING)])
    
    print("Configurando colección 'muestras'...")
    muestras = db['muestras']
    muestras.create_index([("paciente_id", ASCENDING)])
    muestras.create_index([("tipo_muestra", ASCENDING)])
    muestras.create_index([("fecha_extraccion", DESCENDING)])
    
    print("Configurando colección 'analisis'...")
    analisis = db['analisis']
    analisis.create_index([("muestra_id", ASCENDING)])
    analisis.create_index([("tipo_analisis", ASCENDING)])
    
    print(f"\n--OK-- Base de datos '{DB_NAME}' inicializada con índices correctos.")
    client.close()

if __name__ == "__main__":
    setup_database()
