from fastapi import FastAPI, HTTPException
from database import leer_base_datos, obtener_producto

# Inicializar la aplicación
apiRest = FastAPI(
    title="API inventarios SENA",
    description="Mi primera API asíncrona",
    version="1.0.0"
)

# Nuestro primer endpoint
@apiRest.get("/")
async def ruta_principal():
    return {"mensaje": "¡Bienvenido a mi primera API Rest!"}

@apiRest.get("/estado")
async def estado_servidor():
    return {"status": "En línea", "servicios": "Operativos sin ningún inconveniente"}

@apiRest.get("/suma")
async def sumar():
    numero1 = 5
    numero2 = 4
    resultado = numero1 + numero2
    return  resultado

@apiRest.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return {"cantidad": len(datos), "productos": datos}

@apiRest.get("/productos/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        producto = await obtener_producto(codigo_producto)
        return producto
    except KeyError:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe en la BD")

@apiRest.get("/categorias")
async def listar_categorias():
    datos = await leer_base_datos()
    categorias = set()

@apiRest.get("/alertas/stock")
async def stock_critico():
    datos = await leer_base_datos()
    productos_criticos = []

@apiRest.get("/productos/buscar/{palabra_clave}")
async def buscar_por_nombre(palabra_clave: str):
    datos = await leer_base_datos()
    productos_encontrados = []
