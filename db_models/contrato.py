from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Contrato(BaseModel):
    """
    Documento de la colección `contratos`.
    Formaliza la operación (venta o alquiler) entre un `Cliente` y una
    `Propiedad`, siempre dentro del alcance de una `agencia_id`.

    `InmoCoreDAO.insertar_contrato` convierte `propiedad_id` y
    `cliente_id` a `ObjectId` antes de guardar, para poder resolver
    referencias entre colecciones con `$lookup` si se necesitan reportes
    combinados a futuro. `archivo_path` es opcional y apunta al PDF del
    contrato firmado guardado en MinIO.
    """

    id: str = Field(alias="_id", default=None)
    agencia_id: str
    propiedad_id: str
    cliente_id: str
    tipo_contrato: str  # Venta, Alquiler
    monto_total: float
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    archivo_path: Optional[str] = None  # Path al PDF del contrato en MinIO

    class Config:
        populate_by_name = True
