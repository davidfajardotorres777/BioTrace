"""
Script de carga de datos de prueba para InmoCore.
Limpia las colecciones operativas y genera, para dos agencias de
ejemplo en Palermo (CABA): propiedades con descripciones realistas
(indexadas en ChromaDB), fotos simuladas en MinIO, clientes y
contratos. Una fracción de las propiedades en venta se publica con
precio anómalo a propósito, para poblar el panel de alertas.
"""

from faker import Faker
import random
from datetime import datetime, timedelta
from db_models.propiedad import Propiedad
from db_models.cliente import Cliente
from db_models.contrato import Contrato
from db_models.agencia import Agencia
from dao import AdminDAO, InmoCoreDAO, StorageDAO, VectorDAO

fake = Faker('es_AR')

def generar_datos_prueba():
    print("Conectando y limpiando base de datos, Storage y VectorDB...")
    admin_dao = AdminDAO()
    storage = StorageDAO()
    vector_dao = VectorDAO()
    
    # Limpieza
    admin_dao.col_agencias.delete_many({})
    admin_dao.db['propiedades'].delete_many({})
    admin_dao.db['clientes'].delete_many({})
    admin_dao.db['contratos'].delete_many({})
    admin_dao.db['alertas'].delete_many({})
    
    agencias_ids = []
    # Coordenadas alrededor de Palermo, Buenos Aires
    for nombre, lon, lat in [("Inmobiliaria Palermo Soho", -58.42, -34.58), ("Boutique Real Estate", -58.43, -34.59)]:
        agencia = Agencia(
            nombre=nombre, 
            direccion=fake.address(),
            ubicacion={"type": "Point", "coordinates": [lon, lat]}
        )
        a_id = admin_dao.insertar_agencia(agencia)
        agencias_ids.append(a_id)
        
    print(f"Creadas {len(agencias_ids)} agencias.")
    
    adjetivos = ["luminoso", "amplio", "renovado", "moderno", "clásico", "con vistas"]
    amenities = ["balcón al frente", "cochera doble", "piscina compartida", "terraza privada", "seguridad 24hs", "jardín amplio"]
    target = ["estudiantes", "familias numerosas", "parejas jóvenes", "inversores", "uso profesional"]

    for a_id in agencias_ids:
        dao = InmoCoreDAO(agencia_id=a_id)
        print(f"Generando datos para agencia {a_id}...")
        
        bucket_name = f"proptech-data-{a_id.lower()}"
        storage.asegurar_bucket(bucket_name)
        
        num_props = 5
        tipos = ["Casa", "Departamento", "PH", "Terreno"]
        
        for _ in range(num_props):
            # Coordenadas aleatorias cercanas a la agencia
            lon = -58.42 + random.uniform(-0.02, 0.02)
            lat = -34.58 + random.uniform(-0.02, 0.02)
            
            tipo = random.choice(tipos)
            operacion = random.choice(["Venta", "Alquiler"])
            
            # Generar alerta aleatoria bajando mucho el precio
            es_ganga = random.random() > 0.8
            if operacion == "Venta":
                precio = random.uniform(5000, 9500) if es_ganga else random.uniform(80000, 500000)
            else:
                precio = random.uniform(200, 2000)
                
            desc = f"{tipo} {random.choice(adjetivos)} con {random.choice(amenities)}. Ideal para {random.choice(target)}. Excelente ubicación cerca de transportes."
            
            prop = Propiedad(
                agencia_id=a_id,
                titulo=f"{tipo} en {fake.street_name()}",
                descripcion=desc,
                tipo=tipo,
                operacion=operacion,
                precio_usd=round(precio, 2),
                superficie_m2=round(random.uniform(30.0, 300.0), 2),
                habitaciones=random.randint(1, 5),
                ubicacion={"type": "Point", "coordinates": [lon, lat]}
            )
            p_id = dao.insertar_propiedad(prop)
            
            # Indexar descripción en ChromaDB
            vector_dao.indexar_descripcion(p_id, desc)
            
            # Subir fotos dummy a MinIO
            file_name = f"{p_id}_foto1.jpg"
            dummy_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" # Fake JPEG header
            storage.subir_archivo_bytes(bucket_name, file_name, dummy_content)
            
            # Cliente
            cliente = Cliente(
                agencia_id=a_id,
                dni=str(fake.random_int(min=10000000, max=99999999)),
                nombre=fake.first_name(),
                apellido=fake.last_name(),
                telefono=fake.phone_number(),
                email=fake.email()
            )
            c_id = dao.insertar_cliente(cliente)
            
            # Contrato
            contrato = Contrato(
                agencia_id=a_id,
                propiedad_id=p_id,
                cliente_id=c_id,
                tipo_contrato=operacion,
                monto_total=prop.precio_usd,
                fecha_inicio=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            dao.insertar_contrato(contrato)

    admin_dao.cerrar_conexion()
    print("Datos (MongoDB), Fotos (MinIO) y Búsqueda Semántica (ChromaDB) generados exitosamente.")

if __name__ == "__main__":
    generar_datos_prueba()
