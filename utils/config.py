from pathlib import Path

# Rutas
APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"
OUTPUTS_DIR = APP_DIR / "outputs"

# Catálogos UI
CATALOGOS = {
    "modalidad": ["Embotellado", "Flexitank", "Mixto"],
    "incoterm": ["FOB", "CIF"],
    "puerto": ["Cartagena", "Buenaventura"],
    "ciudad": ["Bogotá", "Medellín", "Barranquilla"],
    "unidad_vol": ["Botellas", "Litros", "Contenedor 40ft"],
    "escenario": ["Base", "+10% TRM", "+15% Flete", "Worst-case"],
}

# Constantes
BOTELLA_L = 0.75