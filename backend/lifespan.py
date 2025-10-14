# backend/lifespan.py
import asyncio
import httpx
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Dict
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração NASA FIRMS
NASA_FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
MAP_KEY = os.getenv("NASA_API_KEY", "SEU_MAP_KEY_AQUI")

# Coordenadas da Amazônia
AMAZON_BOUNDS = {
    "west": -75,
    "south": -15,
    "east": -45,
    "north": 5
}

# Cache para armazenar dados em memória
fire_data_cache = {
    "last_update": None,
    "data": []
}


def safe_int(value, default=0):
    """Converte valor para int de forma segura"""
    try:
        if value is None or value == '':
            return default
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            return int(float(value.strip()))
        return default
    except (ValueError, TypeError, AttributeError):
        return default


def safe_float(value, default=0.0):
    """Converte valor para float de forma segura"""
    try:
        if value is None or value == '':
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value.strip())
        return default
    except (ValueError, TypeError, AttributeError):
        return default


class FireDataCollector:
    def __init__(self, map_key: str):
        self.map_key = map_key
        self.base_url = NASA_FIRMS_BASE_URL
    
    async def fetch_amazon_fires(self, source: str = "MODIS_NRT", days: int = 5) -> List[Dict]:
        """Busca dados de queimadas na região amazônica COM CONVERSÃO DE TIPOS"""
        coords = f"{AMAZON_BOUNDS['west']},{AMAZON_BOUNDS['south']},{AMAZON_BOUNDS['east']},{AMAZON_BOUNDS['north']}"
        url = f"{self.base_url}/{self.map_key}/{source}/{coords}/{days}"
        
        logger.info(f"Buscando dados de {source} - últimos {days} dias")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse CSV data
                lines = response.text.strip().split('\n')
                if len(lines) <= 1:
                    logger.warning(f"{source}: Nenhum dado encontrado")
                    return []
                
                headers = lines[0].split(',')
                fires = []
                
                for line in lines[1:]:
                    if not line.strip():
                        continue
                        
                    values = line.split(',')
                    if len(values) < len(headers):
                        continue
                    
                    try:
                        fire_data = {}
                        
                        # Processar cada campo com conversão adequada
                        for i, header in enumerate(headers):
                            value = values[i] if i < len(values) else ""
                            
                            # Conversão baseada no tipo esperado do campo
                            if header == 'latitude':
                                fire_data[header] = safe_float(value)
                            elif header == 'longitude':
                                fire_data[header] = safe_float(value)
                            elif header == 'brightness':
                                fire_data[header] = safe_float(value)
                            elif header == 'scan':
                                fire_data[header] = safe_float(value)
                            elif header == 'track':
                                fire_data[header] = safe_float(value)
                            elif header == 'bright_t31':
                                fire_data[header] = safe_float(value)
                            elif header == 'frp':
                                fire_data[header] = safe_float(value)
                            elif header == 'confidence':
                                # CONVERSÃO EXPLÍCITA PARA INT
                                fire_data[header] = safe_int(value)
                            elif header == 'version':
                                fire_data[header] = str(value).strip()
                            else:
                                # Outros campos como string
                                fire_data[header] = str(value).strip()
                        
                        # Validar dados essenciais
                        if fire_data.get('latitude') and fire_data.get('longitude'):
                            fires.append(fire_data)
                        
                    except Exception as e:
                        logger.warning(f"Erro ao processar linha: {e}")
                        continue
                
                logger.info(f"{source}: {len(fires)} focos encontrados")
                return fires
                
        except httpx.TimeoutException:
            logger.error(f"{source}: Timeout na requisição")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"{source}: Erro HTTP {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"{source}: Erro inesperado - {e}")
            return []
    
    async def fetch_multiple_sources(self, days: int = 5) -> List[Dict]:
        """Busca dados de múltiplas fontes de satélite"""
        sources = ["MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
        all_fires = []
        
        for source in sources:
            try:
                fires = await self.fetch_amazon_fires(source, days)
                # Adiciona fonte aos dados
                for fire in fires:
                    fire['source'] = source
                all_fires.extend(fires)
            except Exception as e:
                logger.error(f"Erro ao buscar dados de {source}: {e}")
                continue
        
        logger.info(f"Total de focos coletados: {len(all_fires)}")
        return all_fires


# Instância do coletor
collector = FireDataCollector(MAP_KEY)


async def update_fire_data():
    """Atualiza dados de queimadas em background"""
    global fire_data_cache
    
    try:
        logger.info("Atualizando dados de queimadas...")
        
        if MAP_KEY == "SEU_MAP_KEY_AQUI":
            logger.error("ERRO: Configure sua chave da NASA FIRMS no arquivo .env")
            return
        
        new_data = await collector.fetch_multiple_sources(days=5)
        
        fire_data_cache['data'] = new_data
        fire_data_cache['last_update'] = datetime.now().isoformat()
        
        logger.info(f"Dados atualizados: {len(new_data)} focos de queimada")
        
        # Log de estatísticas por fonte
        sources = {}
        for fire in new_data:
            source = fire.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            logger.info(f"  {source}: {count} focos")
        
    except Exception as e:
        logger.error(f"Erro na atualização dos dados: {e}")


async def periodic_update():
    """Task que roda periodicamente para atualizar dados"""
    while True:
        await update_fire_data()
        # Aguarda 10 minutos (600 segundos)
        await asyncio.sleep(600)


@asynccontextmanager
async def lifespan(app):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("🚀 Iniciando aplicação...")
    
    if MAP_KEY == "SEU_MAP_KEY_AQUI":
        logger.warning("⚠️  ATENÇÃO: Configure sua chave da NASA FIRMS!")
        logger.warning("📝 Crie um arquivo .env com: NASA_API_KEY=sua_chave_aqui")
        logger.warning("🔗 Obtenha em: https://firms.modaps.eosdis.nasa.gov/api/map_key/")
    else:
        # Primeira atualização
        await update_fire_data()
        
        # Inicia task periódica
        task = asyncio.create_task(periodic_update())
        logger.info("✅ Sistema iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("🛑 Encerrando aplicação...")
    if MAP_KEY != "SEU_MAP_KEY_AQUI":
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("👋 Aplicação encerrada")