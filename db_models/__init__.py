"""
Paquete de modelos de datos de InmoCore.
Cada módulo define un modelo Pydantic que representa una colección
de MongoDB. Se re-exportan acá para poder importarlos de forma
directa: `from db_models import Propiedad, Cliente, ...`
"""

from db_models.agencia import Agencia
from db_models.propiedad import Propiedad
from db_models.cliente import Cliente
from db_models.contrato import Contrato
from db_models.alerta import Alerta

__all__ = [
    "Agencia",
    "Propiedad",
    "Cliente",
    "Contrato",
    "Alerta",
]
