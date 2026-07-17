from pymongo import MongoClient, ASCENDING, DESCENDING
from config_vars import MONGO_URI, DB_NAME

def setup_database():
    print(f"Conectando a MongoDB en {MONGO_URI}...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Crear colecciones (si no existen) e indices
    print("Configurando colección 'clinicas'...")
    clinicas = db['clinicas']
    clinicas.create_index([("nombre", ASCENDING)], unique=True)
    
    print("Configurando colección 'pacientes'...")
    pacientes = db['pacientes']
    # El dni es unico por clinica
    pacientes.create_index([("clinica_id", ASCENDING), ("dni", ASCENDING)], unique=True)
    pacientes.create_index([("clinica_id", ASCENDING), ("apellido", ASCENDING)])
    
    print("Configurando colección 'muestras'...")
    muestras = db['muestras']
    muestras.create_index([("clinica_id", ASCENDING), ("paciente_id", ASCENDING)])
    muestras.create_index([("clinica_id", ASCENDING), ("fecha_extraccion", DESCENDING)])
    
    print("Configurando colección 'analisis'...")
    analisis = db['analisis']
    analisis.create_index([("clinica_id", ASCENDING), ("muestra_id", ASCENDING)])
    
    print("Configurando colección 'alertas'...")
    alertas = db['alertas']
    alertas.create_index([("clinica_id", ASCENDING), ("resuelta", ASCENDING)])
    
    print(f"\n--OK-- Base de datos '{DB_NAME}' inicializada con índices multi-tenant correctos.")
    client.close()

if __name__ == "__main__":
    setup_database()
