"""
Módulo de acceso a datos de InmoCore.

Concentra los cuatro Data Access Objects del sistema:

- `AdminDAO`    : colecciones globales, sin tenancy (alta de agencias).
- `InmoCoreDAO` : colecciones operativas (propiedades, clientes,
                  contratos, alertas). Aplica multi-tenancy por
                  `agencia_id` en cada consulta y escritura.
- `StorageDAO`  : Object Storage en MinIO (fotos de propiedades).
- `VectorDAO`   : búsqueda semántica de descripciones en ChromaDB.
"""

from datetime import datetime, timezone

from pymongo import MongoClient
from bson.objectid import ObjectId
from minio import Minio
import io
import chromadb

from config_vars import (
    MONGO_URI, DB_NAME,
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE
)
from db_models.propiedad import Propiedad
from db_models.cliente import Cliente
from db_models.contrato import Contrato
from db_models.agencia import Agencia
from db_models.alerta import Alerta


class StorageDAO:
    """
    Data Access Object para interactuar con MinIO.
    Guarda y recupera las fotos en alta resolución de las propiedades,
    organizadas en un bucket por agencia.
    """

    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )

    def asegurar_bucket(self, bucket_name: str):
        """Crea el bucket si todavía no existe. Idempotente."""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def subir_archivo_bytes(self, bucket_name: str, object_name: str, data: bytes):
        """Sube un archivo a partir de bytes en memoria (fotos, PDFs de contratos, etc.)."""
        self.asegurar_bucket(bucket_name)
        return self.client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data)
        )

    def descargar_archivo_bytes(self, bucket_name: str, object_name: str) -> bytes:
        """Descarga un objeto de MinIO y devuelve su contenido crudo."""
        response = self.client.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


