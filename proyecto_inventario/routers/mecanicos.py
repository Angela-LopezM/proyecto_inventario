import json
import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from schemas import MecanicoCreate
from dependencias import verificar_auditor, verificar_gerente, parametros_paginacion

router = APIRouter(prefix="/mecanicos", tags=["Gestionar mecanicos"])

ARCHIVO_MECANICOS = "mecanicos.json"

async def leer_mecanicos():
    try:
        async with aiofiles.open(ARCHIVO_MECANICOS, mode="r", encoding="utf-8") as archivo:
            contenido = await archivo.read()
            return json.loads(contenido)
    except FileNotFoundError:
        return []

async def guardar_mecanicos(datos):
    async with aiofiles.open(ARCHIVO_MECANICOS, mode="w", encoding="utf-8") as archivo:
        await archivo.write(json.dumps(datos, indent=4, ensure_ascii=False))

@router.get("")
async def obtener_mecanicos(
    paginacion: dict = Depends(parametros_paginacion),
    rol: str = Depends(verificar_auditor)
):
    datos = await leer_mecanicos()

    skip = paginacion["skip"]
    limit = paginacion["skip"]
    datos_paginados = datos[skip:skip + limit]

    return {
        "total_mecanicos": len(datos),
        "mostrando": len(datos_paginados),
        "skip": skip,
        "mecanicos": datos_paginados
    }

@ router.post("", status_code=201)
async def crear_mecanico(
    mecanico: MecanicoCreate,
    rol : str = Depends(verificar_gerente)
):
    datos = await leer_mecanicos()

    nuevo_id = 1
    for item in datos:
        if item["id"] >= nuevo_id:
            nuevo_id = item["id"] + 1

    nuevo_mecanico = mecanico.model_dump()
    nuevo_mecanico["id"] = nuevo_id

    datos.append(nuevo_mecanico)
    await guardar_mecanicos(datos)

    return {
        "mensaje": "Mecanico creado exitosamente",
        "mecanico": nuevo_mecanico
    }

@router.delete("/{id}")
async def eliminar_mecanico(
    id: int,
    rol: str = Depends(verificar_gerente)
):
    datos = await leer_mecanicos()
    nuevos_datos = [mecanico for mecanico in datos if mecanico["id"] != id]

    if len(datos) == len(nuevos_datos):
        raise HTTPException(status_code=404, detail="Mecanico no encontrado")

    await guardar_mecanicos(nuevos_datos)

    return {"mensaje": "Mecanico eliminado exitosamente", "id": id}