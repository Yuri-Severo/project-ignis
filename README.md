# 🔥 Ignis - App de Monitoramento de Queimadas na Amazônia

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![NASA FIRMS](https://img.shields.io/badge/NASA-FIRMS%20API-red.svg)

**Sistema de monitoramento em tempo real de focos de queimada na região amazônica utilizando dados de satélite da NASA**

</div>

---

## 📋 Sobre o Projeto

O **Ignis** é uma aplicação web que permite o monitoramento em tempo real de queimadas na região amazônica, utilizando dados fornecidos pela **NASA FIRMS API** (Fire Information for Resource Management System). O sistema coleta dados de múltiplos satélites (MODIS e VIIRS) e disponibiliza através de uma API REST e interface de visualização em mapa interativo.

### ✨ Funcionalidades

- 🛰️ **Coleta automática de dados** de múltiplas fontes de satélite
- 🗺️ **Visualização em mapa interativo** com Leaflet.js
- 📊 **Dashboard com estatísticas** em tempo real
- 🔍 **Filtros avançados** por fonte, confiança, período e região
- 📡 **API REST completa** para integração com outras aplicações
- 🔄 **Atualização automática** a cada 10 minutos
- 📈 **Análise temporal** de dados históricos
- 🌍 **Formato GeoJSON** para fácil integração com mapas

---

## 🚀 Tecnologias Utilizadas

### Backend
- **Python 3.11+**
- **FastAPI** - Framework web moderno e rápido
- **httpx** - Cliente HTTP assíncrono
- **Uvicorn** - Servidor ASGI
- **python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend
- **HTML5 / CSS3 / JavaScript**
- **Leaflet.js** - Biblioteca de mapas interativos
- **Tailwind CSS** - Framework CSS utilitário

### Fontes de Dados
- **NASA FIRMS** - Fire Information for Resource Management System
  - MODIS (Terra e Aqua)
  - VIIRS (Suomi-NPP, NOAA-20, NOAA-21)

---

## 📦 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- Chave da API NASA FIRMS ([obter aqui](https://firms.modaps.eosdis.nasa.gov/api/map_key/))

### Passo 1: Clone o repositório

```bash
git clone https://github.com/seu-usuario/project-ignis.git
cd project-ignis
```

### Passo 2: Crie um ambiente virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Passo 3: Instale as dependências

```bash
cd backend
pip install -r requirements.txt
```

### Passo 4: Configure as variáveis de ambiente

Crie um arquivo `.env` na pasta `backend/`:

```env
NASA_API_KEY=sua_chave_da_nasa_aqui
```

**Como obter sua chave da NASA FIRMS:**
1. Acesse: https://firms.modaps.eosdis.nasa.gov/api/map_key/
2. Preencha o formulário com suas informações
3. Verifique seu email e copie a chave recebida

### Passo 5: Execute a aplicação

```bash
# Na pasta backend/
python main.py
```

A API estará disponível em: `http://localhost:8000`

### Passo 6: Abra o frontend

Abra o arquivo `frontend/index.html` em seu navegador ou use um servidor web local:

```bash
# Usando Python
cd frontend
python -m http.server 8080

# Acesse: http://localhost:8080
```

---

## 📚 Documentação da API

### Base URL
```
http://localhost:8000
```

### Documentação Interativa
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principais

#### 🔥 **GET /api/fires**
Retorna lista de focos de queimada com filtros opcionais.

**Parâmetros:**
- `source` (opcional): Fonte do satélite (`MODIS_NRT`, `VIIRS_SNPP_NRT`, etc.)
- `min_confidence` (opcional, padrão: 0): Confiança mínima (0-100)
- `hours_ago` (opcional, padrão: 24): Período em horas

**Exemplo:**
```bash
GET /api/fires?min_confidence=80&hours_ago=48
```

**Resposta:**
```json
{
  "total": 1523,
  "last_update": "2025-10-06T14:30:00",
  "fires": [
    {
      "latitude": -3.456,
      "longitude": -60.123,
      "brightness": 320.5,
      "confidence": 85,
      "frp": 12.3,
      "satellite": "Terra",
      "source": "MODIS_NRT",
      "acq_date": "2025-10-06",
      "acq_time": "1430",
      "daynight": "D"
    }
  ]
}
```

#### 📊 **GET /api/fires/stats**
Retorna estatísticas agregadas dos focos de queimada.

**Resposta:**
```json
{
  "total_fires": 1523,
  "avg_confidence": 75.8,
  "avg_fire_power": 15.2,
  "by_source": {
    "MODIS_NRT": 856,
    "VIIRS_SNPP_NRT": 667
  },
  "by_period": {
    "D": 1200,
    "N": 323
  },
  "last_update": "2025-10-06T14:30:00"
}
```

#### 🗺️ **GET /api/fires/geojson**
Retorna dados no formato GeoJSON para visualização em mapas.

**Parâmetros:**
- `source` (opcional): Filtro por fonte
- `min_confidence` (opcional, padrão: 0): Confiança mínima
- `hours_ago` (opcional): Período em horas

**Resposta:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-60.123, -3.456]
      },
      "properties": {
        "brightness": 320.5,
        "confidence": 85,
        "frp": 12.3,
        "satellite": "Terra",
        "source": "MODIS_NRT"
      }
    }
  ],
  "metadata": {
    "total": 1523,
    "last_update": "2025-10-06T14:30:00"
  }
}
```

#### 🔄 **POST /api/fires/refresh**
Força atualização manual dos dados.

**Resposta:**
```json
{
  "message": "Atualização iniciada em background"
}
```

---

## 🛰️ Fontes de Dados Disponíveis

| Código | Satélite | Descrição | Atualização |
|--------|----------|-----------|-------------|
| `MODIS_NRT` | Terra/Aqua | Near Real-Time | < 3 horas |
| `VIIRS_SNPP_NRT` | Suomi-NPP | Near Real-Time | < 3 horas |
| `VIIRS_NOAA20_NRT` | NOAA-20 | Near Real-Time | < 3 horas |
| `VIIRS_NOAA21_NRT` | NOAA-21 | Near Real-Time | < 3 horas |
| `MODIS_SP` | Terra/Aqua | Standard Processing | 2-3 meses |
| `VIIRS_SNPP_SP` | Suomi-NPP | Standard Processing | 2-3 meses |
| `VIIRS_NOAA20_SP` | NOAA-20 | Standard Processing | 2-3 meses |

**Legenda:**
- **NRT** (Near Real-Time): Dados recentes, disponíveis em até 3 horas
- **SP** (Standard Processing): Dados históricos validados

---

## 🗂️ Estrutura do Projeto

```
project-ignis/
├── backend/
│   ├── main.py              # API FastAPI principal
│   ├── lifespan.py          # Gerenciamento de ciclo de vida e coleta de dados
│   ├── requirements.txt     # Dependências Python
│   ├── .env                 # Variáveis de ambiente (não versionado)
│   └── .env.example         # Exemplo de configuração
├── frontend/
│   ├── index.html           # Interface web com mapa
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 Configuração Avançada