class VectorDAO:
    """
    Data Access Object para interactuar con ChromaDB.
    Indexa la descripción de cada propiedad como embedding y permite
    buscarlas por similitud semántica en lenguaje natural (por ejemplo,
    "departamento luminoso con pileta").
    """

    def __init__(self, db_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="descripciones_propiedades")

    def indexar_descripcion(self, propiedad_id: str, descripcion: str):
        """Agrega (o reemplaza) el embedding de la descripción de una propiedad."""
        if not descripcion:
            return
        self.collection.upsert(
            documents=[descripcion],
            metadatas=[{"propiedad_id": str(propiedad_id)}],
            ids=[str(propiedad_id)]
        )

    def eliminar_indice(self, propiedad_id: str):
        """Quita una propiedad del índice vectorial (por ejemplo, al eliminarla)."""
        try:
            self.collection.delete(ids=[str(propiedad_id)])
        except Exception:
            pass

    def buscar_similitud(self, query: str, n_results: int = 3):
        """Devuelve las propiedades cuya descripción es más similar semánticamente a `query`."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results


class AdminDAO:
    """
    DAO para colecciones globales (sin tenancy).
    Se usa antes de tener un `agencia_id`: para dar de alta agencias
    nuevas o para listar el padrón completo de tenants del sistema
    (por ejemplo, en la pantalla de login).
    """

    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.col_agencias = self.db['agencias']

    def insertar_agencia(self, agencia: Agencia) -> str:
        """Da de alta una nueva agencia inmobiliaria (tenant)."""
        data = agencia.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        result = self.col_agencias.insert_one(data)
        return str(result.inserted_id)

    def listar_agencias(self):
        """Devuelve todas las agencias registradas en el sistema."""
        agencias = []
        for a in self.col_agencias.find():
            a["_id"] = str(a["_id"])
            agencias.append(Agencia(**a))
        return agencias

    def cerrar_conexion(self):
        self.client.close()


class InmoCoreDAO:
    """
    Data Access Object operativo de InmoCore.

    Aplica multi-tenancy: se instancia con un `agencia_id` obligatorio
    y ese valor se usa como filtro en absolutamente todas las lecturas
    y escrituras, para que una agencia jamás pueda ver ni modificar
    datos de otra.
    """

    def __init__(self, agencia_id: str, uri=MONGO_URI, db_name=DB_NAME):
        self.agencia_id = ObjectId(agencia_id)
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

        # Referencias a colecciones operativas
        self.col_propiedades = self.db['propiedades']
        self.col_clientes = self.db['clientes']
        self.col_contratos = self.db['contratos']
        self.col_alertas = self.db['alertas']

    def _verificar_tenancy(self, data: dict) -> dict:
        """Fuerza el `agencia_id` del DAO en el documento, sin confiar en el valor recibido."""
        data["agencia_id"] = self.agencia_id
        return data

    # --- PROPIEDADES ---

    def insertar_propiedad(self, propiedad: Propiedad) -> str:
        """
        Inserta una propiedad nueva.

        REGLA DE NEGOCIO: si se publica en Venta con un precio menor a
        10.000 USD (probable error de carga o publicación fraudulenta),
        se dispara automáticamente una `Alerta` de tipo "Precio Anómalo"
        enlazada a la propiedad recién creada.
        """
        data = propiedad.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        data = self._verificar_tenancy(data)

        if data.get("operacion") == "Venta" and data.get("precio_usd", 999999) < 10000:
            alerta = Alerta(
                agencia_id=str(self.agencia_id),
                tipo_alerta="Precio Anómalo",
                mensaje=f"Propiedad registrada con precio de Venta sospechoso ({data['precio_usd']} USD).",
                entidad_referencia_id="PENDING"  # Se completa abajo con el id real
            )
            data_alerta = alerta.model_dump(by_alias=True, exclude_none=True)
            if "_id" in data_alerta and data_alerta["_id"] is None:
                del data_alerta["_id"]
            data_alerta = self._verificar_tenancy(data_alerta)
            alert_result = self.col_alertas.insert_one(data_alerta)
            alert_id = alert_result.inserted_id
        else:
            alert_id = None

        result = self.col_propiedades.insert_one(data)

        if alert_id:
            self.col_alertas.update_one(
                {"_id": alert_id},
                {"$set": {"entidad_referencia_id": str(result.inserted_id)}}
            )

        return str(result.inserted_id)

    def obtener_propiedad(self, propiedad_id: str) -> Propiedad:
        """Devuelve una propiedad puntual, siempre que pertenezca a la agencia actual."""
        data = self.col_propiedades.find_one({
            "_id": ObjectId(propiedad_id),
            "agencia_id": self.agencia_id
        })
        if data:
            data["_id"] = str(data["_id"])
            data["agencia_id"] = str(data["agencia_id"])
            return Propiedad(**data)
        return None

    def listar_propiedades(self, limit: int = 100):
        """Lista las propiedades de la agencia actual, más recientes primero."""
        props = []
        cursor = self.col_propiedades.find({"agencia_id": self.agencia_id}) \
            .sort("fecha_publicacion", -1).limit(limit)
        for p in cursor:
            p["_id"] = str(p["_id"])
            p["agencia_id"] = str(p["agencia_id"])
            props.append(Propiedad(**p))
        return props

    def actualizar_propiedad(self, propiedad_id: str, cambios: dict) -> bool:
        """
        Actualiza campos puntuales de una propiedad (por ejemplo, precio
        o descripción). El filtro incluye `agencia_id` para que no se
        pueda editar una propiedad de otra agencia aunque se conozca su id.
        """
        cambios.pop("_id", None)
        cambios.pop("agencia_id", None)
        result = self.col_propiedades.update_one(
            {"_id": ObjectId(propiedad_id), "agencia_id": self.agencia_id},
            {"$set": cambios}
        )
        return result.modified_count > 0

    def eliminar_propiedad(self, propiedad_id: str) -> bool:
        """Elimina una propiedad de la agencia actual."""
        result = self.col_propiedades.delete_one(
            {"_id": ObjectId(propiedad_id), "agencia_id": self.agencia_id}
        )
        return result.deleted_count > 0

    def buscar_propiedades_cerca_de(self, lat: float, lon: float, radio_km: float):
        """
        Consulta geoespacial `$nearSphere` sobre el índice `2dsphere`:
        busca propiedades de la agencia actual dentro de un radio (en km)
        alrededor de un punto.
        """
        pipeline = {
            "agencia_id": self.agencia_id,
            "ubicacion": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "$maxDistance": radio_km * 1000  # metros
                }
            }
        }
        props = []
        for p in self.col_propiedades.find(pipeline):
            p["_id"] = str(p["_id"])
            p["agencia_id"] = str(p["agencia_id"])
            props.append(Propiedad(**p))
        return props

    def reporte_propiedades_por_tipo(self):
        """
        Aggregation Pipeline: cuenta cuántas propiedades activas tiene la
        agencia agrupadas por tipo (Casa, Departamento, PH, Terreno),
        junto con el precio promedio de cada grupo. Se usa en el notebook
        de demostración y puede alimentar un gráfico en la UI.
        """
        pipeline = [
            {"$match": {"agencia_id": self.agencia_id}},
            {"$group": {
                "_id": "$tipo",
                "cantidad": {"$sum": 1},
                "precio_promedio_usd": {"$avg": "$precio_usd"}
            }},
            {"$sort": {"cantidad": -1}}
        ]
        return list(self.col_propiedades.aggregate(pipeline))

    # --- CLIENTES ---

    def insertar_cliente(self, cliente: Cliente) -> str:
        """Da de alta un cliente para la agencia actual."""
        data = cliente.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        data = self._verificar_tenancy(data)
        result = self.col_clientes.insert_one(data)
        return str(result.inserted_id)

    def listar_clientes(self, limit: int = 100):
        """Lista los clientes registrados en la agencia actual."""
        clientes = []
        for c in self.col_clientes.find({"agencia_id": self.agencia_id}).limit(limit):
            c["_id"] = str(c["_id"])
            c["agencia_id"] = str(c["agencia_id"])
            clientes.append(Cliente(**c))
        return clientes

    # --- CONTRATOS ---

    def insertar_contrato(self, contrato: Contrato) -> str:
        """
        Registra un contrato (venta o alquiler) entre un cliente y una
        propiedad de la agencia actual. `propiedad_id` y `cliente_id`
        se guardan como `ObjectId` para poder resolver referencias con
        `$lookup` en reportes futuros.
        """
        data = contrato.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        data = self._verificar_tenancy(data)
        data["propiedad_id"] = ObjectId(data["propiedad_id"])
        data["cliente_id"] = ObjectId(data["cliente_id"])
        result = self.col_contratos.insert_one(data)
        return str(result.inserted_id)

    def listar_contratos(self, limit: int = 100):
        """Lista los contratos de la agencia actual, más recientes primero."""
        contratos = []
        cursor = self.col_contratos.find({"agencia_id": self.agencia_id}) \
            .sort("fecha_inicio", -1).limit(limit)
        for c in cursor:
            c["_id"] = str(c["_id"])
            c["agencia_id"] = str(c["agencia_id"])
            c["propiedad_id"] = str(c["propiedad_id"])
            c["cliente_id"] = str(c["cliente_id"])
            contratos.append(Contrato(**c))
        return contratos

    # --- ALERTAS ---

    def listar_alertas(self):
        """Lista las alertas activas (sin resolver) de la agencia actual."""
        alertas = []
        for a in self.col_alertas.find({"agencia_id": self.agencia_id, "resuelta": False}):
            a["_id"] = str(a["_id"])
            a["agencia_id"] = str(a["agencia_id"])
            a["entidad_referencia_id"] = str(a["entidad_referencia_id"])
            alertas.append(Alerta(**a))
        return alertas

    def resolver_alerta(self, alerta_id: str) -> bool:
        """Marca una alerta como resuelta y registra la fecha de resolución."""
        result = self.col_alertas.update_one(
            {"_id": ObjectId(alerta_id), "agencia_id": self.agencia_id},
            {"$set": {
                "resuelta": True,
                "fecha_resolucion": datetime.now(timezone.utc)
            }}
        )
        return result.modified_count > 0

    def cerrar_conexion(self):
        self.client.close()
