from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests
import time
from tsp_comparativo import procesar_rutas_con_kmeans

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestDirecciones(BaseModel):
    origen: str
    destinos: List[str]
    num_carteros: int = 2
    precio_gasolina: float = 16000
    rendimiento_km_litro: float = 40
    salario_hora: float = 7000
    tiempo_servicio_minutos: float = 5


def geocodificar(direccion: str):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "tesis_logistica_pereira"}
    params = {
        "q": f"{direccion}, Pereira, Risaralda, Colombia",
        "format": "json",
        "limit": 1
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "nombre": data[0]["display_name"].split(",")[0]
            }
    except Exception:
        return None

    return None


def obtener_matriz_osrm(puntos):
    coords = ";".join([f"{p['lon']},{p['lat']}" for p in puntos])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords}"

    try:
        res = requests.get(
            url,
            params={"annotations": "distance,duration"},
            timeout=20
        ).json()

        if res.get("code") == "Ok":
            distancias_km = [
                [round((d or 0) / 1000, 2) for d in fila]
                for fila in res["distances"]
            ]
            duraciones_min = [
                [round((d or 0) / 60, 2) for d in fila]
                for fila in res["durations"]
            ]

            return {
                "distancias_km": distancias_km,
                "duraciones_min": duraciones_min
            }

        return None
    except Exception:
        return None


def obtener_geometria_ruta_osrm(ruta):
    coords = ";".join([f"{p['lon']},{p['lat']}" for p in ruta])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}"

    try:
        res = requests.get(
            url,
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "false"
            },
            timeout=20
        ).json()

        if res.get("code") == "Ok" and res.get("routes"):
            geometry = res["routes"][0]["geometry"]["coordinates"]
            # OSRM devuelve [lon, lat], Leaflet necesita [lat, lon]
            return [[coord[1], coord[0]] for coord in geometry]

        return []
    except Exception:
        return []


@app.post("/ruta-direcciones")
async def ruta_direcciones(data: RequestDirecciones):
    origen_geo = geocodificar(data.origen)
    if not origen_geo:
        return {"error": "Origen no encontrado"}

    destinos_geo = []
    for d in data.destinos:
        geo = geocodificar(d)
        if geo:
            destinos_geo.append(geo)
            time.sleep(1.1)

    if len(destinos_geo) == 0:
        return {"error": "No se encontró ningún destino válido"}

    num_carteros = max(1, min(data.num_carteros, len(destinos_geo)))

    resultado = procesar_rutas_con_kmeans(
        origen=origen_geo,
        destinos=destinos_geo,
        num_clusters=num_carteros,
        funcion_matriz=obtener_matriz_osrm,
        funcion_geometria=obtener_geometria_ruta_osrm,
        precio_gasolina=data.precio_gasolina,
        rendimiento_km_litro=data.rendimiento_km_litro,
        salario_hora=data.salario_hora,
        tiempo_servicio_minutos=data.tiempo_servicio_minutos
    )

    return resultado