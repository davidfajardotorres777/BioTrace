from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Alerta(BaseModel):
    """
    Documento de la colección `alertas`.
    Registra un evento generado automáticamente por una regla de negocio
    del `InmoCoreDAO` — por ejemplo, una propiedad publicada en venta con
    un precio sospechosamente bajo (< 10.000 USD).

    `entidad_referencia_id` guarda el `_id` del documento que originó la
    alerta (hoy, una propiedad), y `resuelta` permite llevar el ciclo de
    vida: se crea en `False` y un agente de la agencia puede marcarla
    como resuelta desde la interfaz.
    """

    id: str = Field(alias="_id", default=None)
    agencia_id: str
    tipo_alerta: str  # Ej: "Precio Anómalo", "Contrato Vencido"
    mensaje: str
    entidad_referencia_id: str  # _id de la propiedad (u otra entidad) que originó la alerta
    resuelta: bool = False
    fecha_alerta: datetime = Field(default_factory=datetime.utcnow)
    fecha_resolucion: Optional[datetime] = None

    class Config:
        populate_by_name = True
