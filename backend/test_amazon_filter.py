#!/usr/bin/env python3
"""
Script de teste para validar a filtragem de pontos da Amazônia Legal.
Testa se pontos de Bolívia, Peru e Colômbia são corretamente excluídos.
"""

# Polígono aproximado da Amazônia Legal (copiado do lifespan.py)
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

# Pontos de teste
test_points = [
    # Dentro da Amazônia Legal (Brasil)
    {"name": "Manaus, AM", "lon": -60.0217, "lat": -3.1190, "expected": True},
    {"name": "Belém, PA", "lon": -48.5044, "lat": -1.4558, "expected": True},
    {"name": "Porto Velho, RO", "lon": -63.9004, "lat": -8.7612, "expected": True},
    {"name": "Rio Branco, AC", "lon": -67.8100, "lat": -9.9750, "expected": True},
    {"name": "Palmas, TO", "lon": -48.3558, "lat": -10.1847, "expected": True},
    {"name": "Cuiabá, MT", "lon": -56.0974, "lat": -15.6014, "expected": True},
    {"name": "Macapá, AP", "lon": -51.0694, "lat": 0.0389, "expected": True},
    {"name": "Boa Vista, RR", "lon": -60.6753, "lat": 2.8235, "expected": True},
    
    # Fora da Amazônia Legal (países vizinhos)
    {"name": "La Paz, Bolívia", "lon": -68.1193, "lat": -16.4897, "expected": False},
    {"name": "Santa Cruz, Bolívia", "lon": -63.1812, "lat": -17.8146, "expected": False},
    {"name": "Lima, Peru", "lon": -77.0428, "lat": -12.0464, "expected": False},
    {"name": "Iquitos, Peru", "lon": -73.2472, "lat": -3.7437, "expected": False},
    {"name": "Bogotá, Colômbia", "lon": -74.0721, "lat": 4.7110, "expected": False},
    {"name": "Leticia, Colômbia", "lon": -69.9406, "lat": -4.2153, "expected": False},
    
    # Pontos fronteiriços (limítrofes)
    {"name": "Fronteira Brasil-Peru (Acre)", "lon": -73.2, "lat": -9.0, "expected": True},
    {"name": "Fronteira Brasil-Bolívia (Rondônia)", "lon": -65.3, "lat": -11.5, "expected": True},
]

def test_filter():
    """Testa a função de filtragem"""
    print("=" * 80)
    print("TESTE DE FILTRAGEM - AMAZÔNIA LEGAL")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for point in test_points:
        result = is_point_in_amazon_legal(point['lon'], point['lat'])
        status = "✓ PASSOU" if result == point['expected'] else "✗ FALHOU"
        
        if result == point['expected']:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {point['name']:<35} | Lon: {point['lon']:>9.4f}, Lat: {point['lat']:>8.4f} | "
              f"Esperado: {point['expected']}, Resultado: {result}")
    
    print()
    print("=" * 80)
    print(f"RESULTADOS: {passed} passaram, {failed} falharam de {len(test_points)} testes")
    print("=" * 80)
    
    if failed > 0:
        print("\n⚠️  ATENÇÃO: Alguns testes falharam. O polígono pode precisar de ajustes.")
    else:
        print("\n✓ Todos os testes passaram! Filtragem funcionando corretamente.")
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = test_filter()
    sys.exit(0 if success else 1)
