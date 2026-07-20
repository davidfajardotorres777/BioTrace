from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Propiedad(BaseModel):
    """
    Documento de la colección `propiedades`.
    Representa un inmueble publicado por una agencia (venta o alquiler).

    Siempre pertenece a una `agencia_id`: el `InmoCoreDAO` filtra por ese
    campo en cada consulta para que ninguna agencia pueda ver propiedades
    de otra. El campo `ubicacion` (GeoJSON Point) habilita la búsqueda
    geoespacial `$nearSphere` implementada en
    `InmoCoreDAO.buscar_propiedades_cerca_de`.

    La `descripcion` se indexa además en ChromaDB (ver `VectorDAO`) para
    permitir búsquedas semánticas por lenguaje natural, y las
    `fotos_paths` apuntan a los objetos guardados en MinIO mediante
    `StorageDAO`.

    Si el precio de una propiedad en venta es sospechosamente bajo
    (< 10.000 USD), `InmoCoreDAO.insertar_propiedad` dispara
    automáticamente una `Alerta` de tipo "Precio Anómalo".
    """

    id: str = Field(alias="_id", default=None)
    agencia_id: str
    titulo: str
    descripcion: str
    tipo: str  # Casa, Departamento, PH, Terreno
    operacion: str  # Venta, Alquiler
    precio_usd: float
    superficie_m2: float
    habitaciones: int
    ubicacion: Optional[dict] = None  # GeoJSON Point
    fotos_paths: Optional[List[str]] = []  # Paths a los objetos en MinIO
    fecha_publicacion: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
