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

# Coordenadas da Amazônia Legal Brasileira (bounding box para API NASA FIRMS)
# A bounding box retangular é usada para requisitar dados da API
# Porém, como é retangular, inclui partes de Bolívia, Peru e Colômbia
# Por isso, aplicamos filtragem adicional por polígono após receber os dados
# Abrange: AC, AM, AP, PA, RO, RR, TO, MT e MA (oeste)
AMAZON_BOUNDS = {
    "west": -73.99,   # Fronteira oeste (Acre)
    "south": -18.04,  # Sul do Mato Grosso
    "east": -44.00,   # Leste do Maranhão
    "north": 5.27     # Norte de Roraima
}

# Polígono aproximado da Amazônia Legal para filtragem precisa
# Exclui áreas de Bolívia, Peru e Colômbia com margem de segurança
# Coordenadas no sentido anti-horário (longitude, latitude)
AMAZON_LEGAL_POLYGON = [
    (-73.75, -7.35),   # Fronteira Brasil-Peru (Acre sul) - margem interna
    (-73.50, -5.00),   # Acre-Peru com margem
    (-73.00, -2.50),   # Amazonas oeste (margem da fronteira Peru)
    (-72.50, -0.50),   # Amazonas noroeste
    (-70.50, 0.00),    # Fronteira Brasil-Colômbia com margem
    (-69.50, 1.00),    # Amazonas norte com margem
    (-69.40, 2.00),    # Roraima oeste (fronteira Venezuela)
    (-64.83, 2.24),    # Roraima nordeste
    (-60.24, 5.27),    # Extremo norte (Roraima)
    (-59.80, 4.50),    # Norte de Roraima
    (-51.65, 4.45),    # Norte do Amapá
    (-50.39, 1.80),    # Amapá leste
    (-49.97, 1.70),    # Amapá costa
    (-48.48, 1.68),    # Pará norte
    (-44.21, -1.30),   # Maranhão nordeste
    (-44.00, -2.80),   # Maranhão leste
    (-44.36, -6.00),   # Maranhão sul
    (-44.70, -9.00),   # Tocantins leste
    (-46.05, -10.96),  # Tocantins sudeste
    (-46.87, -12.47),  # Tocantins sul
    (-50.09, -13.84),  # Mato Grosso leste
    (-51.09, -14.48),  # Mato Grosso centro-leste
    (-52.50, -15.40),  # Mato Grosso central
    (-56.09, -17.00),  # Mato Grosso sul
    (-57.50, -16.00),  # Mato Grosso sudoeste
    (-59.43, -15.42),  # Mato Grosso oeste
    (-60.11, -13.69),  # Fronteira Brasil-Bolívia (MT/RO)
    (-64.50, -12.56),  # Rondônia sul (fronteira Bolívia) - margem
    (-65.00, -11.01),  # Rondônia sudoeste - margem
    (-66.50, -10.85),  # Rondônia oeste - margem
    (-68.50, -11.15),  # Acre sul (fronteira Bolívia) - margem
    (-69.40, -10.95),  # Acre sudoeste - margem
    (-70.00, -9.49),   # Acre oeste - margem
    (-72.50, -9.08),   # Acre-Peru fronteira - margem
    (-73.75, -7.35),   # Retorna ao ponto inicial
]

def is_point_in_amazon_legal(longitude: float, latitude: float) -> bool:
    """
    Verifica se um ponto está dentro da Amazônia Legal usando algoritmo ray-casting.
    
    Este filtro é ESSENCIAL para excluir focos de queimadas de países vizinhos
    (Bolívia, Peru e Colômbia) que são capturados pela bounding box retangular.
    
    O algoritmo ray-casting traça um raio horizontal a partir do ponto e conta
    quantas vezes ele cruza as arestas do polígono. Se o número for ímpar, o
    ponto está dentro; se for par, está fora.
    
    Args:
        longitude: Longitude do ponto (coordenada X)
        latitude: Latitude do ponto (coordenada Y)
    
    Returns:
        True se o ponto está dentro do polígono da Amazônia Legal
        False se está fora (países vizinhos ou outras regiões do Brasil)
    
    Nota:
        O polígono é aproximado. Para maior precisão, use shapefile oficial do IBGE.
        Cidades fronteiriças (ex: Iquitos/Peru, Leticia/Colômbia) podem ter margem
        de erro de ~30-50km devido à resolução do polígono.
    """
    x, y = longitude, latitude
    n = len(AMAZON_LEGAL_POLYGON)
    inside = False
    
    p1x, p1y = AMAZON_LEGAL_POLYGON[0]
    for i in range(n + 1):
        p2x, p2y = AMAZON_LEGAL_POLYGON[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

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
                        
                        # Validar dados essenciais e filtrar por Amazônia Legal
                        if fire_data.get('latitude') and fire_data.get('longitude'):
                            lat = safe_float(fire_data.get('latitude'))
                            lon = safe_float(fire_data.get('longitude'))
                            
                            # Filtro: apenas pontos dentro do polígono da Amazônia Legal
                            # Exclui focos de Bolívia, Peru e Colômbia
                            if is_point_in_amazon_legal(lon, lat):
                                fires.append(fire_data)
                        
                    except Exception as e:
                        logger.warning(f"Erro ao processar linha: {e}")
                        continue
                
                logger.info(f"{source}: {len(fires)} focos dentro da Amazônia Legal")
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