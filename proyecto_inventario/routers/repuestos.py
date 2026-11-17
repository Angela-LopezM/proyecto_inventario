from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import obtener_bd
from models.repuesto import Repuesto
from schemas.schemas import RepuestoCreate, RepuestoResponse

router = APIRouter(prefix="/repuestos", tags=["Repuestos"])

@router.post("", response_model=RepuestoResponse, status_code=201)
async def crear_repuesto(
    repuesto: RepuestoCreate,
    db: AsyncSession = Depends(obtener_bd)
):
    nuevo_repuesto = Repuesto(**repuesto.model_dump())

    db.add(nuevo_repuesto)
    await db.commit()
    await db.refresh(nuevo_repuesto)

    return nuevo_repuesto

@router.get("", response_model=list[RepuestoResponse])
async def obtener_repuestos(
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(Repuesto)
    resultado = await db.execute(sentencia)
    repuestos = resultado.scalars().all()

    return repuestos