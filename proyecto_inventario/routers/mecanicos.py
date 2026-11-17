from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import obtener_bd
from models.mecanico import Mecanico
from schemas.schemas import MecanicoCreate, MecanicoResponse

router = APIRouter(prefix="/mecanicos", tags=["Mecanicos"])

@router.post("", response_model=MecanicoResponse, status_code=201)
async def crear_mecanico(
    mecanico: MecanicoCreate,
    db: AsyncSession = Depends(obtener_bd)
):
    nuevo_mecanico = Mecanico(**mecanico.model_dump())

    db.add(nuevo_mecanico)
    await db.commit()
    await db.refresh(nuevo_mecanico)

    return nuevo_mecanico

@router.get("", response_model=list[MecanicoResponse])
async def obtener_mecanicos(
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(Mecanico)
    resultado = await db.execute(sentencia)
    mecanicos = resultado.scalars().all()

    return mecanicos