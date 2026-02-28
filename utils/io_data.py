# utils/io_data.py
import pandas as pd
import os


def load_parametros_base(path_csv: str) -> dict:
    """
    Lee data/parametros_base.csv con columnas:
        parametro, valor, unidad (opcional), nota (opcional)

    Devuelve:
        dict {parametro: valor}

    Características:
        - Convierte automáticamente valores numéricos
        - Elimina espacios
        - Controla archivo inexistente
        - Maneja valores vacíos
    """

    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"No se encontró el archivo: {path_csv}")

    df = pd.read_csv(path_csv)

    if "parametro" not in df.columns or "valor" not in df.columns:
        raise ValueError("El CSV debe contener columnas 'parametro' y 'valor'.")

    # Limpieza básica
    df["parametro"] = df["parametro"].astype(str).str.strip()
    df["valor"] = df["valor"].astype(str).str.strip()

    # Conversión automática a numérico cuando sea posible
    def _convert_value(x):
        try:
            # Intenta convertir a float
            val = float(x)
            # Si es entero exacto, devuélvelo como int
            if val.is_integer():
                return int(val)
            return val
        except:
            # Si no es número, devolver string original
            return x

    df["valor"] = df["valor"].apply(_convert_value)

    # Eliminar parámetros vacíos
    df = df[df["parametro"] != ""]

    # Si hay duplicados, conservar el último
    df = df.drop_duplicates(subset="parametro", keep="last")

    return dict(zip(df["parametro"], df["valor"]))