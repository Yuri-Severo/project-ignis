import os
import asyncio
from fastapi import FastAPI
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fire_data_collector import FireDataCollector

load_dotenv()

MAP_KEY = os.getenv("MAP_KEY")  # Registre-se em: https://firms.modaps.eosdis.nasa.gov/api/

# Instância do coletor
collector = FireDataCollector(MAP_KEY)

fire_data_cache = {
    "last_update": None,
    "data": []
}

async def update_fire_data():
    """Atualiza dados de queimadas em background"""
    
    
    try:
        print("Atualizando dados de queimadas...")
        new_data = await collector.fetch_multiple_sources(days=1)
        
        fire_data_cache['data'] = new_data
        fire_data_cache['last_update'] = datetime.now().isoformat()
        
        print(f"Dados atualizados: {len(new_data)} focos de queimada encontrados")
        
    except Exception as e:
        print(f"Erro na atualização dos dados: {e}")

# Tarefa periódica para atualização
async def periodic_update():
    """Task que roda a cada 5 minutos para atualizar dados"""
    while True:
        await update_fire_data()
        # Aguarda 5 minutos (300 segundos)
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia a aplicação e primeira coleta de dados"""
    
    # Primeira atualização
    await update_fire_data()
    
    # Inicia task periódica
    asyncio.create_task(periodic_update())

    yield
    print("Encerrando server...")
