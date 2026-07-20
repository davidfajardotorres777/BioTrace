from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Agencia(BaseModel):
    """
    Documento de la colección `agencias`.
    Representa al tenant raíz del sistema: una inmobiliaria que opera
    de forma aislada dentro de InmoCore. El campo `_id` de este documento
    es el `agencia_id` que se propaga a todas las colecciones operativas
    (propiedades, clientes, contratos, alertas) para garantizar el
    aislamiento multi-tenant.

    El campo `ubicacion` es un GeoJSON Point y habilita, junto con el
    índice `2dsphere` creado en `setup_db.py`, futuras búsquedas de
    agencias por proximidad.
    """

    id: str = Field(alias="_id", default=None)
    nombre: str
    direccion: str
    ubicacion: Optional[dict] = None  # GeoJSON Point: {"type": "Point", "coordinates": [lon, lat]}
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
