#!/bin/bash

# Script para iniciar o projeto Ignis completo
# Backend (API) + Frontend (Interface Web)

echo "🔥 Iniciando Projeto Ignis - Monitoramento de Queimadas"
echo "=================================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se uma porta está em uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Porta em uso
    else
        return 1  # Porta livre
    fi
}

# Verificar se estamos no diretório correto
if [ ! -f "backend/server.py" ]; then
    echo -e "${RED}❌ Erro: Execute este script a partir da raiz do projeto Ignis${NC}"
    exit 1
fi

# Verificar se as dependências estão instaladas
echo -e "${BLUE}📦 Verificando dependências...${NC}"
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Instalando dependências...${NC}"
    pip install -r requirements.txt
fi

# Criar arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}🔧 Criando arquivo .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Arquivo .env criado. Você pode editá-lo se necessário.${NC}"
fi

# Verificar se as portas estão disponíveis
if check_port 8000; then
    echo -e "${RED}❌ Porta 8000 já está em uso. Pare o processo que está usando esta porta.${NC}"
    exit 1
fi

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Porta 3000 já está em uso. Tentando porta 3001...${NC}"
    FRONTEND_PORT=3001
else
    FRONTEND_PORT=3000
fi

echo ""
echo -e "${GREEN}🚀 Iniciando serviços...${NC}"

# Função para limpar processos ao sair
cleanup() {
    echo -e "\n${YELLOW}🛑 Parando serviços...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}👋 Serviços parados. Até logo!${NC}"
    exit 0
}

# Capturar sinais para limpeza
trap cleanup SIGINT SIGTERM

# Iniciar Backend (API)
echo -e "${BLUE}🔧 Iniciando API Backend (porta 8000)...${NC}"
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Aguardar um pouco para o backend iniciar
sleep 3

# Verificar se o backend iniciou corretamente
if ! check_port 8000; then
    echo -e "${RED}❌ Erro: Backend não conseguiu iniciar na porta 8000${NC}"
    exit 1
fi

# Iniciar Frontend
echo -e "${BLUE}🌐 Iniciando Frontend (porta $FRONTEND_PORT)...${NC}"
python start_frontend.py &
FRONTEND_PID=$!

# Aguardar um pouco para o frontend iniciar
sleep 2

echo ""
echo -e "${GREEN}✅ Projeto Ignis iniciado com sucesso!${NC}"
echo "=================================================="
echo -e "${BLUE}🔗 URLs de acesso:${NC}"
echo -e "   • Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "   • API: ${GREEN}http://localhost:8000${NC}"
echo -e "   • Documentação: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}📝 Pressione Ctrl+C para parar todos os serviços${NC}"
echo ""

# Manter o script rodando
while true; do
    # Verificar se os processos ainda estão rodando
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend parou de funcionar${NC}"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend parou de funcionar${NC}"
        break
    fi
    
    sleep 5
done

cleanup