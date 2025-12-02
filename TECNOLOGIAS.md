# 📚 Tecnologias Essenciais - Projeto Ignis

## 🎯 Visão Geral

**Ignis** é uma aplicação full-stack para monitoramento em tempo real de queimadas na Amazônia usando dados da NASA.

- **Backend**: FastAPI (Python) - API REST assíncrona
- **Frontend**: Next.js 16 + React 19 - Interface web moderna
- **Dados**: NASA FIRMS API - Satélites MODIS e VIIRS

---

## 🔧 Backend - Stack Principal

### **FastAPI** (v0.104.1) + **Uvicorn** (v0.24.0)
**Por quê?** Framework assíncrono de alta performance com documentação automática (OpenAPI/Swagger). Uvicorn é o servidor ASGI que executa a aplicação.

**Impacto**: Permite requisições simultâneas à NASA API sem bloqueio, essencial para performance em tempo real.

### **HTTPX** (v0.25.2)
**Por quê?** Cliente HTTP assíncrono para integração com APIs externas.

**Impacto**: Coleta dados da NASA FIRMS API de forma não-bloqueante com retry automático.

### **Pydantic** (v2.5.0)
**Por quê?** Validação de dados com type hints Python, integrado ao FastAPI.

**Impacto**: Garante integridade dos dados de queimadas (lat/lon, temperatura, confiança) com validação automática.

---

## 🎨 Frontend - Stack Principal

### **Next.js** (v16.0.5) + **React** (v19.2.0)
**Por quê?** Framework moderno com App Router, Server Components e otimizações automáticas.

**Impacto**: 
- Roteamento simplificado baseado em arquivos
- SEO otimizado
- Bundle splitting automático
- Performance superior

### **Leaflet** (v1.9.4) + **React-Leaflet** (v5.0.0)
**Por quê?** Biblioteca open-source para mapas interativos, leve (42KB) e sem necessidade de API key.

**Impacto**: **CORE DO PROJETO** - Visualização geográfica dos focos de queimada com marcadores interativos, clusters e layers customizáveis.

### **Tailwind CSS** (v4)
**Por quê?** Framework utility-first com purge automático de CSS não utilizado.

**Impacto**: Desenvolvimento rápido com design consistente e bundle pequeno em produção.

### **TypeScript** (v5)
**Por quê?** Type safety e autocompletar em todo o código.

**Impacto**: Detecta erros em tempo de desenvolvimento, facilita refatoração e manutenção.

---

## 🌐 API Externa Crítica

### **NASA FIRMS API**
**Por quê?** Fonte oficial e gratuita de dados de satélite (MODIS e VIIRS) com cobertura global.

**Impacto**: **FONTE DE DADOS PRIMÁRIA** - Fornece dados de queimadas em tempo quase real (latência de 3h) com precisão de localização e temperatura.

**Satélites**:
- **MODIS**: Resolução 1km (Terra/Aqua)
- **VIIRS**: Resolução 375m (SNPP/NOAA-20) - mais preciso

---

## � Decisões Arquiteturais Críticas

### 1. **Async/Await em Todo Stack**
- Backend assíncrono (FastAPI + HTTPX)
- Hooks React com atualização não-bloqueante
- **Resultado**: Aplicação responsiva mesmo com milhares de pontos de queimada

### 2. **Cache em Memória (Backend)**
- Armazena dados da NASA entre requisições
- Reduz chamadas à API externa
- **Resultado**: Resposta instantânea e economia de quota da NASA API

### 3. **Dynamic Import do Leaflet**
```typescript
const FireMap = dynamic(() => import("@/components/FireMap"), { ssr: false });
```
- **Motivo**: Leaflet depende de APIs do browser (window, document)
- **Resultado**: Evita erros de SSR no Next.js

### 4. **Type Safety Completo**
- TypeScript no frontend
- Type hints Python no backend
- Pydantic para validação de dados
- **Resultado**: Menos bugs em produção, melhor manutenibilidade

---

## 📊 Fluxo de Dados Essencial

```
NASA FIRMS API (CSV)
        ↓
HTTPX (requisição async)
        ↓
FastAPI Cache (memória)
        ↓
REST Endpoints (/api/fires)
        ↓
Frontend fetch (useFireData hook)
        ↓
React State Management
        ↓
Leaflet Map (marcadores visuais)
```

---

## ⚡ Otimizações Críticas

### Backend
- **Cache em memória**: Evita requisições repetidas à NASA
- **Background tasks**: Atualização de dados sem bloquear endpoints
- **Conversão segura de tipos**: Fallbacks para dados inválidos da API

### Frontend
- **Dynamic imports**: Leaflet carrega apenas no client-side
- **Memoization**: Hook `useFireData` evita re-renders desnecessários
- **Purge CSS**: Tailwind remove estilos não utilizados (bundle < 10KB)

---

## 🛠️ Ferramentas de Desenvolvimento

### **pnpm**
**Por quê?** Mais rápido que npm/yarn com economia de espaço.

**Impacto**: Instalação de dependências 2-3x mais rápida.

### **ESLint** + **eslint-config-next**
**Por quê?** Padrões de código e detecção de problemas.

**Impacto**: Código consistente e prevenção de bugs (Core Web Vitals rules).

---

## 🎯 Tecnologias que Fazem a Diferença

### **Top 5 - Impacto Direto no Projeto**

1. **Leaflet + React-Leaflet** → Visualização de mapas (core feature)
2. **NASA FIRMS API** → Fonte de dados de queimadas (sem isso, não há projeto)
3. **FastAPI Async** → Performance para lidar com milhares de pontos
4. **Next.js 16** → Otimizações automáticas e DX superior
5. **TypeScript** → Confiabilidade e manutenibilidade do código

### **Configurações Essenciais**

```bash
# Backend
NASA_API_KEY=sua_chave_aqui  # Obrigatório

# Dependências Críticas
fastapi, uvicorn, httpx  # Backend
next, react, leaflet, react-leaflet  # Frontend
```

---

## 📝 Resumo Final

O projeto usa tecnologias modernas priorizando:
- ⚡ **Performance**: Async em todo stack + cache inteligente
- 🗺️ **Visualização**: Leaflet para mapas interativos sem custo
- 🔒 **Confiabilidade**: TypeScript + Pydantic para type safety
- 🚀 **DX**: Next.js + FastAPI com hot reload e docs automáticas

**Stack escolhido = Rápido de desenvolver + Performance em produção + Custo zero de APIs**
