from pydantic import BaseModel, Field
from datetime import datetime


class Cliente(BaseModel):
    """
    Documento de la colección `clientes`.
    Representa a una persona (comprador, inquilino o vendedor) que
    interactúa comercialmente con una agencia.

    Pertenece siempre a una `agencia_id`. El índice compuesto
    `(agencia_id, dni)` definido en `setup_db.py` es único: garantiza
    que dentro de una misma agencia no se pueda duplicar un cliente,
    pero permite que la misma persona (mismo DNI) exista como cliente
    en agencias distintas, respetando el aislamiento multi-tenant.
    """

    id: str = Field(alias="_id", default=None)
    agencia_id: str
    dni: str
    nombre: str
    apellido: str
    telefono: str
    email: str
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
