import asyncio 

# Importar funciones de otro archivo
from database import crear_producto, obtener_producto, actualizar_stock, eliminar_producto, vender_producto

async def prueba_de_estres():
    print("--- Iniciando prueba ---")
    tareas_creacion = [
        crear_producto("M001", "Llanta trasera", 10),
        crear_producto("M002", "Filtro de aire", 25),
        crear_producto("M003", "Bujía", 50),
    ]

    try:
        await asyncio.gather(*tareas_creacion)
        print("Productos creados exitosamente")
    except Exception as e:
        print(f"Error de creación: {e}")

    print("\nActualizar y consultar...")
    try:
        resultado = await asyncio.gather(
            actualizar_stock(8, "M001"),
            obtener_producto("M002")
        )
        print("Operaciones mixtas completadas.")
        print(f" - Update devolvió: {resultado[0]}")
        print(f" - Get devolvió: {resultado[1]}")
    except Exception as e:
        print("Error en operaciones mixtas.")

async def procesar_venta(codigo, cantidad_vendida):
    try:
        resultado = await vender_producto(codigo, cantidad_vendida)
        print(f"VENTA: {resultado}")
    except KeyError as e:
        print(f"ERROR: {e}")
    except ValueError as e:
        print(f"ERROR: {e}")

async def prueba_ventas():
    print("\n--- PRUEBA DE ESTRÉS: VENTAS ---")
    ventas = [
        procesar_venta("M001", 2),
        procesar_venta("M002", 24),
        procesar_venta("M003", 60),
        procesar_venta("M003", 10)
    ]

    await asyncio.gather(*ventas)
    await asyncio.sleep(2)
    print("--- FIN DE LAS VENTAS ---")

async def main():
    await prueba_de_estres()
    await prueba_ventas()

asyncio.run(main())