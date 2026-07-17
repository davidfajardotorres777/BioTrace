from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Agencia(BaseModel):
    id: str = Field(alias="_id", default=None)
    nombre: str
    direccion: str
    ubicacion: Optional[dict] = None # GeoJSON Point
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