### Personalizar Área Geográfica

Edite `backend/lifespan.py`:

```python
AMAZON_BOUNDS = {
    "west": -75,    # Longitude oeste
    "south": -15,   # Latitude sul
    "east": -45,    # Longitude leste
    "north": 5      # Latitude norte
}
```

### Ajustar Frequência de Atualização

Edite `backend/lifespan.py`:

```python
async def periodic_update():
    while True:
        await update_fire_data()
        await asyncio.sleep(600)  # 600 segundos = 10 minutos
```

### Configurar Período de Coleta

Edite `backend/lifespan.py`:

```python
new_data = await collector.fetch_multiple_sources(days=5)  # Últimos 5 dias
```

---

## 📝 Roadmap

- [ ] Sistema de alertas por email/SMS
- [ ] Análise preditiva com Machine Learning
- [ ] Integração com dados meteorológicos
- [ ] App mobile (React Native/Flutter)
- [ ] Dashboard administrativo
- [ ] API de notificações em tempo real (WebSocket)
- [ ] Exportação de relatórios PDF
- [ ] Suporte multi-idiomas
- [ ] Banco de dados PostgreSQL + PostGIS
- [ ] Autenticação e controle de acesso

---

<div align="center">

**Desenvolvido com ❤️ para preservação da Amazônia**

🌳 Ajude a proteger nossa floresta 🌳

</div>
