from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import obtener_bd
from models.orden import Orden as OrdenModel
from models.mecanico import Mecanico as MecanicoModel
from models.repuesto import Repuesto as RepuestoModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from models.factura import Factura as FacturaModel
from typing import Optional, List
from schemas.ordenes import OrdenCreate, OrdenPatch, OrdenResponse, AgregarRepuestoOrden, RepuestoEnOrdenResponse
from dependencias import verificar_api_key, parametros_paginacion
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/ordenes", tags=["Gestionar ordenes"])

@router.get("/", response_model=List[OrdenResponse])
async def obtener_ordenes(
    estado: Optional[str] = None,
    paginacion: dict = Depends(parametros_paginacion), 
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).options(joinedload(OrdenModel.mecanico))
    resultado = await db.execute(sentencia)
    ordenes = resultado.scalars().all() # Traer los objetos (No "lenguaje" sql)

    return ordenes

@router.get("/{orden_id}", response_model=OrdenResponse)
async def obtener_orden_por_id(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    # SELECT * FROM ordenes WHERE id = orden_id
    sentencia = select(OrdenModel).options(joinedload(OrdenModel.mecanico)).where(OrdenModel.id == orden_id)
    resultado = await db.execute(sentencia)

    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return orden

@router.post("/", status_code=201)
async def crear_orden(
    orden: OrdenCreate,
    api_key: str = Depends(verificar_api_key), 
    db: AsyncSession = Depends(obtener_bd)
):

    consulta_mec = select(MecanicoModel).where(MecanicoModel.id == orden.mecanico_id)
    res_mec = await db.execute(consulta_mec)
    mecanico_db = res_mec.scalar_one_or_none()

    if not mecanico_db or not mecanico_db.activo:
        raise HTTPException(
            status_code=400,
            detail=f"El mecanico con el ID {orden.mecanico_id} no existe o está inactivo."
        )
    
    nueva_orden = OrdenModel(**orden.model_dump())

    db.add(nueva_orden)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al guardar la base de datos")

    await db.refresh(nueva_orden)

    return {"mensaje": "Orden creada", "orden": nueva_orden}

@router.delete("/{placa}", status_code=204)
async def eliminar_orden(
    placa: str,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).where(OrdenModel.placa == placa)
    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    await db.delete(orden)
    await db.commit()
    return None

@router.patch("/{orden_id}")
async def actualizacion_parcial(
    orden_id: int,
    orden_patch: OrdenPatch,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).where(OrdenModel.id == orden_id)
    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    datos = orden_patch.model_dump(exclude_unset=True)
    nuevo_estado = datos.pop("nuevo_estado", None)
    mano_obra = datos.pop("mano_obra", None)

    for campo, valor in datos.items():
        setattr(orden, campo, valor)

    if nuevo_estado == "Reparada":
        consulta_factura = select(FacturaModel).where(FacturaModel.orden_id == orden.id)
        resultado_factura = await db.execute(consulta_factura)
        factura_existente = resultado_factura.scalar_one_or_none()

        if factura_existente:
            return {"mensaje": "La orden ya tiene una factura generada", "factura_id": factura_existente.id}

        if orden.estado != "Reparada" and mano_obra is not None:
            orden.costo_reparacion += mano_obra

        consulta_repuestos = select(OrdenRepuestoModel).where(OrdenRepuestoModel.orden_id == orden.id)
        resultado_repuestos = await db.execute(consulta_repuestos)
        repuestos = resultado_repuestos.scalars().all()

        subtotal_repuestos = sum(repuesto.cantidad * repuesto.precio_unitario_historico for repuesto in repuestos)

        if orden.costo_reparacion <= 0:
            raise HTTPException(status_code=400, detail="No se puede facturar una orden con costo de reparación igual a cero")

        if orden.costo_reparacion < subtotal_repuestos:
            raise HTTPException(status_code=400, detail="El costo de reparación no puede ser inferior al subtotal de repuestos")

        costo_mano_obra = orden.costo_reparacion - subtotal_repuestos
        total_neto = subtotal_repuestos + costo_mano_obra

        iva = round(total_neto * 0.19, 2)
        total_pagar = round(total_neto + iva, 2)
        orden.estado = "Reparada"
        nueva_factura = FacturaModel(
            orden_id=orden.id,
            subtotal_repuestos=subtotal_repuestos,
            costo_mano_obra=costo_mano_obra,
            iva=iva,
            total_pagar=total_pagar
        )

        db.add(nueva_factura)

    elif nuevo_estado is not None:
        orden.estado = nuevo_estado

    try:
        await db.commit()
        await db.refresh(orden)
    except Exception:
        await db.rollback()
        raise HTTPException( status_code=500, detail="Error aplicando la actualización de la orden")

    return {"mensaje": "La orden ha sido actualizada con éxito", "orden": orden}

@router.post("/{orden_id}/repuestos", status_code=201, response_model=RepuestoEnOrdenResponse)
async def agregar_repuesto_a_orden(
    orden_id: int,
    datos: AgregarRepuestoOrden,
    db: AsyncSession = Depends(obtener_bd)
):
    # 1. Validar que la orden exista
    res_orden = await db.execute(select(OrdenModel).where(OrdenModel.id == orden_id))
    orden_db = res_orden.scalar_one_or_none()
    if not orden_db:
        raise HTTPException(status_code=404, detail="La orden de servicio no existe")

    # 2. Validar que la orden no esté cerrada o facturada
    if orden_db.estado == "Reparada":
        raise HTTPException(status_code=400, detail="No se pueden modificar repuestos de una orden ya cerrada/facturada")

    consulta_factura = select(FacturaModel).where( FacturaModel.orden_id == orden_id)
    resultado_factura = await db.execute(consulta_factura)

    if resultado_factura.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="No se pueden modificar repuestos de una orden ya cerrada/facturada")

    # 3. Validar que el repuesto exista
    res_rep = await db.execute(select(RepuestoModel).where(RepuestoModel.id == datos.repuesto_id))
    rep_db = res_rep.scalar_one_or_none()
    if not rep_db:
        raise HTTPException(status_code=404, detail="El repuesto no existe")

    # 4. Validar stock
    if rep_db.stock_actual < datos.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. En almacen tengo: {rep_db.stock_actual} y se solicitaron: {datos.cantidad}"
        )

    # Operacion transaccional
    rep_db.stock_actual -= datos.cantidad
    subtotal = rep_db.precio_venta * datos.cantidad
    orden_db.costo_reparacion += subtotal

    detalle = OrdenRepuestoModel(
        orden_id=orden_db.id,
        repuesto_id=rep_db.id,
        cantidad=datos.cantidad,
        precio_unitario_historico=rep_db.precio_venta
    )

    db.add(detalle)

    try:
        await db.commit()
        await db.refresh(detalle)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error aplicando la actualización parcial.")

    return detalle