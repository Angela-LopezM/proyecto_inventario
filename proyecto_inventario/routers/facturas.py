from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from core.database import obtener_bd
from models.factura import Factura as FacturaModel
from models.orden import Orden as OrdenModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from schemas.facturas import FacturaDetalladaResponse

router = APIRouter(prefix="/facturas", tags=["Facturación"])

@router.get("/{orden_id}", response_model=FacturaDetalladaResponse)
async def obtener_factura(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(FacturaModel).options(
        joinedload(FacturaModel.orden).joinedload(OrdenModel.mecanico),
        joinedload(FacturaModel.orden)
        .joinedload(OrdenModel.repuestos_usados)
        .joinedload(OrdenRepuestoModel.repuesto)
    ).where(FacturaModel.orden_id == orden_id)

    resultado = await db.execute(sentencia)
    factura = resultado.unique().scalar_one_or_none()

    if not factura:
        raise HTTPException(status_code=404, detail="No existe una factura para esta orden")

    orden = factura.orden
    repuestos = []

    for detalle in orden.repuestos_usados:
        repuestos.append({
            "nombre_repuesto": detalle.repuesto.nombre,
            "cantidad": detalle.cantidad,
            "precio_unitario_historico": detalle.precio_unitario_historico,
            "subtotal_linea": round(detalle.cantidad * detalle.precio_unitario_historico, 2)
        })

    return {
        "id": factura.id,
        "fecha_emision": factura.fecha_emision,
        "subtotal_repuestos": factura.subtotal_repuestos,
        "costo_mano_obra": factura.costo_mano_obra,
        "iva": factura.iva,
        "total_pagar": factura.total_pagar,
        "placa": orden.placa,
        "modelo": orden.modelo,
        "mecanico": orden.mecanico.nombre_completo if orden.mecanico else "Sin mecánico",
        "repuestos": repuestos
    }