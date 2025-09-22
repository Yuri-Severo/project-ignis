from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx

# Configuração NASA FIRMS
NASA_FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Coordenadas da Amazônia (aproximadamente)
AMAZON_BOUNDS = {
    "west": -85,
    "south": -20,
    "east": -32,
    "north": 14
}

class FireData(BaseModel):
    latitude: float
    longitude: float
    brightness: float
    scan: float
    track: float
    acq_date: str
    acq_time: str
    satellite: str
    confidence: int
    version: str
    bright_t31: float
    frp: float
    daynight: str

class FireDataCollector:
    def __init__(self, map_key: str):
        self.map_key = map_key
        self.base_url = NASA_FIRMS_BASE_URL
    
    async def fetch_amazon_fires(self, source: str = "MODIS_NRT", days: int = 1) -> List[Dict]:
        """Busca dados de queimadas na região amazônica"""
        # Formato da URL: /csv/MAP_KEY/SOURCE/west,south,east,north/days
        coords = f"{AMAZON_BOUNDS['west']},{AMAZON_BOUNDS['south']},{AMAZON_BOUNDS['east']},{AMAZON_BOUNDS['north']}"
        url = f"{self.base_url}/{self.map_key}/{source}/{coords}/{days}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse CSV data
                lines = response.text.strip().split('\n')
                if len(lines) <= 1:
                    return []
                
                headers = lines[0].split(',')
                fires = []
                
                for line in lines[1:]:
                    values = line.split(',')
                    if len(values) >= len(headers):
                        fire_data = {}
                        for i, header in enumerate(headers):
                            try:
                                # Conversão de tipos baseada no header
                                if header in ['latitude', 'longitude', 'brightness', 'scan', 'track', 'bright_t31', 'frp']:
                                    fire_data[header] = float(values[i])
                                elif header in ['confidence']:
                                    fire_data[header] = int(values[i])
                                else:
                                    fire_data[header] = values[i]
                            except (ValueError, IndexError):
                                fire_data[header] = values[i] if i < len(values) else ""
                        
                        fires.append(fire_data)
                
                return fires
                
        except Exception as e:
            print(f"Erro ao buscar dados do NASA FIRMS: {e}")
            return []
    
    async def fetch_multiple_sources(self, days: int = 1) -> List[Dict]:
        """Busca dados de múltiplas fontes de satélite"""
        sources = ["MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"]
        all_fires = []
        
        for source in sources:
            try:
                fires = await self.fetch_amazon_fires(source, days)
                # Adiciona fonte aos dados
                for fire in fires:
                    fire['source'] = source
                all_fires.extend(fires)
            except Exception as e:
                print(f"Erro ao buscar dados de {source}: {e}")
                continue
        
        return all_fires