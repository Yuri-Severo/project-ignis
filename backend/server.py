# backend/main.py
import os
import json
import uvicorn
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, BackgroundTasks

from lifespan import lifespan, update_fire_data, fire_data_cache

app = FastAPI(title="Amazon Fire Monitoring API", lifespan=lifespan)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache para armazenar dados em memória


# Endpoints da API    
@app.get("/")
async def root():
    return {"message": "Amazon Fire Monitoring API", "docs": "/docs"}

@app.get("/api/fires")
async def get_fires(
    source: Optional[str] = None,
    min_confidence: int = 0,
    hours_ago: int = 24
):
    """Retorna dados de queimadas com filtros opcionais"""
    
    if not fire_data_cache['data']:
        raise HTTPException(status_code=503, detail="Dados ainda não disponíveis")
    
    fires = fire_data_cache['data'].copy()
    
    # Filtro por fonte
    if source:
        fires = [f for f in fires if f.get('source') == source]
    
    # Filtro por confiança
    fires = [f for f in fires if f.get('confidence', 0) >= min_confidence]
    
    # Filtro por tempo (últimas X horas)
    cutoff_time = datetime.now() - timedelta(hours=hours_ago)
    filtered_fires = []
    
    for fire in fires:
        try:
            # Parse da data e hora
            fire_datetime = datetime.strptime(
                f"{fire.get('acq_date')} {fire.get('acq_time')}", 
                "%Y-%m-%d %H%M"
            )
            if fire_datetime >= cutoff_time:
                filtered_fires.append(fire)
        except:
            # Se não conseguir fazer parse da data, inclui o ponto
            filtered_fires.append(fire)
    
    return {
        "total": len(filtered_fires),
        "last_update": fire_data_cache['last_update'],
        "fires": filtered_fires
    }

@app.get("/api/fires/stats")
async def get_fire_stats():
    """Retorna estatísticas dos focos de queimada"""
    
    if not fire_data_cache['data']:
        raise HTTPException(status_code=503, detail="Dados ainda não disponíveis")
    
    fires = fire_data_cache['data']
    
    # Estatísticas básicas
    total_fires = len(fires)
    
    # Confiança média
    confidences = [f.get('confidence', 0) for f in fires if f.get('confidence')]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    # FRP (Fire Radiative Power) média
    frp_values = [f.get('frp', 0) for f in fires if f.get('frp')]
    avg_frp = sum(frp_values) / len(frp_values) if frp_values else 0
    
    # Contagem por fonte
    source_count = {}
    for fire in fires:
        source = fire.get('source', 'unknown')
        source_count[source] = source_count.get(source, 0) + 1
    
    # Contagem por período do dia
    day_night_count = {}
    for fire in fires:
        period = fire.get('daynight', 'unknown')
        day_night_count[period] = day_night_count.get(period, 0) + 1
    
    return {
        "total_fires": total_fires,
        "avg_confidence": round(avg_confidence, 2),
        "avg_fire_power": round(avg_frp, 2),
        "by_source": source_count,
        "by_period": day_night_count,
        "last_update": fire_data_cache['last_update']
    }

@app.get("/api/fires/geojson")
async def get_fires_geojson(
    source: Optional[str] = None,
    min_confidence: int = 0
):
    """Retorna dados de queimadas no formato GeoJSON para mapas"""
    
    if not fire_data_cache['data']:
        raise HTTPException(status_code=503, detail="Dados ainda não disponíveis")
    
    fires = fire_data_cache['data'].copy()
    
    # Aplicar filtros
    if source:
        fires = [f for f in fires if f.get('source') == source]
    
    fires = [f for f in fires if f.get('confidence', 0) >= min_confidence]

    # Converter para GeoJSON
    features = []
    for fire in fires:
        if fire.get('latitude') and fire.get('longitude'):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [fire['longitude'], fire['latitude']]
                },
                "properties": {
                    "brightness": fire.get('brightness'),
                    "confidence": fire.get('confidence'),
                    "frp": fire.get('frp'),
                    "satellite": fire.get('satellite'),
                    "source": fire.get('source'),
                    "acq_date": fire.get('acq_date'),
                    "acq_time": fire.get('acq_time'),
                    "daynight": fire.get('daynight')
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total": len(features),
            "last_update": fire_data_cache['last_update']
        }
    }
    
    return geojson

@app.post("/api/fires/refresh")
async def refresh_fire_data(background_tasks: BackgroundTasks):
    """Força atualização dos dados"""
    background_tasks.add_task(update_fire_data)
    return {"message": "Atualização iniciada em background"}

if __name__ == "__main__":
    print("Iniciando servidor de monitoramento de queimadas na Amazônia...")
    print("Documentação disponível em: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)