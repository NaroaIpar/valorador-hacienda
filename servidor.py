"""
Servidor local para que la interfaz HTML pueda usar la automatización de Playwright.
Ejecutar con:  python servidor.py
Se queda escuchando en  http://localhost:8000
"""
import asyncio
import functools
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from obtener_modelo import extraer_datos_allianz
from obtener_valoracion import obtener_valoracion_gipuzkoa

app = FastAPI(title="Ipar Artekaritza API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DatosVehiculo(BaseModel):
    id: str
    fecha_mat: str
    tipo_vehiculo: str = "Turismos y Todo Terrenos"
    marca: str
    version_completa: str
    modelo_buscar: str
    cc: int
    kw: int
    combustible: str


class SolicitudValoracion(BaseModel):
    datos: DatosVehiculo
    modelo: str


@app.get("/api/allianz/{matricula}")
async def get_allianz(matricula: str):
    result = await asyncio.to_thread(extraer_datos_allianz, matricula)
    return result or {}


@app.post("/api/opciones")
async def get_opciones(datos: DatosVehiculo):
    fn = functools.partial(obtener_valoracion_gipuzkoa, datos.dict())
    opts = await asyncio.to_thread(fn)
    return {"opciones": opts or []}


@app.post("/api/valoracion")
async def get_valoracion(req: SolicitudValoracion):
    fn = functools.partial(
        obtener_valoracion_gipuzkoa,
        req.datos.dict(),
        req.modelo,
    )
    precio = await asyncio.to_thread(fn)
    return {"precio": precio}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
