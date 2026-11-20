from pydantic import BaseModel
from datetime import datetime
from typing import List

class RepuestoFacturaResponse(BaseModel):
    nombre_repuesto: str
    cantidad: int
    precio_unitario_historico: float
    subtotal_linea: float

class FacturaDetalladaResponse(BaseModel):
    id: int
    fecha_emision: datetime
    subtotal_repuestos: float
    costo_mano_obra: float
    iva: float
    total_pagar: float

    placa: str
    modelo: str
    mecanico: str

    repuestos: List[RepuestoFacturaResponse]