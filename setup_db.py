"""
Inicializa la base de datos de InmoCore: crea las colecciones
operativas y los índices necesarios para garantizar unicidad
(por ejemplo, DNI único por agencia) y para habilitar las
búsquedas geoespaciales y de alertas activas.
Se ejecuta una sola vez, antes de correr `seed.py`.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from config_vars import MONGO_URI, DB_NAME

def setup_database():
    print(f"Conectando a MongoDB en {MONGO_URI}...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Crear colecciones (si no existen) e indices
    print("Configurando colección 'agencias'...")
    agencias = db['agencias']
    agencias.create_index([("nombre", ASCENDING)], unique=True)
    agencias.create_index([("ubicacion", "2dsphere")])
    
    print("Configurando colección 'propiedades'...")
    propiedades = db['propiedades']
    propiedades.create_index([("agencia_id", ASCENDING), ("tipo", ASCENDING)])
    propiedades.create_index([("ubicacion", "2dsphere")])
    
    print("Configurando colección 'clientes'...")
    clientes = db['clientes']
    clientes.create_index([("agencia_id", ASCENDING), ("dni", ASCENDING)], unique=True)
    
    print("Configurando colección 'contratos'...")
    contratos = db['contratos']
    contratos.create_index([("agencia_id", ASCENDING), ("propiedad_id", ASCENDING)])
    
    print("Configurando colección 'alertas'...")
    alertas = db['alertas']
    alertas.create_index([("agencia_id", ASCENDING), ("resuelta", ASCENDING)])
    
    print(f"\n--OK-- Base de datos '{DB_NAME}' inicializada para INMOCORE.")
    client.close()

if __name__ == "__main__":
    setup_database()
