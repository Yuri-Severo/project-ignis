#!/usr/bin/env python3
"""
Servidor simples para servir o frontend do projeto Ignis
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Define o diretório do frontend
        frontend_dir = Path(__file__).parent / "frontend"
        os.chdir(frontend_dir)
        super().__init__(*args, **kwargs)

    def end_headers(self):
        # Adiciona headers CORS para evitar problemas
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_frontend_server(port=3000):
    """Inicia o servidor do frontend"""
    try:
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 Servidor do frontend iniciado em: http://localhost:{port}")
            print(f"📁 Servindo arquivos do diretório: {Path.cwd() / 'frontend'}")
            print("🔥 Certifique-se de que a API está rodando em: http://localhost:8000")
            print("Pressione Ctrl+C para parar o servidor")
            
            # Abre automaticamente no navegador
            webbrowser.open(f'http://localhost:{port}')
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor do frontend parado.")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Porta {port} já está em uso. Tente uma porta diferente.")
        else:
            print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    start_frontend_server()